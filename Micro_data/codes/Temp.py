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
    os.chdir("B:\\Dropbox")
except:
    # Home Desktop Directory
    os.chdir("D:\Dropbox")
    
#Windows System Path
os.chdir("Research Projects\\02_HeteFirm_AsymetricInformation\\Data\\Micro_data\\codes")

# End of Section: Setup Working Directory
###############################################################################



#%% Import Self-written Functions
CodeFolder      =   'Toolkit\\'
exec(open(CodeFolder+'Toolbox_Graph.py').read())
idx             =   pd.IndexSlice
# End of Section: Import Self-written Functions
###############################################################################


#%% Temporary Functions for Running the Regressions

### One Single Simple Regression
def TempFun_SingleReg(DS,YVar,XVarList,WeightVar='',ClusterIDVar=''):
    if WeightVar=='':
        if ClusterIDVar=='':
            TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                               missing='drop').fit()
        else:
            TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                                   missing='drop'). \
                                   fit(cov_type='cluster',cov_kwds={'groups': DS[ClusterIDVar]})
    else:
        if ClusterIDVar=='':
            TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                               weights=DS[WeightVar], \
                               missing='drop').fit()
        else:
            TempReg     =   sm.OLS(DS[YVar],sm.add_constant(DS[XVarList]), \
                                   weights=DS[WeightVar], \
                                   missing='drop'). \
                                   fit(cov_type='cluster',cov_kwds={'groups': DS[ClusterIDVar]})
    TempTable   =   pd.concat([pd.DataFrame(TempReg.params,columns=[YVar]), \
                               pd.DataFrame(TempReg.tvalues,columns=[YVar]), \
                               pd.DataFrame(TempReg.bse,columns=[YVar]), \
                               pd.DataFrame(TempReg.pvalues,columns=[YVar])], \
                              axis=0,keys=['Coef','Tstat','Se','Pvalue']) \
                    .swaplevel(i=0,j=1,axis=0)
    TempTable.loc[('RegInfo','Obs'),YVar]    =   TempReg.nobs
    TempTable.loc[('RegInfo','R2'),YVar]     =   TempReg.rsquared
    
    TempTable.sort_index(inplace=True)
    
    return TempTable,TempReg

