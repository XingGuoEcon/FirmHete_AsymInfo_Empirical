# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Sat May 11 09:53:59 2019
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


#%% Generating Raw Data


### Read-in 
DataFolder          =   "..\\..\\Micro_data\\datasets\\SDC\\Download_20190424\\"
DataFile            =   "Download_20190424.xls"

## SDC Data
TypeDict            =   {'CUSIP': str, '9-Digit\nCUSIP': str, \
                         'Immediate\nParent\nCUSIP': str, \
                         'Ulti-\nmate\nParent\nCUSIP': str, \
                         'Main\nSIC\nCode': str, \
                         'Ticker\nSymbol': str, \
                         }
Sample              =   pd.read_excel(open(DataFolder+DataFile,'rb'), \
                                      dtype=TypeDict)


### Clean Data

## Restrict the Sample and Rename the Variables
VarList             =   Sample.columns.tolist()
ReNameDict          =   {'Filing\nDate': 'FilingDate', \
                         'Issue\nDate': 'IssueDate', \
                         'Issuer': 'Issuer', \
                         'Main\nSIC\nCode': 'SIC', \
                         'Nation': 'Nation', \
                         'Ticker\nSymbol': 'TickerSymbol', \
                         "Primary\nExchange\nWhere\nIssuer's\nStock\nTrades": 'Exchange', \
                         'Principal\nAmount\n($ mil)': 'PrincipalAmount_ThisMarket', \
                         'Principal \nAmt - sum \nof all Mkts \n($ mil)': 'PrincipalAmount_AllMarket', \
                         'Proceeds\nAmt - in \nthis Mkt\n($ mil)': 'ProceedsAmount_ThisMarket',
                         'Proceeds \nAmt - sum \nof all Mkts\n($ mil)': 'ProceedsAmount_AllMarket', \
                         'Type\nof\nSecurity': 'SecurityType', \
                         'Cur-\nrency': 'Currency', \
                         'Shares \nFiled - \nin this Mkt': 'FiledShares_ThisMarket', \
                         'Shares \nFiled - \nsum of \nall Mkts': 'FiledShares_AllMarket', \
                         'Amt Filed - \nin this Mkt \n($ mil)': 'FiledAmount_ThisMarket', \
                         'Total Dollar\nAmount Filed': 'FiledAmount_AllMarket', \
                         'IPO\nFlag\n(Y/N)': 'IPO_Flag', \
                         'Total\nShares\nOffered\nIn This\nMarket': 'OfferedTotalShares_ThisMarket', \
                         'Primary \nShares \nOffered \n- in \nthis Mkt': 'OfferedPrimaryShares_ThisMarket', \
                         'Secondary \nShs Ofrd - \nin this Mkt': 'OfferedSecondaryShares_ThisMarket', \
                         'Shares \nOffered - \nsum of \nall Mkts': 'OfferedTotalShares_AllMarket', \
                         'CUSIP': 'CUSIP', \
                         '9-Digit\nCUSIP': 'CUSIP_9digit', \
                         'Immediate\nParent\nCUSIP': 'CUSIP_ImParent', \
                         'Ulti-\nmate\nParent\nCUSIP': 'CUSIP_UlParent', \
                         'Total\nAssets\nAfter\nthe\nOffering\n($ mil)': 'TotalAsset_AfterOffering', \
                         'Total\nAssets\nBefore\nthe\nOffering\n($ mil)': 'TotalAsset_BeforeOffering', \
                         'Total\nDebt\n($ mil)': 'TotalDebt', \
                         'Total\nEquity\n($ mil)': 'TotalEquity', \
                         'Market Value/\nMarket\nCapitalization': 'MarketValue_MarketCap', \
                         'Total\nCapital-\nization\n($ mil)': 'MarketCap', \
                         'Market\nValue\nBefore\nOffer\n($ mil)': 'MarketValue_BeforeOffering', \
                         'Shares\nOutstanding\nBefore\nOffering': 'TotalShares_BeforeOffering', \
                         'Shares\nOutstanding\nAfter\nthe\nOffering': 'TotalShares_AfterOffering', \
                         '% Of\nInsider\nShares\nBefore\nOffer': 'InsiderSharesPct_BeforeOffering', \
                         'Prim Shs as \n% of Shs Out\nBef Ofr - \nsum of \nall Mkts': 'PrimarySharesPct_BeforeOffering', \
                         'Prim Shs as \n% of Shs Out\nAft Ofr - sum\nof all Mkts': 'PrimarySharesPct_AfterOffering', \
                         'Prim Shs \nas % of Shs\nOfrd - sum \nof all Mkts': 'OfferedPrimarySharesPct', \
                         'Type\nof\nShares': 'ShareType', \
                         'Event\nHistory\nDate': 'EventHistoryDate', \
                         'Event\nHistory\nCode': 'EventHistoryCode', \
                         'Dates: Launch Date': 'LaunchDate', \
                         'Issue\nType': 'IssueType', \
                         'Issue\nType\nDescription': 'IssueTypeDescription', \
                         'Days In\nRegistration': 'DaysInRegistration', \
                         'Offering\nTechnique': 'OfferingTechnique', \
                         'Offering Technique\nDescription': 'OfferingTechniqueDescription', \
                         'Rights\nOffer\nFlag\n(Y/N)': 'RightsOfferFlag', \
                         'Rule\n415\nShelf': 'Rule415ShelfFlag', \
                         'Shelf Type': 'ShelfType', \
                         'Transaction\nType': 'TransactionType', \
                         'Use of Proceeds': 'ProceedsUse', \
                         }
