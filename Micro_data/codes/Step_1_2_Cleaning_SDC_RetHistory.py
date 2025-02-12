# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code computes the Return History around the Issuance Events.
    
Version History:
    Created: Fri Mar 29 11:25:16 2019
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


#%% Generating the Sample for Running the 1-Factor Model Regression


### Raw Data Sets

## Read-in the SEO Deal Information and CRSP History Information
DataFolder          =   "..\\datasets\\SDC\\Download_20190424\\"
CRSP_SDC            =   pickle.load(open(DataFolder+'CRSP_SDC.p','rb'))
CRSP_SP             =   pickle.load(open(DataFolder+'CRSP_SP.p','rb'))
DataFolder          =   "..\\temp\\"
SDC_IssuanceInfo    =   pickle.load(open(DataFolder+'SDC_IssuanceInfo.p','rb'))

## Download the Aggregate Economic History

# Daily Risk-free Interest Rate
try:
    RfRate          =   pickle.load(open(DataFolder+"RfRate.p",'rb'))
except:
    fred                =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
    RfRate              =   fred.get_series('DTB3')
    RfRate              =   pd.DataFrame(RfRate/100/365,columns={'Rf'})
    RfRate.reset_index(inplace=True)
    RfRate.rename(columns={'index': 'Date'},inplace=True)
    RfRate['Date']      =   RfRate['Date'].apply(lambda x: x.date())
    pickle.dump(RfRate,open(DataFolder+"RfRate.p",'wb'))


### Construct the Price History Sample
TempIDVarList       =   ['IssueID','FilingDate','LaunchDate','IssueDate','CUSIP','CUSIP_8digit']
CRSP_SDC            =   SDC_IssuanceInfo[TempIDVarList] \
                        .merge(right=CRSP_SDC,how='left',on=['CUSIP','CUSIP_8digit'])

## Preliminary Date Cleaning
# Date Format
CRSP_SDC['Date']            =   pd.to_datetime(CRSP_SDC['Date']).apply(lambda x: x.date())
# Sorted Panel
CRSP_SDC                    =   CRSP_SDC.sort_values(['IssueID','Date']).reset_index(drop=True)
# Price
'''
In CRSP, the reported daily price is typically the closing price of the trading
day. If there is no closing price available, the reported price will be the 
average bid/ask price, with a negative sign.
'''
CRSP_SDC['Price']           =   CRSP_SDC['Price'].abs()
# Eliminate the Replicated Obs.
'''
In CRSP, there are some duplicated observations which need to be eliminated.
'''
print('There are '+ \
      str(np.round(CRSP_SDC.duplicated(['IssueID','Date','Price'],keep=False).sum()/CRSP_SDC.shape[0]*100,2)) + \
      '% duplicated observations with same IssueID, Date and Price.')
print('There are '+ \
      str(np.round(CRSP_SDC.duplicated(['IssueID','Date'],keep=False).sum()/CRSP_SDC.shape[0]*100,2)) + \
      '% duplicated observations with same IssueID and Date.')

CRSP_SDC                    =   CRSP_SDC.drop_duplicates(subset=['IssueID','Date'], \
                                                         keep='first') \
                                .sort_values(['IssueID','Date']) \
                                .reset_index(drop=True)

## Compute the Daily Return
CRSP_SDC['LogPrice']        =   np.log(CRSP_SDC['Price'])
CRSP_SDC['DiffLogPrice']    =   CRSP_SDC.groupby('IssueID')['LogPrice'].diff()

CRSP_SDC['DiffDate']        =   CRSP_SDC.groupby('IssueID')['Date'].diff().dt.days

CRSP_SDC['LagDate']         =   CRSP_SDC.groupby('IssueID')['Date'].shift()
TempInd                     =   ~(pd.isna(CRSP_SDC['Date']) | pd.isna(CRSP_SDC['LagDate']))
CRSP_SDC.loc[TempInd,'DiffBusDate'] \
                            =   np.busday_count(CRSP_SDC.loc[TempInd,'LagDate'].values.tolist(), \
                                                CRSP_SDC.loc[TempInd,'Date'].values.tolist())

CRSP_SDC['Ret_NAdj']        =   CRSP_SDC['DiffLogPrice']/CRSP_SDC['DiffDate']
CRSP_SDC['Ret_Adj']         =   CRSP_SDC['DiffLogPrice']/CRSP_SDC['DiffBusDate']

