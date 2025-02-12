# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Fri May 10 16:21:50 2019
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
## Database API
from fredapi import Fred


# End of Section: Import Moduels
###############################################################################


#%% Setup Work Directory

## Office Desktop Directory
os.chdir("E:\\Dropbox")
## Home Desktop Directory
#os.chdir("L:\Dropbox")

##Windows System Path
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Macro_data\\codes")


# End of Section: Setup Work Directory
###############################################################################

#%% Import Self-written Functions
exec(open('Fun_RomerRomerReg.py').read())
exec(open('Toolkit\\Toolbox_Graph.py').read())
# End of Section: Import Self-written Functions
###############################################################################


#%% Regression Results based on Monthly Data


### Construct the Sample 

## Read-in Data
DataFolder      =   "..\\temp\\"
# Quarterly Data Sample
Sample_Q        =   pickle.load(open(DataFolder+"Sample_Q.p",'rb'))


### Transform the Variables
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
DF              =   DF[(DF.index>=datetime.datetime(1996,10,1)) & \
                       (DF.index<=datetime.datetime(2016,12,31))]

## Temporary Functions for Different Types of Detrending
# Python's Internal Function
def Cycle_Python(DF,VarList=DF.columns.tolist(),Freq=4):
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
def Cycle_Polynomial(DF,VarList=DF.columns.tolist(),Freq='Quarterly',Order=1):
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
def Cycle_HP(DF,VarList=DF.columns.tolist(),Freq='Quarterly'):
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
def Cycle_BK(DF,VarList=DF.columns.tolist(),Freq='Quarterly'):
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


### Cyclical Data Set
DF_Cycle_PY     =   Cycle_Python(DF)
DF_Cycle_PO     =   Cycle_Polynomial(DF)
DF_Cycle_HP     =   Cycle_HP(DF)
DF_Cycle_BK     =   Cycle_BK(DF)

# End of Section:
###############################################################################
