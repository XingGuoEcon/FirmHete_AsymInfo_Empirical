# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Sat May 11 10:23:52 2019
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
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Macro_data\\codes")

# End of Section: Setup Working Directory
###############################################################################

#%% Import and Clean the Compustat Quarterly Data 

DataFolder      =   "..\\..\\..\\..\\..\\Data\\Compustat\\Quarterly\\"


### Firm Sample

## Import
FirmSample          =   pickle.load(open(DataFolder+"Compustat_Names.p","rb"))

## Clean Data
FirmSample          =   FirmSample[['gvkey','sic']]
FirmSample['sic']   =   pd.to_numeric(FirmSample['sic'],errors='coerce',downcast='integer')

## Restrict the Firm Sample by Sectors
# Eliminate the Firms in Financial Sector
TempInd_Finance     =   ( FirmSample['sic']>=6000 ) & (FirmSample['sic']<=6999)
# Utility Sector
TempInd_Utility     =   ( FirmSample['sic']>=4900 ) & (FirmSample['sic']<=4999)
# Quasi-government Sector
TempInd_QuasiGov    =   ( FirmSample['sic']>=9000 ) & (FirmSample['sic']<=9999)

TempInd_Drop        =   (TempInd_Finance)
FirmSample          =   FirmSample[~TempInd_Drop] \
                        .dropna(subset=['gvkey']).reset_index(drop=True)


### Historical Record of Firms

## Import FUNDQ
FirmRecord          =   pickle.load(open(DataFolder+"Compustat_FundQ.p","rb"))

## Merge with the Selected Firm Sample
Sample              =   FirmSample[['gvkey']] \
                        .merge(right=FirmRecord,how='left',left_on='gvkey',right_on='gvkey') \
                        .drop_duplicates()
                        
## Check the Record
# Report Format: whether indfmt is 'INDL' 
Sample['IndFmt'].value_counts(normalize=True)
# Cash Flow Statement Format: 7 is the right Cash Flow Statement format
Sample['SCFQ'].value_counts(normalize=True)
TempCheck_SCFQ      =   Sample.groupby('CalendarQtr')['SCFQ'].value_counts(normalize=True)
'''
Starting from 1988Q4, firms start adopting the new reporting standard. Between
1988Q4 and 2000Q1, the percentage of SCFQ=7 is around 95%. Since 2000, almost 
all the firms use SCFQ=7.
'''
# Replicates of gvkey and CalendarQtr
Sample.groupby(['gvkey','CalendarQtr']).apply(lambda x: x.shape[0]).value_counts(normalize=True)
TempCheck_UniqueID  =   Sample.groupby(['gvkey','CalendarQtr']).apply(lambda x: x.shape[0])


### Clean the Sample

## Drop the Obs. with Exchange outside of US
'''
Code	  Description	                     Exchange Country
0	      Subsidiary/Private	             Canada
0	      Subsidiary/Private	             United States
1	      Non-traded Company or Security	 Canada
1	      Non-traded Company or Security	 Germany
1	      Non-traded Company or Security	 Switzerland
1	      Non-traded Company or Security	 Taiwan
1	      Non-traded Company or Security	 United States
2	      Consolidated Parent or Tracking Stock Company	United States
3	      Leveraged Buyout	                 United States
4	      Additional Company Record-PreSFAS 94, ProForma, PreAmended	United States
7	      Toronto	                         Canada
8	      Montreal Stock Exchange	         Canada
9	      Canadian Venture Exchange	         Canada
10	      Alberta Stock Exchange	         Canada
11	      New York Stock Exchange	         United States
12	      American Stock Exchange	         United States
13	      OTC Bulletin Board	             United States
14	      NASDAQ-NMS Stock Market	         United States
15	      Boston Stock Exchange	             United States
16	      Midwest Exchange (Chicago)	     United States
17	      Pacific Exchange	                 United States
18	      Philadelphia Exchange	             United States
19	      Other-OTC	                         United States
20	      Unlisted Evaluated Equity	         United States
'''
TempInd_Drop        =   ( Sample['Exchange']==1 ) | \
                        ( Sample['Exchange']==7 ) | \
                        ( Sample['Exchange']==8 ) | \
                        ( Sample['Exchange']==9 ) | \
                        ( Sample['Exchange']==10 ) 
Sample              =   Sample[~TempInd_Drop].reset_index(drop=True)

## Drop the Obs. without the key Information
Sample              =   Sample.dropna(subset=['gvkey','CalendarQtr','FiscalQtr']) \
                        .sort_values(['gvkey','CalendarQtr']).reset_index(drop=True)

## Date Information: Calendar/Fiscal Quarter
for QtrVar in ['CalendarQtr','FiscalQtr']:
    Sample[QtrVar+'_Quarter']   =   Sample[QtrVar].map(lambda x: int(x[-1]))
    Sample[QtrVar+'_Year']      =   Sample[QtrVar].map(lambda x: int(x[0:4]))
    Sample[QtrVar+'_Date']      =   Sample[QtrVar].map(lambda x: datetime.date(int(x[0:4]),int(x[-1])*3-2,1))
    Sample[QtrVar+'_Qnum']      =   Sample[QtrVar].map(lambda x: int(x[0:4])*4+int(x[-1]))


