# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Thu Apr 11 15:55:56 2019
    Current: 

@author: Xing Guo (xingguo@umich.edu)

"""


#%% Import Moduels

## System Tools
import os
import numpy as np
## I/O Tools
import _pickle as pickle
## Data Process Tools
import pandas as pd
import datetime
## Graphs
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as figpdf
import matplotlib.dates as matdates
## Statistical Tools
import statsmodels.api as sm
## Database API
from fredapi import Fred
## API for WRDS
import wrds


# End of Section: Import Moduels
###############################################################################


#%% Setup Working Directory
FolderList = [xx+"\\Dropbox\\Research Projects\\02_FirmHete_AsymmetricInformation\\Data\\Micro_data\\codes\\" \
              for xx in ["D:\\", "E:\\","B:\\","/mnt/b/"]]
for Folder in FolderList:
    if os.path.exists(Folder):
        os.chdir(Folder)     
# End of Section: Setup Working Directory
###############################################################################



#%% Import Self-written Functions
# CodeFolder      =   'Toolkit\\'
# exec(open(CodeFolder+'Toolbox_Graph.py').read())
idx             =   pd.IndexSlice
# End of Section: Import Self-written Functions
###############################################################################


#%% Temporary Functions for Running the Regressions

### One Single Simple Regression
def TempFun_SingleReg(DS,YVar,XVarList,WeightVar=''):
    if WeightVar=='':
        TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                               missing='drop').fit()
    else:
        TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                               weights=DS[WeightVar], \
                               missing='drop').fit()
    TempTable   =   pd.concat([pd.DataFrame(TempReg.params,columns=[YVar]), \
                               pd.DataFrame(TempReg.tvalues,columns=[YVar])], \
                              axis=0,keys=['Coef','Tstat']) \
                    .swaplevel(i=0,j=1,axis=0)
    TempTable.loc[('RegInfo','Obs'),YVar]    =   TempReg.nobs
    TempTable.loc[('RegInfo','R2'),YVar]     =   TempReg.rsquared
    
    TempTable.sort_index(inplace=True)
    
    return TempTable,TempReg

### A Single Regression with a Given Regression Setup (with Monetary Shocks)
def TempFun_GroupUnitReg_Ms(DS,GroupVar,DateLimit,EventDict, \
                            RetVar,MsVar, \
                            XList_Macro,XList_Firm,XList_IndRet,XList_FirmFix, \
                            MacroSuffix='',FirmSuffix='',WeightVar=''):
    
    ## Preliminary
    DateType        =   EventDict['Suffix']
    DateVar         =   EventDict['DateVar']
    
    ## Assemble the Variables
    # Y-Variables
    YVar            =   DateType+'_'+RetVar
    # X-Variables
    if MacroSuffix=='' and MsVar!='':
        XVarList_Macro  =   [DateType+'_'+MsVar+'_'+x for x in XList_Macro]
    else:
        XVarList_Macro  =   [DateType+'_'+MacroSuffix+'_'+x for x in XList_Macro]
    
    if FirmSuffix=='' and MsVar!='':
        XVarList_Firm   =   [DateType+'_'+MsVar+'_'+x for x in XList_Firm]
    else:
        XVarList_Firm   =   [DateType+'_'+FirmSuffix+'_'+x for x in XList_Firm]

    XVarList_IndRet =   [DateType+'_'+x for x in XList_IndRet]
    XVarList_FirmFix=   XList_FirmFix
    
    if MsVar=='':
        MsType          =   'NoMs'
        XVarList        =   XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
        XLabelList      =   XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
    else:
        MsType          =   MsVar
        XVarList        =   [DateType+'_'+MsVar]+ \
                            XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
        XLabelList      =   ['Ms']+ \
                            XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
    
    ## Assemble the Data
    TempInd         =   ( DS[DateVar]>=DateLimit[0] ) & ( DS[DateVar]<=DateLimit[1] )
    EffectiveDS     =   DS.loc[TempInd,:].copy()    
    if GroupVar=='Pooled':
        EffectiveDS[GroupVar]   =   0
    RegVarList      =   list(set([YVar]+XVarList+[GroupVar]))
    EffectiveDS     =   EffectiveDS[RegVarList].dropna().reset_index(drop=True)
    GroupValueList  =   EffectiveDS[GroupVar].unique().tolist()
    
    ## Computation
    InitiateFlag    =   True
    for GroupValue in GroupValueList:
        # Regression Sample
        RegDS           =   EffectiveDS[EffectiveDS[GroupVar]==GroupValue].reset_index(drop=True)
        # Check whether the XVar only has one value
        RegXVarList     =   []
        RegXLabelList   =   []
        for ii in range(len(XVarList)):
            if len(RegDS[XVarList[ii]].unique().tolist())>1:
                RegXVarList     =   RegXVarList+[XVarList[ii]]
                RegXLabelList   =   RegXLabelList+[XLabelList[ii]]
        # OLS (WLS)
        if RegDS.shape[0]>10:
            RegTable,RegInfo    =   TempFun_SingleReg(RegDS,YVar,RegXVarList,WeightVar)
            ColTuple            =   (DateType,RetVar,MsType, \
                                     str(DateLimit[0].year)+'-'+str(DateLimit[1].year), \
                                     GroupVar,GroupValue)
            RegTable.rename(columns={YVar: ColTuple},inplace=True)
            RegTable.columns    =   pd.MultiIndex.from_tuples(RegTable.columns.tolist())
            RegTable.rename(index={RegXVarList[i]: RegXLabelList[i] for i in range(len(RegXVarList))}, \
                                   level=0,inplace=True)
        else:
            RegTable    =   pd.DataFrame()
        # Collect the Result
        if InitiateFlag and (not RegTable.empty):
            RegResult   =   RegTable
            InitiateFlag=   False
        elif (not RegTable.empty):
            RegResult   =   RegResult.merge(right=RegTable,how='outer', \
                                            left_index=True,right_index=True)
    
    ## If there is no result to return, just return an empty dataframe       
    if InitiateFlag:
        RegResult   =   pd.DataFrame()
    
    return RegResult

# End of Section:
###############################################################################
    
    
#%% Regressions 
    

### Setup

## Read-in Data
DataFolder      =   '..\\temp\\'
DS              =   pd.read_pickle(DataFolder+"RegSample.p")

#DS = DS[DS['GapBusDays_F2I']>5]
#DS=DS[DS['PrimaryFlag']==-1]
## Event List
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]

## Sample Period
SamplePeriodList=   [ \
                      [datetime.date(1970,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1983,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1994,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1970,1,1),datetime.date(1996,12,31)], \
                      [datetime.date(1983,1,1),datetime.date(1996,12,31)], \
                      [datetime.date(1994,1,1),datetime.date(1996,12,31)], \
                      [datetime.date(1970,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(1983,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(1994,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(1997,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(2000,1,1),datetime.date(2007,6,1)], \
#                      [datetime.date(1970,1,1),datetime.date(1983,1,1)] \
                    ]

#SamplePeriodList=   [[datetime.date(x,1,1),datetime.date(x+2,1,1)] for x in range(1970,2006)]
## Variable Lists
GroupVarList    =   ['Pooled','PrimaryFlag','ShelfIssueFlag']
RetVar          =   'AccAbRet_-1_1'
MsVarList       =   ['30d_MsRR','90d_MsRR','30d_MsWideHF','90d_MsWideHF']
MacroVarList    =   ['GdpGrowth','Inflation','UnemploymentRate','FedFundsRate','SpRet_Sum','SpRet_Std']
IndRetVarList   =   ['AbRetRunup','AbRetStd']
FirmVarList     =   ['Leverage','OfferedPrimarySharesDivByCommonShares_Outstanding', \
                     'SaleGrowth_LowQuant','SaleGrowth_UppQuant', \
                     'Size_LowQuant','Size_UppQuant', \
                     'Equity_M2B_LowQuant','Equity_M2B_UppQuant']
FirmFixVarList  =   ['FF5_1','FF5_2','FF5_3','FF5_4', \
                     'PrimarySecondaryFlag','OnlySecondaryFlag', \
                     'ShelfIssueFlag']

## Regression Design

RegDesignList   =   [ \
                     {'MsFlag': False,'Macro': [], 'IndRet': IndRetVarList, 'Firm': FirmVarList,'FirmFix': FirmFixVarList}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': [], 'Firm': [],'FirmFix': []}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': IndRetVarList,'Firm': FirmVarList,'FirmFix': FirmFixVarList} \
                    ]

RegDesignTagList=   ['No Ms','Ms, Only Macro','Ms, Full']

### Collect the Regression Results
RegResultTableList  =   []
for RegDesign in RegDesignList:
    InitiateFlag    =   True
    if RegDesign['MsFlag']:
        TempRegMsVarList    =   MsVarList
    else:
        TempRegMsVarList    =   ['']
    for GroupVar in GroupVarList:
        for EventDict in EventDictList:
            for MsVar in TempRegMsVarList:
                if MsVar=='':
                    TempMacroSuffix     =   'Lag1'
                for DateLimit in SamplePeriodList:
                    TempResult  =   TempFun_GroupUnitReg_Ms(DS,GroupVar,DateLimit,EventDict, \
                                                            RetVar,MsVar, \
                                                            RegDesign['Macro'], \
                                                            RegDesign['Firm'], \
                                                            RegDesign['IndRet'], \
                                                            RegDesign['FirmFix'],\
                                                            MacroSuffix=TempMacroSuffix, \
                                                            FirmSuffix='Lag1')
                    if not TempResult.empty:
                        if InitiateFlag==1:
                            RegResultTable  =   TempResult
                            InitiateFlag    =   False
                        else:
                            RegResultTable  =   RegResultTable.merge(right=TempResult, \
                                                                     how='outer', \
                                                                     left_index=True, \
                                                                     right_index=True)

    RegResultTableList.append(RegResultTable)

RegResultTable  =   pd.concat(RegResultTableList,join='outer',axis=1, \
                              keys=RegDesignTagList)

                
### Clean the Regression Results

RegResultTable.columns \
                =   RegResultTable.columns.droplevel(level=2)
                
## Sort the Vairables for Easier Interpretation
OutputTable     =   RegResultTable.loc[idx[['Ms','const'],:],:] \
                    .append(RegResultTable.loc[idx[MacroVarList,:],:]) \
                    .append(RegResultTable.loc[idx[IndRetVarList,:],:]) \
                    .append(RegResultTable.loc[idx[FirmFixVarList,:],:]) \
                    .append(RegResultTable.loc[idx[FirmVarList,:],:]) \
                    .append(RegResultTable.loc[idx['RegInfo',:],:])
                    
                    
TT=OutputTable.loc[idx[['Ms','RegInfo'],:],idx['Ms, Full','L',:,:,'Pooled',:]] \
     .reset_index(level=[0],drop=True).T. \
     reset_index(level=[0,1,4,5],drop=True)['Tstat'].unstack(level=1)

# End of Section:
###############################################################################
# %% Understand the old code 

GroupVar = 'Pooled'
DateLimit = [datetime.date(1983,1,1),datetime.date(2007,6,1)]
RetVar  = 'AccAbRet_-1_1'
EventDict = {'Suffix': 'F', 'DateVar': 'FilingDate'}
MsVar = '90d_MsWideHF'
MacroVarList    =   ['GdpGrowth','Inflation','UnemploymentRate','FedFundsRate','SpRet_Sum','SpRet_Std']
IndRetVarList   =   ['AbRetRunup','AbRetStd']
FirmVarList     =   ['Leverage','OfferedPrimarySharesDivByCommonShares_Outstanding', \
                     'Diff_LogSales_LowQuant','Diff_LogSales_UppQuant', \
                     'Lag_Asset_LowQuant','Lag_Asset_UppQuant', \
                     'Equity_M2B_LowQuant','Equity_M2B_UppQuant']
FirmFixVarList  =   ['FF5_1','FF5_2','FF5_3','FF5_4', \
                     'PrimarySecondaryFlag','OnlySecondaryFlag', \
                     'ShelfIssueFlag']

RegDesignList   =   [ \
                     {'MsFlag': False,'Macro': [], 'IndRet': IndRetVarList, 'Firm': FirmVarList,'FirmFix': FirmFixVarList}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': [], 'Firm': [],'FirmFix': []}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': IndRetVarList,'Firm': FirmVarList,'FirmFix': FirmFixVarList} \
                    ]
RegDesign = RegDesignList[2]

MacroSuffix = ''
FirmSuffix = ''
XList_Macro = RegDesign['Macro']
XList_Firm = RegDesign['Firm']
XList_IndRet = RegDesign['IndRet']
XList_FirmFix = RegDesign['FirmFix']

## Preliminary
DateType        =   EventDict['Suffix']
DateVar         =   EventDict['DateVar']
    
## Assemble the Variables
# Y-Variables
YVar            =   DateType+'_'+RetVar
# X-Variables
if MacroSuffix=='' and MsVar!='':
    XVarList_Macro  =   [DateType+'_'+MsVar+'_'+x for x in XList_Macro]
else:
    XVarList_Macro  =   [DateType+'_'+MacroSuffix+'_'+x for x in XList_Macro]

if FirmSuffix=='' and MsVar!='':
    XVarList_Firm   =   [DateType+'_'+MsVar+'_'+x for x in XList_Firm]
else:
    XVarList_Firm   =   [DateType+'_'+FirmSuffix+'_'+x for x in XList_Firm]

    XVarList_IndRet =   [DateType+'_'+x for x in XList_IndRet]
    XVarList_FirmFix=   XList_FirmFix
    
if MsVar=='':
    MsType          =   'NoMs'
    XVarList        =   XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
    XLabelList      =   XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
else:
    MsType          =   MsVar
    XVarList        =   [DateType+'_'+MsVar]+ \
                        XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
    XLabelList      =   ['Ms']+ \
                        XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
    
## Assemble the Data
TempInd         =   ( DS[DateVar]>=DateLimit[0] ) & ( DS[DateVar]<=DateLimit[1] )
EffectiveDS     =   DS.loc[TempInd,:].copy()    
if GroupVar=='Pooled':
    EffectiveDS[GroupVar]   =   0
RegVarList      =   list(set([YVar]+XVarList+[GroupVar]))
EffectiveDS     =   EffectiveDS.loc[:, RegVarList].dropna().reset_index(drop=True)
GroupValueList  =   EffectiveDS[GroupVar].unique().tolist()