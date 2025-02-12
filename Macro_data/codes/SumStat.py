# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Wed Mar 20 10:57:13 2019
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
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
## Statistical Tools
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
## Database API
from fredapi import Fred
# End of Section: Import Moduels
###############################################################################


#%% Setup Work Directory

try:
    # Office Desktop Directory
    os.chdir("E:\\Dropbox")
except:
    # Home Desktop Directory
    os.chdir("L:\Dropbox")
    
#Windows System Path
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Macro_data\\codes")
# End of Section: Setup Work Directory
###############################################################################

#%% Import Self-written Functions

exec(open('Toolkit\\Toolbox_Graph.py').read())
# End of Section: Import Self-written Functions
###############################################################################

#%% Temporary Functions to Extract the Cyclical Component of Time-series
# Python's Internal Function
def Cycle_Python(DF,Freq=4):
    VarList     =   DF.columns.tolist()
    InitiateFlag    =   1
    for TempVar in VarList:
        Temp        =   DF[TempVar]
        Temp.dropna(inplace=True)
        Temp        =   seasonal_decompose(Temp,freq=Freq)
        if InitiateFlag:
            Cycle           =   Temp.resid.to_frame(TempVar)
            InitiateFlag    =   0
        else:
            Cycle   =   Cycle.merge(Temp.resid.to_frame(TempVar),how='outer', \
                                    left_index=True,right_index=True)
    return Cycle
# Polinomial Detrend
def Cycle_Polynomial(DF,Freq='Quarterly',Order=1):
    VarList     =   DF.columns.tolist()
    
    InitiateFlag    =   1
    for TempVar in VarList:
        Temp        =   DF[TempVar]
        Temp.dropna(inplace=True)
        Temp        =   sm.tsa.detrend(Temp,Order).to_frame(TempVar)
        if Freq=='Quarterly':        
            Temp['Season']  =   Temp.index.map(lambda x: np.ceil(x.month/3))
        elif Freq=='Monthly':
            Temp['Season']  =   Temp.index.map(lambda x: x.month)
        Temp_Season =   Temp.groupby('Season')[TempVar].mean().to_frame('SeasonalComponent')
        Temp        =   Temp.merge(right=Temp_Season,left_on='Season',right_index=True)
        Temp[TempVar] \
                    =   Temp[TempVar]-Temp['SeasonalComponent']
        Temp.drop(['Season','SeasonalComponent'],axis=1,inplace=True)
        if InitiateFlag:
            Cycle       =   Temp
            InitiateFlag=   0
        else:
            Cycle   =   Cycle.merge(Temp,how='outer',left_index=True,right_index=True)
    return Cycle
# HP Detrend
def Cycle_HP(DF,Freq='Quarterly'):
    VarList     =   DF.columns.tolist()
    
    if Freq=='Quarterly':
        Lambda      =   1600
    elif Freq=='Monthly':
        Lambda      =   1600*3**4
        
    InitiateFlag    =   1
    for TempVar in VarList:
        Temp        =   DF[TempVar]
        Temp.dropna(inplace=True)
        Temp        =   sm.tsa.filters.hpfilter(Temp,lamb=Lambda)[0].to_frame(TempVar)
        
        if Freq=='Quarterly':        
            Temp['Season']  =   Temp.index.map(lambda x: np.ceil(x.month/3))
        elif Freq=='Monthly':
            Temp['Season']  =   Temp.index.map(lambda x: x.month)
            
        Temp_Season =   Temp.groupby('Season')[TempVar].mean().to_frame('SeasonalComponent')
        Temp        =   Temp.merge(right=Temp_Season,left_on='Season',right_index=True)
        Temp[TempVar] \
                    =   Temp[TempVar]-Temp['SeasonalComponent']
        Temp.drop(['Season','SeasonalComponent'],axis=1,inplace=True)
        if InitiateFlag:
            Cycle       =   Temp
            InitiateFlag=   0
        else:
            Cycle   =   Cycle.merge(Temp,how='outer',left_index=True,right_index=True)
    return Cycle