### Clean the Flows: Accumulated Flow within the Fiscal Year into Quarterly Flows

## Sort the Data
Sample              =   Sample.sort_values(by=['gvkey','FiscalQtr_Qnum']) \
                        .reset_index(drop=True)
for QtrVar in ['CalendarQtr','FiscalQtr']:
    Sample[QtrVar+'_Gap']   =   Sample.groupby('gvkey')[QtrVar+'_Qnum'].diff()

## Decompose the Accumulated Flow into the Quarterly Flow
AccFlowVarList      =   ['StockIssuance','StockRepurchase','Dividend', \
                         'LongTermDebt_Issuance','LongTermDebt_Reduction','CurrentDebt_NetIssuance']
QtrFlowVarList      =   [x+'_'+'QFlow' for x in AccFlowVarList]
Sample[QtrFlowVarList] \
                    =   Sample.groupby(['gvkey','FiscalQtr_Year'])[AccFlowVarList].diff()

Sample.loc[Sample['FiscalQtr_Gap']>1,QtrFlowVarList] \
                    =   np.nan
TempInd_FQ1         =   Sample[Sample['FiscalQtr_Quarter']==1].index

for ii in range(len(AccFlowVarList)):
    Sample.loc[TempInd_FQ1,QtrFlowVarList[ii]] \
                        =  Sample.loc[TempInd_FQ1,AccFlowVarList[ii]]

Sample              =   Sample.drop(AccFlowVarList,axis=1) \
                        .rename(columns={QtrFlowVarList[ii]: AccFlowVarList[ii] \
                                         for ii in range(len(AccFlowVarList))})


### Clean the Flows: Generate the Flows of Interest
Sample['LongTermDebt_NetIssuance']  =   Sample['LongTermDebt_Issuance']- \
                                        Sample['LongTermDebt_Reduction']
Sample['DebtFinancing']             =   Sample['LongTermDebt_NetIssuance']+ \
                                        Sample['CurrentDebt_NetIssuance']
Sample['Equity_NetIssuance']        =   Sample['StockIssuance']- \
                                        Sample['StockRepurchase']
Sample['EquityFinancing']           =   Sample['StockIssuance']- \
                                        Sample['StockRepurchase']- \
                                        Sample['Dividend']                                        

### Aggregate Number and Total Sum of Repurchase and Dividend Payment
StockVarList        =   ['Asset']
FlowVarList         =   ['StockIssuance','StockRepurchase','Dividend', \
                         'Equity_NetIssuance','EquityFinancing', \
                         'LongTermDebt_Issuance','LongTermDebt_Reduction','CurrentDebt_NetIssuance', \
                         'LongTermDebt_NetIssuance','DebtFinancing']
AggVarList          =   StockVarList+FlowVarList
TempSample          =   Sample[['CalendarQtr_Date']+AggVarList].copy()

## Total Sum             
AggQrtStat          =   TempSample.groupby('CalendarQtr_Date')[AggVarList].sum()



### Final Clean of the Flows
DataFolder          =   "..\\temp\\"

## Quarterly PPI 
try:
    PPI_Q           =   pickle.load(open(DataFolder+'PPI_Q.p','rb'))
except:
    PPI_Q           =   pd.DataFrame(fred.get_series('PIEAMP01USQ661N'))
    PPI_Q.reset_index(inplace=True)
    PPI_Q['index']  =   pd.to_datetime(PPI_Q['index'])
    
    PPI_Q['QDate']  =   PPI_Q['index'].apply(lambda x: pd.datetime(x.year,x.quarter*3-2,1))
    PPI_Q.drop('index',axis=1,inplace=True)
    PPI_Q.set_index('QDate',inplace=True)
    PPI_Q.rename(columns={0: 'ppi'},inplace=True)
    PPI_Q           =   PPI_Q/100
    pickle.dump(PPI_Q,open(DataFolder+'PPI_Q.p','wb')) 

## Nominal to Real
AggQrtStat[AggVarList] \
                    =   AggQrtStat[AggVarList].divide(PPI_Q['ppi'],axis=0)

## Convert the Flow Variables: Quarterly Million Rate to Annual Billion Rate
AggQrtStat[FlowVarList] \
                    =   AggQrtStat[FlowVarList]/1000*4
## Convert the Stock Variables: Million to Billion
AggQrtStat[StockVarList] \
                    =   AggQrtStat[StockVarList]/1000
                    
                    
## Delete the Data before 1984Q1 since most of these data are 0 or missing
AggQrtStat          =   AggQrtStat[AggQrtStat.index>=datetime.date(1984,1,1)]
pickle.dump(AggQrtStat,open(DataFolder+"AggCompustat_Q.p","wb"))

# End of Section:
###############################################################################

