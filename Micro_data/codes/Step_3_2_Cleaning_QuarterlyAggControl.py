# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Wed Apr 10 12:47:34 2019
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

#%% Setup

### Load Data
DataFolder          =   "..\\temp\\"

## Macro Economic Conditions
Macro_Q             =   pickle.load(open(DataFolder+"AggTS_Macro_Quarterly.p","rb"))
AggMacroVarList     =   ['GdpGrowth','Inflation','UnemploymentRate','FedFundsRate', \
                         'VIX','RecessionFlag']
## SP500 Index Return History
SpRet_D             =   pickle.load(open(DataFolder+"AggTS_SpRet_Daily.p","rb"))

# End of Section: 
###############################################################################


                            
#%% Compute the Quarterly Statistics of SP500 Index

### Temporary Functions 

## Temporary Function Generating the Lagged Quarter
def TempFun_LagQDate(Date):
    if pd.isna(Date):
        LagQDate    =   Date
    else:
        Y   =   Date.year
        Q   =   int(np.ceil(Date.month/3))
        LagQ=   Q-1
        LagY=   Y
        if LagQ==0:
            LagQ    =   4
            LagY    =   Y-1
        
        LagQDate    =   datetime.date(LagY,LagQ*3-2,1)
    
    return LagQDate

## Temporary Function Generating the Lagged Quarter
def TempFun_NextQDate(Date):
    if pd.isna(Date):
        NextQDate   =   Date
    else:
        Y       =   Date.year
        Q       =   int(np.ceil(Date.month/3))
        NextQ   =   Q+1
        NextY   =   Y
        if NextQ==5:
            NextQ   =   1
            NextY   =   Y+1
        
        NextQDate   =   datetime.date(NextY,NextQ*3-2,1)
    
    return NextQDate

### Calculation

##Time Window for Computing the Aggregate Statistics
SpRetWindow             =   Macro_Q[['Date']].rename(columns={'Date': 'QDate'})
SpRetWindow['QDate_1']  =   SpRetWindow['QDate']
SpRetWindow['QDate_2']  =   SpRetWindow['QDate'].map(TempFun_NextQDate)

## Convert the SP500 Daily Return to Pct
SpRet_D['SpRet']        =   SpRet_D['SpRet']*100
## Generate the Data for Computing the Statistics
SpRetWindow['TempLink'] =   1
SpRet_D['TempLink']     =   1
TempData                =   SpRetWindow.merge(right=SpRet_D,how='outer', \
                                              left_on='TempLink',right_on='TempLink')
TempInd                 =   ( TempData['QDate_1']<=TempData['Date'] ) & \
                            ( TempData['QDate_2']>TempData['Date'] )
TempData                =   TempData[TempInd]

## Compute the Statistics
SpRetStat               =   TempData.groupby('QDate')['SpRet'] \
                            .agg(['sum','mean','std','median','count']) \
                            .rename(columns={'sum': 'Sum', \
                                             'mean': 'Mean', 'std': 'Std', \
                                             'median': 'Median','count': 'Obs'})
SpRetStat.columns       =   ['SpRet_'+x for x in SpRetStat.columns]
SpRetStat.reset_index(inplace=True)

Agg_SpRet               =   SpRetStat[['QDate']+ \
                                      ['SpRet_Sum','SpRet_Mean','SpRet_Std','SpRet_Median']] \
                            .rename(columns={'QDate': 'Date'})
# End of Section: 
###############################################################################

#%% Merge into the Final Data Set

### Merge the Data Sets
AggControl              =   Macro_Q[['Date']+AggMacroVarList] \
                            .merge(Agg_SpRet,how='left',on='Date')

### Clean the Data Set

pickle.dump(AggControl,open(DataFolder+"AggControl_Q.p","wb"))
# End of Section: 
###############################################################################