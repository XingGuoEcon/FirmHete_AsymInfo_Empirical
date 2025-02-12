# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Mon Apr  8 21:59:45 2019
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

#%% NBER Recession Date Information

### Load in the Original Data
RecessionDates      =   pd.read_excel("..\\datasets\\RecessionDates\\NBER_RecessionDates.xlsx")


### Clean the Data

## Date Format
RecessionDates['PeakMonth']     =   pd.to_datetime(RecessionDates['PeakMonth']).dt.date
RecessionDates['TroughMonth']   =   pd.to_datetime(RecessionDates['TroughMonth']).dt.date
RecessionDates.dropna(inplace=True)

## Historical Monthly Dummy Variables
MonthList           =   [datetime.date(yy,mm,1) for yy in range(1900,2019) for mm in range(1,13)]
RecessionFlagList   =   []
for Month in MonthList:
    if ( (RecessionDates['PeakMonth']<=Month) &  (RecessionDates['TroughMonth']>=Month) ).sum()>0:
        RecessionFlagList.append(1)
    else:
        RecessionFlagList.append(0)
RecessionFlag_DS    =   pd.concat([pd.Series(MonthList),pd.Series(RecessionFlagList)], \
                                   axis=1,keys=['MDate','RecessionFlag'])

## Aggregate to Quarterly Frequency
RecessionFlag_DS['Date'] \
                    =   RecessionFlag_DS['MDate'].map(lambda x: datetime.date(x.year,int(np.ceil(x.month/3)*3-2),1))
RecessionFlag_DS_Q  =   RecessionFlag_DS.groupby('Date')['RecessionFlag'].max().to_frame().reset_index()
# End of Section:
###############################################################################

#%% Aggregate Macro Economic Conditions from Fred

### Read-in or Download the Quarterly Aggregate Economic Variables
DataFolder      =   "..\\temp\\"

## Quarterly Data
QAggVarList     =   ['GdpGrowth','GdpDef']                    
QFredIdList     =   ['A191RL1Q225SBEA','GDPDEF']

fred            =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
for ii in range(len(QAggVarList)):
    QAggVar     =   QAggVarList[ii]
    TempTS      =   fred.get_series(QFredIdList[ii]).to_frame(name=QAggVar)
    if ii==0:
        QAggEconTS      =   TempTS
    else:
        QAggEconTS      =   QAggEconTS.merge(TempTS,how='outer', \
                                             left_index=True,right_index=True)
QAggEconTS['Inflation']     =   np.log(QAggEconTS['GdpDef']).diff()*100*4 

## Monthly Data
MAggVarList     =   ['UnemploymentRate','FedFundsRate']                    
MFredIdList     =   ['UNRATE','FEDFUNDS']

fred            =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
for ii in range(len(MAggVarList)):
    MAggVar     =   MAggVarList[ii]
    TempTS      =   fred.get_series(MFredIdList[ii]).to_frame(name=MAggVar)
    if ii==0:
        MAggEconTS      =   TempTS
    else:
        MAggEconTS      =   MAggEconTS.merge(TempTS,how='outer', \
                                             left_index=True,right_index=True)
MAggEconTS['QDate']      =   MAggEconTS.index \
                            .map(lambda x: datetime.date(x.year,int(np.ceil(x.month/3)*3-2),1))
M2QAggEconTS            =   MAggEconTS.groupby('QDate').mean()

## Daily Data
DAggVarList     =   ['VIX']                    
DFredIdList     =   ['VIXCLS']

fred            =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
for ii in range(len(DAggVarList)):
    DAggVar     =   DAggVarList[ii]
    TempTS      =   fred.get_series(DFredIdList[ii]).to_frame(name=DAggVar)
    if ii==0:
        DAggEconTS      =   TempTS
    else:
        DAggEconTS      =   DAggEconTS.merge(TempTS,how='outer', \
                                             left_index=True,right_index=True)
DAggEconTS['QDate']     =   DAggEconTS.index \
                            .map(lambda x: datetime.date(x.year,int(np.ceil(x.month/3)*3-2),1))
D2QAggEconTS            =   DAggEconTS.groupby('QDate').mean()

## Merge Different Data Sets from Fred
AggEconTS       =   pd.concat([QAggEconTS,M2QAggEconTS,D2QAggEconTS],axis=1,join='outer')
AggEconTS       =   AggEconTS.reset_index().rename(columns={'index': 'Date'})
AggEconTS['Date']=  AggEconTS['Date'].apply(lambda x: x.date())

## Merge with the NBER Date Information
AggEconTS       =   AggEconTS.merge(right=RecessionFlag_DS_Q,how='left',on='Date')

## Save the Data
pickle.dump(AggEconTS,open(DataFolder+'AggTS_Macro_Quarterly.p','wb'))

# End of Section:
###############################################################################

#%% Daily History of SP500 Index


### Download Data
db              =   wrds.Connection()
SP500           =   db.get_table('crsp','dsp500',columns=['caldt','spindx'])


### Clean the Data

## Drop Missing Obs.
SpHist                  =   SP500.rename(columns={'caldt': 'Date', 'spindx': 'SpIndx'}) \
                            .dropna().reset_index(drop=True).sort_values('Date')
## Compute the Daily Return
SpHist['LagDate']       =   SpHist['Date'].shift()
SpHist['LogDiffIndx']   =   ( np.log(SpHist['SpIndx']) ).diff()
TempInd                 =   ~(pd.isna(SpHist['Date']) | pd.isna(SpHist['LagDate']))
SpHist.loc[TempInd,'DiffBusDate'] \
                        =   np.busday_count(SpHist.loc[TempInd,'LagDate'].values.tolist(), \
                                            SpHist.loc[TempInd,'Date'].values.tolist())
SpHist['SpRet']         =   SpHist['LogDiffIndx']/SpHist['DiffBusDate']

SpHist                  =   SpHist[SpHist['DiffBusDate']<=2]
SpHist                  =   SpHist[['Date','SpIndx','SpRet']].reset_index(drop=True)

### Save the Data
DataFolder      =   "..\\temp\\"
pickle.dump(SpHist,open(DataFolder+'AggTS_SpRet_Daily.p','wb'))

# End of Section:
###############################################################################