# Band Pass Detrend
def Cycle_BK(DF,Freq='Quarterly'):
    VarList     =   DF.columns.tolist()
    
    if Freq=='Quarterly':
        Low         =   6
        High        =   32
        K           =   12
    elif Freq=='Annual':
        Low         =   1.5
        High        =   8
        K           =   3
        
    InitiateFlag    =   1
    for TempVar in VarList:
        Temp        =   DF[TempVar]
        Temp.dropna(inplace=True)
        Temp        =   sm.tsa.filters.bkfilter(Temp,Low,High,K).to_frame(TempVar)
        if InitiateFlag:
            Cycle       =   Temp
            InitiateFlag=   0
        else:
            Cycle   =   Cycle.merge(Temp,how='outer',left_index=True,right_index=True)
    return Cycle


# End of Section:
###############################################################################
    

#%% Clean the Data


### Generate the Sample

## Read in Data
DataFolder      =   "..\\temp\\"
Sample_Q        =   pickle.load(open(DataFolder+"Sample_Q.p",'rb'))

## Clean the Data
DF              =   Sample_Q.copy()[[]]

## Different Types of Transformation
# Level
VarList_Level   =   ['EquityGrossIssue_LagTotalAsset_Cor','DebtGrossIssue_LagTotalAsset_Cor', \
                     'EquityFin_LagTotalAsset_Cor','EquityFin_LagTotalAsset_NonCor', \
                     'DebtFin_LagTotalAsset_Cor','DebtFin_LagTotalAsset_NonCor', \
                     'EquityNetIssue_LagTotalAsset_Cor','DivPayment_LagTotalAsset_Cor', \
                     'TotalGrossIssue_LagTotalAsset_Cor', \
                     'EquityFin_LagTotalAsset_Agg','DebtFin_LagTotalAsset_Agg', \
                     'ExternalFin_LagTotalAsset_Cor','ExternalFin_LagTotalAsset_NonCor', \
                     'ExternalFin_LagTotalAsset_Agg', \
                     'Inv_LagTotalAsset_Cor','Inv_LagTotalAsset_NonCor','Inv_LagTotalAsset_Agg', \
                     'DebtFin_GrossValAdd_Cor','DebtFin_GrossValAdd_NonCor','DebtFin_GrossValAdd_Agg', \
                     'EquityFin_GrossValAdd_Cor','EquityFin_GrossValAdd_NonCor','EquityFin_GrossValAdd_Agg',
                     'ExternalFin_GrossValAdd_Cor','ExternalFin_GrossValAdd_NonCor','ExternalFin_GrossValAdd_Agg',
                     'IpoNum_Cor','SeoNum_Cor', \
                     'AggIpoSum_LagTotalAsset_Cor','AggSeoSum_LagTotalAsset_Cor', \
                     'AggIpoNum_Cor','AggSeoNum_Cor']
for TempVar in VarList_Level:
    DF[TempVar]             =   Sample_Q[TempVar]
    
VarList_Level   =   VarList_Level
# Log-Level
VarList_Log     =   ['GDP','INV','EquityGrossIssue_Cor','DebtGrossIssue_Cor']
for TempVar in VarList_Log:
    DF['Log_'+TempVar]      =   np.log(Sample_Q[TempVar])

VarList_Log     =   ['Log_'+x for x in VarList_Log]
# Difference
VarList_Diff    =   ['EquityGrossIssue_LagTotalAsset_Cor','DebtGrossIssue_LagTotalAsset_Cor', \
                     'EquityFin_LagTotalAsset_Cor','EquityFin_LagTotalAsset_NonCor', \
                     'DebtFin_LagTotalAsset_Cor','DebtFin_LagTotalAsset_NonCor', \
                     'EquityNetIssue_LagTotalAsset_Cor','DivPayment_LagTotalAsset_Cor', \
                     'Inv_LagTotalAsset_Cor','Inv_LagTotalAsset_NonCor','Inv_LagTotalAsset_Agg', \
                     'IpoNum_Cor','SeoNum_Cor', \
                     'AggIpoSum_LagTotalAsset_Cor','AggSeoSum_LagTotalAsset_Cor', \
                     'AggIpoNum_Cor','AggSeoNum_Cor']