Sample              =   Sample[list(ReNameDict.keys())].rename(columns=ReNameDict)

## Date-Time Variables
for DateVar in ['IssueDate','FilingDate','LaunchDate']:
    Sample[DateVar]             =   pd.to_datetime(Sample[DateVar])
    Sample[DateVar+'Flag']      =   ~pd.isna(Sample[DateVar])
    TempInd                     =   ~pd.isna(Sample[DateVar])
    Sample.loc[TempInd,DateVar+'_Year'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,1,1))
    Sample.loc[TempInd,DateVar+'_Quarter'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,x.quarter*3-2,1))
    Sample.loc[TempInd,DateVar+'_Month'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,x.month,1))
                                    
    Sample[DateVar]             =   pd.to_datetime(Sample[DateVar]).map(lambda x: x.date())
    Sample[DateVar+'_Year']     =   pd.to_datetime(Sample[DateVar+'_Year']).map(lambda x: x.date())
    Sample[DateVar+'_Quarter']  =   pd.to_datetime(Sample[DateVar+'_Quarter']).map(lambda x: x.date())
    Sample[DateVar+'_Month']    =   pd.to_datetime(Sample[DateVar+'_Month']).map(lambda x: x.date())
    

## Only Keep the Issuance within US Markets and by US Firms
# Check Currency: 'US'
Sample['Currency'].value_counts(normalize=True)
Sample              =   Sample[Sample['Currency']=='US']
# Check Nation: 'United States'
Sample['Nation'].value_counts(normalize=True)
# Check Exchange: 'Nasdaq', 'New York', ‘OTC'
Sample['Exchange'].value_counts(normalize=True)
Sample              =   Sample[ (Sample['Exchange']=='Nasdaq') | \
                                (Sample['Exchange']=='New York') | \
                                (Sample['Exchange']=='American') | \
                                (Sample['Exchange']=='OTC')]

## Only Keep the Issuance of Common or Ordinary Shares
Sample['SecurityType'].value_counts(normalize=True)
#KeepTypeList        =   ['Common Shares','Ord/Common Shs.']
#Sample              =   Sample[Sample['SecurityType'].isin(KeepTypeList)]

Sample              =   Sample.reset_index(drop=True)
## Drop the Financial and Utility Firms
Sample['SIC']       =   Sample['SIC'].apply(pd.to_numeric,errors='coerce',downcast='signed')
# Financial Sector
TempInd_Finance     =   ( Sample['SIC']>=6000 ) & ( Sample['SIC']<=6999)
# Utility Sector
TempInd_Utility     =   ( Sample['SIC']>=4900 ) & ( Sample['SIC']<=4999)
# Quasi-government Sector
TempInd_QuasiGov    =   ( Sample['SIC']>=9000 ) & ( Sample['SIC']<=9999)

TempInd_Drop        =   (TempInd_Finance)
Sample              =   Sample[~TempInd_Drop]

# Save the Number and Total Proceeds of IPO and SEO Deals-Selected SIC Group
AggIpoSeo           =   Sample.groupby(['IssueDate_Quarter','IPO_Flag']) \
                        ['ProceedsAmount_AllMarket'].agg(['count','sum']) \
                        .rename(columns={'count': 'Num','sum': 'Sum'}) \
                        .rename(index={'Yes': 'Ipo','No': 'Seo'},level=1) \
                        .unstack(level=1)
AggIpoSeo.columns   =   [x[1]+x[0] for x in AggIpoSeo.columns]

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
AggIpoSeo[['IpoSum','SeoSum']] \
                    =   AggIpoSeo[['IpoSum','SeoSum']].divide(PPI_Q['ppi'],axis=0)

## Quarterly Million Rate to Annual Billion Rate
AggIpoSeo[['IpoSum','SeoSum']] \
                    =   AggIpoSeo[['IpoSum','SeoSum']]/1000*4
                    

pickle.dump(AggIpoSeo,open(DataFolder+'AggIpoSeo_Q.p','wb'))

# End of Section: 
###############################################################################
