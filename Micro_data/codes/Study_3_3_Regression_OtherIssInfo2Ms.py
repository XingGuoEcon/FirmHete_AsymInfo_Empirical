# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Tue Apr 23 16:36:20 2019
    Current: 

@author: Xing Guo (xingguo@umich.edu)

"""
# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Tue Apr 16 14:42:29 2019
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
try:
    # Office Desktop Directory
    os.chdir("E:\\Dropbox")
except:
    # Home Desktop Directory
    os.chdir("L:\Dropbox")
    
#Windows System Path
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Micro_data\\codes")

# End of Section: Setup Working Directory
###############################################################################



#%% Import Self-written Functions
CodeFolder      =   'Toolkit\\'
exec(open(CodeFolder+'Fun_NBER_date.py').read())
exec(open(CodeFolder+'Fun_RomerRomerReg.py').read())
exec(open(CodeFolder+'Fun_IRF_Plot.py').read())
exec(open(CodeFolder+'Toolbox_Graph.py').read())
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
def TempFun_GroupUnitReg_Ms(DS,DateLimit,IF,RetVar,MsVar,XList_Macro,XList_Firm,XList_IndRet,XList_FirmFix, \
                         WeightVar='',MacroSuffix='',FirmSuffix=''):
    YVar            =   RetVar
    XVar_Ms         =   IF+'_'+MsVar
    
    if MacroSuffix=='':
        MacroSuffix     =   IF+'_'+MsVar
    else:
        MacroSuffix     =   IF+'_'+MacroSuffix
    
    if FirmSuffix=='':
        FirmSuffix      =   IF+'_'+MsVar
    else:
        FirmSuffix      =   IF+'_'+FirmSuffix
        
    XVarList_Macro  =   [MacroSuffix+'_'+x for x in XList_Macro]
    XVarList_Firm   =   [FirmSuffix+'_'+x for x in XList_Firm]
    XVarList_IndRet =   [IF+'_'+x for x in XList_IndRet]
    XVarList_FirmFix=   XList_FirmFix
    
    XVarList        =   [XVar_Ms]+XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
    XLabelList      =   ['Ms']+XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
    
    if IF=='I':
        DateVar     =   'IssueDate'
    elif IF=='F':
        DateVar     =   'FilingDate'

    TempInd         =   ( DS[DateVar]>=DateLimit[0] ) & ( DS[DateVar]<=DateLimit[1] )
                        
    EffectiveDS     =   DS.loc[TempInd,[YVar]+XVarList].dropna().reset_index(drop=True)
    if EffectiveDS.shape[0]>10:
        RegTable,RegInfo    =   TempFun_SingleReg(EffectiveDS,YVar,XVarList,WeightVar)
        ColTuple            =   (IF,RetVar,MsVar, \
                                 str(DateLimit[0].year)+'-'+str(DateLimit[1].year))
        RegTable.rename(columns={YVar: ColTuple},inplace=True)
        RegTable.columns    =   pd.MultiIndex.from_tuples(RegTable.columns.tolist())
        
        RegTable.rename(index={XVarList[i]: XLabelList[i] for i in range(len(XVarList))}, \
                        level=0,inplace=True)
    else:
        RegTable    =   pd.DataFrame()
    
    return RegTable

### A Single Regression with a Given Regression Setup (with Monetary Shocks)
def TempFun_GroupUnitReg_NoMs(DS,DateLimit,IF,RetVar,XList_Macro,XList_Firm,XList_IndRet,XList_FirmFix, \
                              MacroSuffix='',FirmSuffix='',WeightVar=''):
    YVar            =   RetVar
    
    if MacroSuffix=='':
        MacroSuffix     =   IF+'_Lag1'
    else:
        MacroSuffix     =   IF+'_'+MacroSuffix
    
    if FirmSuffix=='':
        FirmSuffix      =   IF+'_Lag1'
    else:
        FirmSuffix      =   IF+'_'+FirmSuffix
        
    XVarList_Macro  =   [MacroSuffix+'_'+x for x in XList_Macro]
    XVarList_Firm   =   [FirmSuffix+'_'+x for x in XList_Firm]
    XVarList_IndRet =   [IF+'_'+x for x in XList_IndRet]
    XVarList_FirmFix=   XList_FirmFix
    
    XVarList        =   XVarList_Macro+XVarList_Firm+XVarList_IndRet+XVarList_FirmFix
    XLabelList      =   XList_Macro+XList_Firm+XList_IndRet+XVarList_FirmFix
    
    if IF=='I':
        DateVar     =   'IssueDate'
    elif IF=='F':
        DateVar     =   'FilingDate'

    TempInd         =   ( DS[DateVar]>=DateLimit[0] ) & ( DS[DateVar]<=DateLimit[1] )
                        
    EffectiveDS     =   DS.loc[TempInd,[YVar]+XVarList].dropna().reset_index(drop=True)
    if EffectiveDS.shape[0]>10:
        RegTable,RegInfo    =   TempFun_SingleReg(EffectiveDS,YVar,XVarList,WeightVar)
        ColTuple            =   (IF,RetVar,'NoMs', \
                                 str(DateLimit[0].year)+'-'+str(DateLimit[1].year))
        RegTable.rename(columns={YVar: ColTuple},inplace=True)
        RegTable.columns    =   pd.MultiIndex.from_tuples(RegTable.columns.tolist())
        
        RegTable.rename(index={XVarList[i]: XLabelList[i] for i in range(len(XVarList))}, \
                        level=0,inplace=True)
    else:
        RegTable    =   pd.DataFrame()
    
    return RegTable
# End of Section:
###############################################################################
    

#%% Regressions based on the Full Sample

### Setup

## Read-in Data
DataFolder      =   '..\\temp\\'
DS              =   pickle.load(open(DataFolder+"RegSample.p","rb"))

## Sample Period
SamplePeriodList=   [ [datetime.date(1970,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1983,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1994,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1970,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(1983,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(1994,1,1),datetime.date(1999,12,31)], \
                      [datetime.date(2000,1,1),datetime.date(2007,6,1)], \
                      [datetime.date(1970,1,1),datetime.date(1983,1,1)] \
                    ]

## Variable Lists
IFResVarList    =   ['Pre_MsRR_GapDays_Min','Pre_MsWideHF_GapDays_Min']
ResVarList      =   ['GapDays_Adj']
MsVarList       =   ['Pre_MsRR','30d_MsRR','90d_MsRR', \
                     'Pre_MsWideHF','30d_MsWideHF','90d_MsWideHF']

MacroVarList    =   ['GdpGrowth','Inflation','UnemploymentRate','SpRet_Sum','SpRet_Std']
IndRetVarList   =   ['AbRetRunup','AbRetStd']
FirmVarList     =   ['Leverage','OfferedPrimarySharesDivByCommonShares_Outstanding', \
                     'SaleGrowth_LowQuant','SaleGrowth_UppQuant', \
                     'Size_LowQuant','Size_UppQuant']
FirmFixVarList  =   ['FF5_1','FF5_2','FF5_3','FF5_4','PrimarySecondaryFlag','OnlySecondaryFlag']
## Regression Design

RegDesignList   =   [{'MsFlag': False,'Macro': [], 'IndRet': IndRetVarList, 'Firm': FirmVarList,'FirmFix': FirmFixVarList}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': [], 'Firm': [],'FirmFix': []}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': IndRetVarList,'Firm': FirmVarList,'FirmFix': FirmFixVarList}
                    ]

RegDesignTagList=   ['No Ms','Ms, Only Macro','Ms, Full']

### Collect the Regression Results
RegResultTableList  =   []

for RegDesign in RegDesignList:
    InitiateFlag    =   1
    for DateLimit in SamplePeriodList:
        if RegDesign['MsFlag']:
            for IF in ['I','F']:
                for ResVar in IFResVarList+ResVarList:
                    if any([ResVar==x for x in IFResVarList]):
                        TempResVar  =   IF+'_'+ResVar
                    else:
                        TempResVar  =   ResVar
                        
                    for MsVar in MsVarList:
                        TempTable   =   TempFun_GroupUnitReg_Ms(DS,DateLimit,IF,TempResVar,MsVar, \
                                                                RegDesign['Macro'], \
                                                                RegDesign['Firm'], \
                                                                RegDesign['IndRet'], \
                                                                RegDesign['FirmFix'], \
                                                                FirmSuffix='Lag1')
                        if not TempTable.empty:
                            if InitiateFlag==1:
                                RegResultTable  =   TempTable
                                InitiateFlag    =   0
                            else:
                                RegResultTable  =   RegResultTable.merge(right=TempTable, \
                                                                         how='outer', \
                                                                         left_index=True, \
                                                                         right_index=True)
        else:
            for IF in ['I','F']:
                for ResVar in IFResVarList+ResVarList:
                    if any([ResVar==x for x in IFResVarList]):
                        TempResVar  =   IF+'_'+ResVar
                    else:
                        TempResVar  =   ResVar
                    TempTable   =   TempFun_GroupUnitReg_NoMs(DS,DateLimit,IF,TempResVar, \
                                                              RegDesign['Macro'], \
                                                              RegDesign['Firm'], \
                                                              RegDesign['IndRet'], \
                                                              RegDesign['FirmFix'])
                    if not TempTable.empty:
                        if InitiateFlag==1:
                            RegResultTable  =   TempTable
                            InitiateFlag    =   0
                        else:
                            RegResultTable  =   RegResultTable.merge(right=TempTable, \
                                                                     how='outer', \
                                                                     left_index=True, \
                                                                     right_index=True)
    RegResultTableList.append(RegResultTable)
                

    
    
RegResultTable  =   pd.concat(RegResultTableList,join='outer',axis=1, \
                              keys=RegDesignTagList) \
                    .sort_index(axis=1) \
                    .rename(columns={**{'I_'+x:x for x in IFResVarList},**{'F_'+x:x for x in IFResVarList}},level=2)

### Clean the Regression Results


## Sort the Vairables for Easier Interpretation
OutputTable     =   RegResultTable.loc[idx[['Ms','const'],:],:] \
                    .append(RegResultTable.loc[idx[MacroVarList,:],:]) \
                    .append(RegResultTable.loc[idx[IndRetVarList,:],:]) \
                    .append(RegResultTable.loc[idx[FirmFixVarList,:],:]) \
                    .append(RegResultTable.loc[idx[FirmVarList,:],:]) \
                    .append(RegResultTable.loc[idx['RegInfo',:],:]) 

#%%
### Produce the Tables
                    
## Setup
TableFolder     =   '..\\results\\TableGraph\\RegOthers2Ms\\'
ExcelWriter     =   pd.ExcelWriter(TableFolder+'RegOthers2Ms.xlsx')

## Column List
ColList         =   [idx['No Ms',:,:,'NoMs',:], \
                     idx['Ms, Full','F','GapDays_Adj',['30d_MsRR','90d_MsRR','Pre_MsRR'],['1983-1999','2000-2007']], \
                     idx['Ms, Full','I','GapDays_Adj',['30d_MsRR','90d_MsRR','Pre_MsRR'],['1970-1999','2000-2007']], \
                     idx['Ms, Full','F','GapDays_Adj',['30d_MsWideHF','90d_MsWideHF','Pre_MsWideHF'],['1994-1999','2000-2007']], \
                     idx['Ms, Full','I','GapDays_Adj',['30d_MsWideHF','90d_MsWideHF','Pre_MsWideHF'],['1994-1999','2000-2007']], \
                     idx['Ms, Full','F','Pre_MsRR_GapDays_Min',['30d_MsRR','90d_MsRR','Pre_MsRR'],['1983-1999','2000-2007']], \
                     idx['Ms, Full','I','Pre_MsRR_GapDays_Min',['30d_MsRR','90d_MsRR','Pre_MsRR'],['1970-1999','2000-2007']], \
                     idx['Ms, Full','F','Pre_MsWideHF_GapDays_Min',['30d_MsWideHF','90d_MsWideHF','Pre_MsWideHF'],['1994-1999','2000-2007']], \
                     idx['Ms, Full','I','Pre_MsWideHF_GapDays_Min',['30d_MsWideHF','90d_MsWideHF','Pre_MsWideHF'],['1994-1999','2000-2007']] \
                     ]
TempTable       =   pd.concat([OutputTable.loc[:,xx] for xx in ColList],axis=1)
TempTable.to_excel(ExcelWriter,sheet_name='Main',float_format='%.2f')
## Comprehensive Check
OutputTable.to_excel(ExcelWriter,sheet_name='FullDetails',float_format='%.2f')

## Save the Excel File
ExcelWriter.save()
# End of Section:
###############################################################################