for TempVar in VarList_Diff:
    DF['Diff_'+TempVar]     =   Sample_Q[TempVar].diff()
    
VarList_Diff    =   ['Diff_'+x for x in VarList_Diff]
# Log-Difference
VarList_LogDiff =   ['EquityGrossIssue_Cor','DebtGrossIssue_Cor','GDP','INV', \
                     'IpoNum_Cor','SeoNum_Cor']
for TempVar in VarList_LogDiff:
    DF['LogDiff_'+TempVar]  =   np.log(Sample_Q[TempVar]).diff()

VarList_LogDiff =   ['LogDiff_'+x for x in VarList_LogDiff]

## Replace the Extreme Value as Missing Value
DF.replace([-np.inf,np.inf],np.nan,inplace=True)


### Extract the Cyclical Component

## Restrict the Sample Period
StartEndDate    =   [datetime.datetime(1970,1,1),datetime.datetime(2016,12,31)]
DF              =   DF[(DF.index>=StartEndDate[0]) & (DF.index<=StartEndDate[1])]
SampleSuffix    =   str(StartEndDate[0].year)+'Q'+str(int(np.ceil(StartEndDate[0].month/3)))+'_'+ \
                    str(StartEndDate[1].year)+'Q'+str(int(np.ceil(StartEndDate[1].month/3)))

## Cyclical Data Set
DF_Cycle_PY     =   Cycle_Python(DF)
DF_Cycle_PO     =   Cycle_Polynomial(DF)
DF_Cycle_HP     =   Cycle_HP(DF)
DF_Cycle_BK     =   Cycle_BK(DF)


### Compute the Summary Statistics

## Mean
LevelStat       =   DF.agg(['min','max','mean']).T*100

## Std and Correlation with GDP/GDP Growth
StdCorr_PY      =   pd.concat([DF_Cycle_PY.std().to_frame('Std')*100, \
                               DF_Cycle_PY.corr()[['Log_GDP','LogDiff_GDP']]], \
                              axis=1,join='outer')
StdCorr_PO      =   pd.concat([DF_Cycle_PO.std().to_frame('Std')*100, \
                               DF_Cycle_PO.corr()[['Log_GDP','LogDiff_GDP']]], \
                              axis=1,join='outer')
StdCorr_HP      =   pd.concat([DF_Cycle_HP.std().to_frame('Std')*100, \
                               DF_Cycle_HP.corr()[['Log_GDP','LogDiff_GDP']]], \
                              axis=1,join='outer')
StdCorr_BK      =   pd.concat([DF_Cycle_BK.std().to_frame('Std')*100, \
                               DF_Cycle_BK.corr()[['Log_GDP','LogDiff_GDP']]], \
                              axis=1,join='outer')

## Merged Statistics
SumStat         =   pd.concat([LevelStat,StdCorr_PY,StdCorr_PO,StdCorr_HP,StdCorr_BK], \
                              axis=1,join='outer', \
                              keys=['','PY','PO','HP','BK'])

## Output Summary Statistics
IndexList       =   ['EquityFin_LagTotalAsset_Cor', \
                     'EquityNetIssue_LagTotalAsset_Cor', \
                     'DivPayment_LagTotalAsset_Cor', \
                     'DebtFin_LagTotalAsset_Cor', \
                     'ExternalFin_LagTotalAsset_Cor', \
                     'EquityFin_LagTotalAsset_NonCor', \
                     'DebtFin_LagTotalAsset_NonCor', \
                     'ExternalFin_LagTotalAsset_NonCor', \
                     'EquityFin_LagTotalAsset_Agg', \
                     'DebtFin_LagTotalAsset_Agg', \
                     'ExternalFin_LagTotalAsset_Agg', \
                     'EquityGrossIssue_LagTotalAsset_Cor', \
                     'DebtGrossIssue_LagTotalAsset_Cor', \
                     'TotalGrossIssue_LagTotalAsset_Cor', \
                     'AggIpoSum_LagTotalAsset_Cor', \
                     'AggSeoSum_LagTotalAsset_Cor', \
                     'AggIpoNum_Cor','AggSeoNum_Cor', \
                     'IpoNum_Cor','SeoNum_Cor']