### A Single Regression with a Given Regression Setup (with Monetary Shocks)
def TempFun_GroupUnitReg_Ms(DS,GroupVar,DateLimit,EventDict, \
                            RetVar,MsVar, \
                            XList_Macro,XList_Firm,XList_IndRet,XList_FirmFix, \
                            MacroSuffix='',FirmSuffix='',WeightVar='', \
                            TimeFixEffect='No',Cluster='No'):
    
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
    # Restrict to the given Sample Period
    TempInd         =   ( DS[DateVar]>=DateLimit[0] ) & ( DS[DateVar]<=DateLimit[1] )
    EffectiveDS     =   DS.loc[TempInd,:].copy()
    
    # Generate the Clustering ID
    if Cluster=='Year':
        EffectiveDS['ClusterID']    =   EffectiveDS[DateVar+'_Year'].map(lambda x: x.year)
    elif Cluster=='Quarter':
        EffectiveDS['ClusterID']    =   EffectiveDS[DateVar+'_Quarter'].map(lambda x: x.year*100+x.month)
    else:
        EffectiveDS['ClusterID']    =   0
    # Generate the Dummy Variables for Time-Fix Effects
    TimeFixEffectVarList    =   []
    if TimeFixEffect=='Year' and TimeFixEffect!='No':
        TimeList        =   EffectiveDS[DateVar+'_Year'].unique().tolist()
        
        if len(TimeList)>=2:
            
            for ii in range(1,len(TimeList)):
                TimeFixEffectVar        =   'Flag_'+str(TimeList[ii].year)
                TimeFixEffectVarList    =   TimeFixEffectVarList+[TimeFixEffectVar]
                EffectiveDS[TimeFixEffectVar]       =   0
                EffectiveDS.loc[EffectiveDS[DateVar+'_Year']==TimeList[ii], \
                                TimeFixEffectVar]   =   1
     
    elif TimeFixEffect=='Quarter' and TimeFixEffect!='No':
        TimeList        =   EffectiveDS[DateVar+'_Quarter'].unique().tolist()
        if len(TimeList)>=2:
            for ii in range(1,len(TimeList)):
                TimeFixEffectVar        =   'Flag_'+str(TimeList[ii].year)+ \
                                            '_'+str(TimeList[ii].month)
                TimeFixEffectVarList    =   TimeFixEffectVarList+[TimeFixEffectVar]
                EffectiveDS[TimeFixEffectVar]       =   0
                EffectiveDS.loc[EffectiveDS[DateVar+'_Quarter']==TimeList[ii], \
                                TimeFixEffectVar]   =   1
    
    
    XVarList    =   XVarList+TimeFixEffectVarList
    XLabelList  =   XLabelList+TimeFixEffectVarList
    # Generate the Group Variable for the 'Pooled' Regression
    if GroupVar=='Pooled':
        EffectiveDS[GroupVar]   =   0
    # Drop the missing Values
    RegVarList      =   list(set([YVar]+XVarList+[GroupVar]+['ClusterID']))
    EffectiveDS     =   EffectiveDS[RegVarList].dropna().reset_index(drop=True)
    # Extract the Unique Value List of the Group Variables
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
            TempXVarUniqueList  =   RegDS[XVarList[ii]].unique().tolist()
            if len(TempXVarUniqueList)>1:
                RegXVarList     =   RegXVarList+[XVarList[ii]]
                RegXLabelList   =   RegXLabelList+[XLabelList[ii]]
                # Normalization: demean the continuous control variables
                if len(TempXVarUniqueList)>2:
                    RegDS[XVarList[ii]]     =   ( RegDS[XVarList[ii]]- \
                                                  RegDS[XVarList[ii]].mean() )/1
        # Check whether there is only one Cluster Group 
        if len(RegDS['ClusterID'].unique().tolist())<=1:
            ClusterIDVar    =   ''
        else:
            ClusterIDVar    =   'ClusterID'
        # OLS (WLS)
        if RegDS.shape[0]>10:
            RegTable,RegInfo    =   TempFun_SingleReg(RegDS,YVar,RegXVarList,WeightVar,ClusterIDVar=ClusterIDVar)
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
DS              =   pickle.load(open(DataFolder+"RegSample.p","rb"))

## Event List
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]

## Clean Data: Normalize the Monetary Shocks
for EventType in ['F','L','I']:
    for MsVar in ['30d_MsWideHF','90d_MsWideHF']:
        # Normalized by the ratio of std
        DS[EventType+'_'+MsVar]     =   DS[EventType+'_'+MsVar]*0.186/0.086
        # Normalized by the correlation with actual interest rate change
#        DS[EventType+'_'+MsVar]     =   DS[EventType+'_'+MsVar]*1.357/0.84

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
GroupVarList    =   ['Pooled','PrimaryFlag','ShelfIssueFlag']
RETVAR          =   'AccAbRet'
RetVar          =   RETVAR+'_-1_1'
TimeFixEffect   =   'No'
Cluster         =   'No'
MsVarList       =   ['30d_MsRR','90d_MsRR','30d_MsWideHF','90d_MsWideHF']
MacroVarList    =   ['GdpGrowth','Inflation','UnemploymentRate','FedFundsRate','SpRet_Sum','SpRet_Std']
IndRetVarList   =   ['AbRetRunup','AbRetStd']
FirmVarList     =   ['Leverage', \
#                     'FiledAmountDivByAsset', \
                     'OfferedPrimarySharesDivByCommonShares_Outstanding', \
                     'SaleGrowth_LowQuant','SaleGrowth_UppQuant', \
                     'Size_LowQuant','Size_UppQuant']