## Compute the Relative Date
EventDictList               =   [{'DateVar': 'FilingDate','Suffix': 'F'}, \
                                 {'DateVar': 'LaunchDate','Suffix': 'L'}, \
                                 {'DateVar': 'IssueDate','Suffix': 'I'}]
for EventDict in EventDictList:
    TempInd                     =   ~( pd.isna(CRSP_SDC[EventDict['DateVar']]) | \
                                       pd.isna(CRSP_SDC['Date']) )
    CRSP_SDC[EventDict['Suffix']+'Date_NAdj'] \
                                =   (CRSP_SDC['Date']-CRSP_SDC[EventDict['DateVar']]).dt.days
    CRSP_SDC.loc[TempInd,EventDict['Suffix']+'Date_Adj'] \
                                =   np.busday_count(CRSP_SDC.loc[TempInd,EventDict['DateVar']].values.tolist(), \
                                                    CRSP_SDC.loc[TempInd,'Date'].values.tolist())
    

### Prepare the SP500 Return History

## Preliminary Cleaning
# Date Format
CRSP_SP['Date']             =   pd.to_datetime(CRSP_SP['Date']).apply(lambda x: x.date())
# Sorted Panel
CRSP_SP                     =   CRSP_SP.drop_duplicates(['Date']).sort_values(['Date']) \
                                .reset_index(drop=True)
## Compute the Return
CRSP_SP['DiffLogSpIdx']     =   np.log(CRSP_SP['SpIdx']).diff()
CRSP_SP['DiffDate']         =   CRSP_SP['Date'].diff().dt.days
CRSP_SP['LagDate']          =   CRSP_SP['Date'].shift()
TempInd                     =   ~(pd.isna(CRSP_SP['Date']) | pd.isna(CRSP_SP['LagDate']))
CRSP_SP.loc[TempInd,'DiffBusDate'] \
                            =   np.busday_count(CRSP_SP.loc[TempInd,'LagDate'].values.tolist(), \
                                                CRSP_SP.loc[TempInd,'Date'].values.tolist())
CRSP_SP['SpRet_NAdj']       =   CRSP_SP['DiffLogSpIdx']/CRSP_SP['DiffDate']
CRSP_SP['SpRet_Adj']        =   CRSP_SP['DiffLogSpIdx']/CRSP_SP['DiffBusDate']


### Construct the Data Sample for Factor Model Regression

## Merge Different Data sets into CRSP_SDC
#+CRSP_SP
CRSP_SDC_VarList            =   ['IssueID', 'FilingDate', 'LaunchDate', 'IssueDate', \
                                 'Date','Ret_NAdj','Ret_Adj']+ \
                                [x+'Date_'+y for x in ['F','L','I'] for y in ['NAdj','Adj']]
CRSP_SP_VarList             =   ['Date','SpRet_NAdj','SpRet_Adj']

SDC_Ret                     =   CRSP_SDC[CRSP_SDC_VarList] \
                                .merge(right=CRSP_SP[CRSP_SP_VarList],how='left',on='Date')
# +Risk-free Return
SDC_Ret                     =   SDC_Ret.merge(right=RfRate,how='left',on='Date')

## Compute the Excess Return
for RetVar in ['Ret','SpRet']:
    for Type in ['NAdj','Adj']:
        SDC_Ret['Ex'+RetVar+'_'+Type]   =   SDC_Ret[RetVar+'_'+Type]-SDC_Ret['Rf']

## Sorted Panel
SDC_Ret                     =   SDC_Ret.sort_values(['IssueID','Date']) \
                                .reset_index(drop=True)

pickle.dump(SDC_Ret,open(DataFolder+'SDC_Ret.p','wb'))
# End of Section: 
###############################################################################


#%% Generate the Wide Panel of Return and Accumulated Return


### Setup

## Load-in the Data
DataFolder      =   "..\\temp\\"
DS_Ret          =   pickle.load(open(DataFolder+"SDC_Ret.p",'rb'))

## Setup
StartEndDate    =   [-100,160]
DateVar         =   'Date_Adj'
RetVar          =   'Ret_Adj'

### Collect the Information about the Event Coverage