Output          =   SumStat.loc[IndexList,:]

TableFolder     =   '..\\results\\SumStat\\'
Output.to_excel(TableFolder+'SumStat_'+SampleSuffix+'.xlsx', \
                engine='xlsxwriter',float_format="%.3f")
# End of Section:
###############################################################################


#%% The Summary Statistics of the Underlying Details of Equity Financing

### Construct the Sample
DF              =   Sample_Q.copy()[[]]

## Different Types of Transformation
# Level
VarList_Level   =   ['EquityNetIssue_LagTotalAsset_Cor']+ \
                    ['EquityIssue_LagTotalAsset_Cor', \
                     'EquityIssueIPO_LagTotalAsset_Cor','EquityIssueSEO_LagTotalAsset_Cor', \
                     'EquityIssuePrivate_LagTotalAsset_Cor']+ \
                    ['EquityRetire_LagTotalAsset_Cor', \
                     'EquityRepurchase_LagTotalAsset_Cor','EquityMA_LagTotalAsset_Cor']
for TempVar in VarList_Level:
    DF[TempVar]             =   Sample_Q[TempVar]
    
VarList_Level   =   VarList_Level
# Log-Level
VarList_Log     =   ['GDP']
for TempVar in VarList_Log:
    DF['Log_'+TempVar]      =   np.log(Sample_Q[TempVar])

VarList_Log     =   ['Log_'+x for x in VarList_Log]
# Difference
VarList_Diff    =   []
for TempVar in VarList_Diff:
    DF['Diff_'+TempVar]     =   Sample_Q[TempVar].diff()
    
VarList_Diff    =   ['Diff_'+x for x in VarList_Diff]
# Log-Difference
VarList_LogDiff =   []
for TempVar in VarList_LogDiff:
    DF['LogDiff_'+TempVar]  =   np.log(Sample_Q[TempVar]).diff()

VarList_LogDiff =   ['LogDiff_'+x for x in VarList_LogDiff]

## Replace the Extreme Value as Missing Value
DF.replace([-np.inf,np.inf],np.nan,inplace=True)


### Extract the Cyclical Component

## Restrict the Sample Period
StartEndDate    =   [datetime.datetime(1996,10,1),datetime.datetime(2016,12,31)]
DF              =   DF[(DF.index>=StartEndDate[0]) & (DF.index<=StartEndDate[1])]
SampleSuffix    =   str(StartEndDate[0].year)+'Q'+str(int(np.ceil(StartEndDate[0].month/3)))+'_'+ \
                    str(StartEndDate[1].year)+'Q'+str(int(np.ceil(StartEndDate[1].month/3)))

## Extract the Cyclical Component 
DF_Cycle_BK     =   Cycle_BK(DF)

## Mean
LevelStat       =   DF.agg(['min','max','mean']).T*100

## Std and Correlation with GDP/GDP Growth
StdCorr_BK      =   pd.concat([DF_Cycle_BK.std().to_frame('Std')*100, \
                               DF_Cycle_BK.corr()['Log_GDP']], \
                              axis=1,join='outer')

## Merged Statistics
SumStat         =   pd.concat([LevelStat,StdCorr_BK], \
                              axis=1,join='outer', \
                              keys=['','BK'])

## Output Summary Statistics
IndexList       =   ['EquityNetIssue_LagTotalAsset_Cor', \
                     'EquityIssue_LagTotalAsset_Cor', \
                     'EquityIssueIPO_LagTotalAsset_Cor', \
                     'EquityIssueSEO_LagTotalAsset_Cor', \
                     'EquityIssuePrivate_LagTotalAsset_Cor', \
                     'EquityRetire_LagTotalAsset_Cor', \
                     'EquityRepurchase_LagTotalAsset_Cor', \
                     'EquityMA_LagTotalAsset_Cor']

Output          =   SumStat.loc[IndexList,:]

TableFolder     =   '..\\results\\SumStat\\'
Output.to_excel(TableFolder+'SumStat_EFinDetails_'+SampleSuffix+'.xlsx', engine='xlsxwriter')
# End of Section:
###############################################################################