FirmFixVarList  =   ['FF5_1','FF5_2','FF5_3','FF5_4', \
                     'PrimarySecondaryFlag','OnlySecondaryFlag', \
                     'ShelfIssueFlag']

## Regression Design

RegDesignList   =   [{'MsFlag': False,'Macro': [], 'IndRet': IndRetVarList, 'Firm': FirmVarList,'FirmFix': FirmFixVarList}, \
                     {'MsFlag': True,'Macro': [], 'IndRet': [], 'Firm': [],'FirmFix': []}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': [], 'Firm': [],'FirmFix': []}, \
                     {'MsFlag': True, 'Macro': MacroVarList,'IndRet': IndRetVarList,'Firm': FirmVarList,'FirmFix': FirmFixVarList}
                    ]

RegDesignTagList=   ['No Ms','Ms, No Control','Ms, Only Macro','Ms, Full']

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
                                                            FirmSuffix='Lag1', \
                                                            TimeFixEffect=TimeFixEffect, \
                                                            Cluster=Cluster)
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

# End of Section:
###############################################################################

#%% Output the Regression Results


### Produce the Tables
                    
## Setup
TableFolder     =   '..\\results\\TableGraph\\RegAccAbRet2Ms\\Reg'+RETVAR+'2Ms_' \
                    +TimeFixEffect+'FixEffect_'+Cluster+'ClusterStd_'


## Pooled
ExcelWriter     =   pd.ExcelWriter(TableFolder+'Pooled.xlsx')
# Main: 
for EventDict in EventDictList:
    Suffix          =   EventDict['Suffix']
    
    # [(F,No Ms,(1994,1999)),(F,No Ms,(1983,1999)),(F,No Ms,(2000,2007))]x['NoMs']
    ColList         =   [idx['No Ms',Suffix,'NoMs','1994-1999','Pooled',:], \
                         idx['No Ms',Suffix,'NoMs','1983-1999','Pooled',:], \
                         idx['No Ms',Suffix,'NoMs','1970-1999','Pooled',:], \
                         idx['No Ms',Suffix,'NoMs','2000-2007','Pooled',:], \
                         ]
    TempTable       =   pd.concat([OutputTable.loc[:,xx] for xx in ColList],axis=1)
    TempTable.columns \
                    =   pd.MultiIndex.from_tuples([(x[2],x[3]) for x in TempTable.columns])
    TempTable       =   TempTable.loc[idx[IndRetVarList+FirmVarList+FirmFixVarList+['RegInfo'],:],:]
    
    TempTable.to_excel(ExcelWriter,sheet_name=Suffix+'_'+'Benchmark_NoMs',float_format='%.3f')
    
    # [(F,90d_MsWideHF,(1994,1999)),(F,90d_MsRR,(1983,1999))]x['Ms, No Control','Ms, Only Macro','Ms, Full']
    
    GroupDictList   =   [{'Ms': '90d_MsWideHF','Period': '1994-1999','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsWideHF','Period': '2000-2007','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsWideHF','Period': '1994-2007','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsRR','Period': '1983-1999','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsRR','Period': '1970-1999','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsRR','Period': '2000-2007','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsRR','Period': '1983-2007','SubSample':'Pooled'}, \
                         {'Ms': '90d_MsRR','Period': '1970-2007','SubSample':'Pooled'}]
    ColList         =   []
    for GroupDict in GroupDictList:
        for RegType in ['Ms, No Control','Ms, Only Macro','Ms, Full']:
            ColList     =   ColList+[idx[RegType,Suffix,GroupDict['Ms'],GroupDict['Period'],GroupDict['SubSample'],:]]
    TempTable       =   pd.concat([OutputTable.loc[:,xx] for xx in ColList],axis=1)
    TempTable.columns \
                    =   pd.MultiIndex.from_tuples([(x[2],x[3],x[0]) for x in TempTable.columns])
    TempTable       =   TempTable.loc[[('Ms','Coef'),('Ms','Se'),('Ms','Tstat'),('Ms','Pvalue'), \
                                       ('const','Coef'),('const','Se'),('const','Tstat'),('const','Pvalue'), \
                                       ('RegInfo','R2'),('RegInfo','Obs')],:]
    
    TempTable.to_excel(ExcelWriter,sheet_name=Suffix+'_'+'Benchmark_Ms',float_format='%.3f')