## Temporary Function Computing the Start/End day and number of days before/after the event date
def TempFun_DateSumStat(DS,StartEndDate,DateType,DateVar,RetVar):
    TempDateVar     =   DateType+DateVar
    TempRetVar      =   RetVar
    TempDS          =   DS[['IssueID',TempDateVar,TempRetVar]] \
                        .dropna(subset=[TempRetVar]) \
                        .reset_index(drop=True)
    TempDS['Obs_L'] =   (TempDS[TempDateVar]<0) & (TempDS[TempDateVar]>=StartEndDate[0])
    TempDS['Obs_R'] =   (TempDS[TempDateVar]>0) & (TempDS[TempDateVar]<=StartEndDate[1])
    
    TempSumStat_0   =   TempDS.groupby('IssueID')[TempDateVar].agg(['min','max']) \
                        .rename(columns={'min': DateType+'_MinDate','max': DateType+'_MaxDate'})
    TempSumStat_1   =   TempDS.groupby('IssueID')[['Obs_L','Obs_R']].sum() \
                        .rename(columns={'Obs_L': DateType+'_Obs_L','Obs_R': DateType+'_Obs_R'})
    TempSumStat     =   TempSumStat_0.merge(right=TempSumStat_1,how='outer', \
                                            left_index=True,right_index=True) \
                        .reset_index()
    return TempSumStat

## List of IssueID which has good coverage of the event
'''
4 requirement: start before the left window end, end after the right window end,
enough days before and after the event date and between the window ends.
'''
DS_Ret_Info     =   TempFun_DateSumStat(DS_Ret,StartEndDate,'F',DateVar,RetVar) \
                    .merge(right=TempFun_DateSumStat(DS_Ret,StartEndDate,'L',DateVar,RetVar), \
                           how='outer',on='IssueID') \
                    .merge(right=TempFun_DateSumStat(DS_Ret,StartEndDate,'I',DateVar,RetVar), \
                           how='outer',on='IssueID')
GoodIssueID     =   {}
for ILF in ['F','L','I']:
    GoodIssueID[ILF]    =   DS_Ret_Info.loc[ ( DS_Ret_Info[ILF+'_MinDate']<=StartEndDate[0] ) & \
                                             ( DS_Ret_Info[ILF+'_MaxDate']>=StartEndDate[1] ) & \
                                             ( DS_Ret_Info[ILF+'_Obs_L']>=2/3*np.abs(StartEndDate[0]) ) & \
                                             ( DS_Ret_Info[ILF+'_Obs_R']>=2/3*np.abs(StartEndDate[1]) ), \
                                             'IssueID'].tolist()


### Compute the Return or Accumulated Return History within Event Window
WindowList      =   [[StartEndDate[0],x] for x in range(StartEndDate[0],StartEndDate[1]+1)]+ \
                    [[0,x] for x in range(0,10+1)]+ \
                    [[-x,x] for x in range(1,10+1)]
## RetHist for Different Types of Event Date
RetHistDict     =   {}

for Suffix in ['F','L','I']:
    # Setup
    RelDateVar          =   Suffix+'Date_Adj'
    # Eliminate Irrelevant Relative Periods
    TempInd             =   ( DS_Ret[RelDateVar]>=StartEndDate[0] ) & \
                            ( DS_Ret[RelDateVar]<=StartEndDate[1] )
    TempDS              =   DS_Ret.loc[TempInd,['IssueID',RelDateVar,RetVar]] \
                            .sort_values(['IssueID',RelDateVar])
    
    # Transform the Long Table to Wide Table
    TempDS              =   TempDS.pivot(index='IssueID',columns=RelDateVar,values=RetVar)
    TempDS.columns      =   [Suffix+'_Ret_'+str(int(x)) for x in TempDS.columns]
    TempDS.dropna(how='all',inplace=True)
    # Generate the Accumulated Abnormal Return
    for Window in WindowList:
        WinStart            =   Window[0]
        WinEnd              =   Window[1]
        ColList             =   [Suffix+'_Ret_'+str(int(x)) for x in range(WinStart,WinEnd+1)]
        VarName             =   Suffix+'_AccRet_'+str(WinStart)+'_'+str(WinEnd)
        TempDS[VarName]     =   TempDS[ColList].sum(axis=1)/TempDS[ColList].count(axis=1)* \
                                ( WinEnd-WinStart+1 )
    
    RetHistDict[Suffix] =   TempDS.sort_index().copy()


## Merge the Data Set
RetHist         =   RetHistDict['F'].loc[GoodIssueID['F'],:] \
                    .merge(right=RetHistDict['L'].loc[GoodIssueID['L'],:], \
                           how='outer',left_index=True,right_index=True) \
                    .merge(right=RetHistDict['I'].loc[GoodIssueID['I'],:], \
                           how='outer',left_index=True,right_index=True) \
                    .reset_index()

DataFolder      =   "..\\temp\\"
pickle.dump(RetHist,open(DataFolder+'SDC_Ret_Wide.p','wb'))
# End of Section:
###############################################################################