# Save the Excel File
ExcelWriter.save()


## Splitted
for GroupVar in ['PrimaryFlag','ShelfIssueFlag']:
    ExcelWriter     =   pd.ExcelWriter(TableFolder+GroupVar+'.xlsx')
    # Main: 
    for EventDict in EventDictList:
        Suffix          =   EventDict['Suffix']
        
        # [(F,No Ms,(1994,1999)),(F,No Ms,(1983,1999)),(F,No Ms,(2000,2007))]x['NoMs']
        ColList         =   [idx['No Ms',Suffix,'NoMs','1994-1999',GroupVar,:], \
                             idx['No Ms',Suffix,'NoMs','1983-1999',GroupVar,:], \
                             idx['No Ms',Suffix,'NoMs','1970-1999',GroupVar,:], \
                             idx['No Ms',Suffix,'NoMs','2000-2007',GroupVar,:], \
                             ]
        TempTable       =   pd.concat([OutputTable.loc[:,xx] for xx in ColList],axis=1)
        TempTable.columns \
                        =   pd.MultiIndex.from_tuples([(x[3],x[5]) for x in TempTable.columns])
        TempTable       =   TempTable.loc[idx[IndRetVarList+FirmVarList+FirmFixVarList+['RegInfo'],:],:]
        
        TempTable.to_excel(ExcelWriter,sheet_name=Suffix+'_'+'Benchmark_NoMs',float_format='%.3f')
        
        # [(F,90d_MsWideHF,(1994,1999)),(F,90d_MsRR,(1983,1999))]x['Ms, Only Macro','Ms, Full']
        GroupDictList   =   [{'Ms': '90d_MsWideHF','Period': '1994-1999','SubSample':GroupVar}, \
                             {'Ms': '90d_MsWideHF','Period': '2000-2007','SubSample':GroupVar}, \
                             {'Ms': '90d_MsWideHF','Period': '1994-2007','SubSample':GroupVar}, \
                             {'Ms': '90d_MsRR','Period': '1983-1999','SubSample':GroupVar}, \
                             {'Ms': '90d_MsRR','Period': '1970-1999','SubSample':GroupVar}, \
                             {'Ms': '90d_MsRR','Period': '2000-2007','SubSample':GroupVar}, \
                             {'Ms': '90d_MsRR','Period': '1983-2007','SubSample':GroupVar}, \
                             {'Ms': '90d_MsRR','Period': '1970-2007','SubSample':GroupVar}]
        ColList         =   []
        for GroupDict in GroupDictList:
            for RegType in ['Ms, No Control','Ms, Only Macro','Ms, Full']:
                ColList     =   ColList+[idx[RegType,Suffix,GroupDict['Ms'],GroupDict['Period'],GroupDict['SubSample'],:]]
        TempTable       =   pd.concat([OutputTable.loc[:,xx] for xx in ColList],axis=1)
        TempTable.columns \
                        =   pd.MultiIndex.from_tuples([(x[2],x[3],x[0],x[5]) for x in TempTable.columns])
        TempTable       =   TempTable.loc[[('Ms','Coef'),('Ms','Se'),('Ms','Tstat'),('Ms','Pvalue'), \
                                           ('const','Coef'),('const','Se'),('const','Tstat'),('const','Pvalue'), \
                                           ('RegInfo','R2'),('RegInfo','Obs')],:]
        
        TempTable.to_excel(ExcelWriter,sheet_name=Suffix+'_'+'Benchmark_Ms',float_format='%.3f')
    
    # Save the Excel File
    ExcelWriter.save()

## Comprehensive Check
OutputTable.to_excel(TableFolder+'FullDetails.xlsx',float_format='%.3f')
# End of Section:
###############################################################################

