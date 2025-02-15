# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Sat Apr  6 10:06:15 2019
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


## Windows System Path
FolderList = [xx + "EquityMarkets_MonetaryPolicy\\Data\\Micro_data\\codes" \
              for xx in ["E:\\Dropbox (Bank of Canada)\\Research Projects\\", \
                         "B:\\Dropbox (Bank of Canada)\\Research Projects\\"] ]
for Folder in FolderList:
    if os.path.exists(Folder):
        os.chdir(Folder)    


# End of Section: Setup Working Directory
###############################################################################


#%% Construct the Link between SDC Deals and Compustat ID


### Original Samples 
 
## Read-in the SDC Sample
DataFolder      =   "..\\temp\\"
SDC             =   pickle.load(open(DataFolder+'SDC_IssuanceInfo.p','rb'))

## Read-in the List of Firms in Compustat
'''
Vintage
DataFolder      =   "..\\..\\..\\..\\..\\Data\\Compustat\\Quarterly\\"
CS              =   pickle.load(open(DataFolder+"Compustat_Names.p","rb"))
'''
DataFolder      =   "..\\..\\..\\..\\..\\Data\\Compustat\\Dataset\\"
## SECURITY File
SECURITY        =   pickle.load(open(DataFolder+"comp_security.p",'rb'))
# Preliminary Cleaning
'''
'excntry' and 'exchg' records the country and market where the stock is exchanged.
'''
SECURITY[['gvkey','excntry']] = SECURITY[['gvkey','excntry']].astype(str)
SECURITY['exchg'] = pd.to_numeric(SECURITY['exchg'],downcast='signed',errors='coerce')

SECURITY = SECURITY.dropna(subset=['gvkey']).reset_index(drop=True)

CS              =   SECURITY[['gvkey','cusip']].dropna().drop_duplicates() \
                    .reset_index(drop=True)

### Search in the WRDS by Matching the CUSIP
Link_SDC_CS     =   SDC[['IssueID','CUSIP','CUSIP_8digit']].reset_index(drop=True)

TempCounter     =   0
for ii in Link_SDC_CS.index:
    TempCusip               =   Link_SDC_CS.loc[ii,'CUSIP_8digit']
    TempSearchIndex         =   CS['cusip'].str.startswith(TempCusip)
    Temp_TargetNum          =   TempSearchIndex.sum()
    Link_SDC_CS.loc[ii,'LinkNum']   =   Temp_TargetNum
    if Temp_TargetNum==0:
        Link_SDC_CS.loc[ii,'gvkey']     =   'nan'
        Link_SDC_CS.loc[ii,'CUSIP_CS']  =   'nan'
    if Temp_TargetNum==1:
        TempCounter                     =   TempCounter+1
        Link_SDC_CS.loc[ii,'gvkey']     =   CS.loc[TempSearchIndex,'gvkey'].values[0]
        Link_SDC_CS.loc[ii,'CUSIP_CS']  =   CS.loc[TempSearchIndex,'cusip'].values[0]
    if Temp_TargetNum>1:
        TempCounter                     =   TempCounter+1
        Link_SDC_CS.loc[ii,'gvkey']     =   ','.join(CS.loc[TempSearchIndex,'gvkey'] \
                                                     .unique().tolist())
        Link_SDC_CS.loc[ii,'CUSIP_CS']  =   ','.join(CS.loc[TempSearchIndex,'cusip'] \
                                                     .unique().tolist())
    if np.mod(ii+1,1000)==0:
        print(str(ii+1)+' search done, with target rate '+ \
              str(np.round(TempCounter/(ii+1)*100,2))+'%')

## Save the Link File
DataFolder      =   "..\\temp\\"
pickle.dump(Link_SDC_CS,open(DataFolder+"Link_SDC_Compustat.p","wb"))

# End of Section:
###############################################################################

#%% Import and Clean the Compustat Quarterly Data 


### Read in Data
DS = pickle.load(open("..\\temp\\Sample_CS_Q.p","rb"))

### Conversion from Nominal to Real

## Download PPI
try:
    PPI = pickle.load(open('..\\temp\\PPI_Q.p','rb'))
except:
    fred = Fred(api_key='86cde3dec5dda5ffca44b58f01838b1e')
    PPI = fred.get_series('USAPPDMQINMEI')
    PPI = pd.DataFrame(PPI,columns={'ppi'})
    PPI['CalendarQtr'] = pd.DataFrame([str(YearDate.year)+'Q'+str(YearDate.quarter) \
                                      for YearDate in PPI.index],index=PPI.index)
    PPI.set_index('CalendarQtr',inplace=True)
    PPI['ppi'] = PPI['ppi']/100
    pickle.dump(PPI,open('..\\temp\\PPI_Q.p','wb'))

PPI = PPI.reset_index()

## Conversion
# Merge into the dataset
DS = DS.merge(right=PPI,on='CalendarQtr',how='left')
# Variable List for Conversion
VarList = ['Asset', 'Asset_Current_CashShortTermInvestment', 'Asset_Current', \
            'Liability', 'Liability_LongTermDebt', \
            'Liability_Current_Debt', 'Liability_Current', \
            'Equity', \
            'Income_Operating_BD', 'NetCashFlow_Operating', 'Sales', 'Depreciation', \
            'CapExp', 'RdExp', 'Acquisition', 'Cash_NetFlow',\
            'StockIssuance', 'StockRepurchase', 'Dividend',  \
            'LongTermDebt_Issuance', 'LongTermDebt_Reduction', \
            'CurrentDebt_NetIssuance','Expense_Interest_NetPaymentFlow', \
            'StockPrice_Close'] 

for vv in VarList:
    DS[vv] = DS[vv]/DS['ppi']
    
    
### Generate Variables of Interest

## Date
DS['Date'] = DS['CalendarQtr_Date']
## Demographics
# Age_year1: using year1 as the birth year
DS['Age_Q_year1'] = DS['FiscalQtr_Qnum']-(DS['year1']*4+1)
DS['Age_Y_year1'] = DS['FiscalQtr_Year']-DS['year1']
# Age_ipoyear: using ipodata.year as the birth year
DS['Age_Q_ipoyear'] = DS['CalendarQtr_Qnum']-(DS['ipodate'].dt.year*4+1)
DS['Age_Y_ipoyear'] = DS['CalendarQtr_Year']-DS['ipodate'].dt.year
# Age
DS['Age_Q'] = DS[['Age_Q_year1','Age_Q_ipoyear']].max(axis=1)
DS['Age_Y'] = DS[['Age_Y_year1','Age_Y_ipoyear']].max(axis=1)
# Birth Year
DS['BirthYear'] = DS['year1']

## Stocks
# Asset
DS['LogAsset'] = np.log(DS['Asset'])
DS['NonCashAsset'] = DS['Asset']-DS['Asset_Current_CashShortTermInvestment']
DS['Cash'] = DS['Asset_Current_CashShortTermInvestment']
# Liability
DS['Debt'] = DS['Liability_Current_Debt']+DS['Liability_LongTermDebt']
DS['NetDebt'] = DS['Debt']-DS['Asset_Current_CashShortTermInvestment']
# Equity Market Value
DS['EquityMV_Common'] = DS['CommonShares_Outstanding']*DS['StockPrice_Close']

## Flows
# Investment
print(str(np.round((pd.isna(DS['RdExp'])).mean()*100,2))+"% of the obs. have missing R&D Expenditure.\n")
DS.loc[pd.isna(DS['RdExp']),'RdExp'] = 0
DS['Investment'] = DS['CapExp']+DS['RdExp']
# Equity Financing
DS['EquityIssuance'] = DS['StockIssuance']
'''
McKeon (2013) cutoff: 3% of the equity market value.
'''
# TempInd = DS['StockIssuance']<0.03*DS['EquityMV_Common']
# DS.loc[TempInd,'EquityIssuance'] = 0
DS['EquityFinancing'] = DS['EquityIssuance']-DS['StockRepurchase']-DS['Dividend']
# Debt Financing
DS['DebtFinancing'] = DS['LongTermDebt_Issuance']-DS['LongTermDebt_Reduction'] \
                      +DS['CurrentDebt_NetIssuance'] \
                      -DS['Expense_Interest_NetPaymentFlow'] \
                      -DS['Cash_NetFlow']

DS['DebtFinancing_LongTermDebt'] = DS['LongTermDebt_Issuance']- \
                                   DS['LongTermDebt_Reduction']
# Total External Financing
DS['ExternalFinancing'] = DS['EquityFinancing']+DS['DebtFinancing']
# Operation Cash Flows
DS['OptCashFlow'] = DS['NetCashFlow_Operating']
# Sales
DS['LogSales'] = np.log(DS['Sales'])

## Operation on Lagged Variables
DS = DS.sort_values(['gvkey','CalendarQtr_Qnum']).reset_index()
DS['QtrGap'] = DS.groupby('gvkey')['CalendarQtr_Qnum'].diff(1)
LagVarList = ['Asset', 'Asset_PPE_TotalGross', 'Asset_PPE','NonCashAsset','Cash', \
              'NetDebt','Debt','LogAsset','LogSales']

# Taking Lag Values
for vv in LagVarList:
    DS['Lag_'+vv] = DS.groupby('gvkey')[vv].shift(1)
    # DS.loc[DS['QtrGap']>1,'Lag_'+vv] = np.nan
    DS['Diff_'+vv] = (DS[vv]-DS['Lag_'+vv])/DS['QtrGap']
    


## Normalized Stocks and Flows
# Size
DS['Kp'] = DS['Asset']
DS['K'] = DS['Lag_Asset']
# Leverage
DS['Leverage'] = DS['Debt']/DS['Kp']
DS['Leverage_Debt'] = DS['Debt']/DS['Kp']
DS['Leverage_LongTermDebt'] = DS['Liability_LongTermDebt']/DS['Kp']
DS['Leverage_TotalLiability'] = DS['Liability']/DS['Kp']
# Market to Book Ratio
DS['Equity_M2B'] = DS['EquityMV_Common']/DS['Equity']
# Current Asset Ratio
DS['CurrentAssetRatio'] = DS['Asset_Current']/DS['Asset']
# Normalized Investment and Financial Flows
DS['DiffAsset_K'] = (DS['Diff_Asset'])/DS['K'] 
DS['DiffAsset_PPE_K'] = (DS['Diff_Asset_PPE'])/DS['K'] 
DS['DiffAsset_PPE_TotalGross_K'] = (DS['Diff_Asset_PPE_TotalGross'])/DS['K'] 

DS['Inv_K'] = DS['Investment']/DS['K']
DS['Inv_CapExp_K'] = DS['CapExp']/DS['K']

DS['EFin_K'] = DS['EquityFinancing']/DS['K']
DS['EFin_Issuance_K'] = DS['EquityIssuance']/DS['K']
DS['EFin_Repurchase_K'] = DS['StockRepurchase']/DS['K']
DS['EFin_Dividend_K'] = DS['Dividend']/DS['K']

DS['DFin_K'] = DS['DebtFinancing']/DS['K']
DS['DFin_LongTerm_K'] = DS['DebtFinancing_LongTermDebt']/DS['K']
DS['DiffDebt_K'] = DS['Diff_Debt']/DS['K']

DS['ExternalFin_K'] = DS['ExternalFinancing']/DS['K']

'''
## Dependency Index: Individual Firms
# Setup
InvVar = 'Investment'
FinVarList = ['EquityFinancing','DebtFinancing','ExternalFinancing', \
              'OptCashFlow']
# Truncated Investment Flow
DS[InvVar+'_pos'] = DS[InvVar]
DS.loc[DS[InvVar]<=0,InvVar+'_pos'] = 0
# Dependency Index
for ff in FinVarList:
    DS['DepIdx_'+ff] = DS[ff]/DS[InvVar]
    TempInd = ( DS[ff]<=0 ) | ( DS[InvVar]<=0 )
    DS.loc[TempInd,'DepIdx_'+ff] = 0
'''

'''
### Sample Restriction

## Year: 1989-2017 (drop rate: 8%)
TempInd = (DS['CalendarQtr_Year']>=1989) & (DS['CalendarQtr_Year']<=2016)
print("Drop Obs. "+str(round((1-TempInd.mean())*100))+"%")
DS = DS.loc[TempInd,:]

## Merge and Acquisition Limit (drop rate: 3%)
MA_Ratio = DS['Acquisition']/DS['Asset']
TempInd = (pd.isna(MA_Ratio)) | (MA_Ratio<0.05)
print("Drop Obs. "+str(round((1-TempInd.mean())*100))+"%")
DS = DS.loc[TempInd,:]

## Drop the Super Small Firms (drop rate: 19% for $10 M, 8% for $1 M, 4% for $0 M)
TempInd = ( DS['Asset']>1 )
print("Drop Obs. "+str(round((1-TempInd.mean())*100))+"%")
DS = DS.loc[TempInd,:]
'''


### Size Quantiles
# DS = DS.dropna(subset=['K']).reset_index()
# DS['SizeQuant'] = DS.groupby('CalendarQtr_Qnum')['K'].rank(ascending=True,pct=True)

### Save the Sample 
DataFolder          =   "..\\temp\\"
pickle.dump(DS,open(DataFolder+"CompustatQ.p","wb"))
# End of Section:
###############################################################################



#%% Refine the Compustat Sample based its Link with SDC Deals


### Load in Data Sets
DataFolder      =   "..\\temp\\"
Link_SDC_CS     =   pickle.load(open(DataFolder+"Link_SDC_Compustat.p","rb"))
CS              =   pickle.load(open(DataFolder+"CompustatQ.p","rb"))


### Clean the Link File
print("The Distribution (by %) of Linked Number is\n")
print(np.round(Link_SDC_CS['LinkNum'].value_counts(normalize=True).sort_index()*100,decimals=2))
Link_SDC_CS     =   Link_SDC_CS[Link_SDC_CS['LinkNum']==1]
Link_SDC_CS     =   Link_SDC_CS[['IssueID','gvkey']].reset_index(drop=True)


### Clean the Compustat Quarterly Data

## Temporary Function to Winsorize Variables
def TempFun_Winsorize(InputS,LowQ,HighQ):
    S       =   InputS.copy()
    LowS    =   S.quantile(LowQ)
    HighS   =   S.quantile(HighQ)
    S[ (S<LowS) | (S>HighS) ]   =   np.nan
    return S

## Summary Statistics before Winsorization
SumStat_1       =   CS.describe(percentiles=[0.005,0.01,0.1,0.25,0.5,0.75,0.9,0.99,0.995])
SumStat_1.loc['count',:] \
                =   SumStat_1.loc['count',:]/CS.shape[0]

## Winsorize the Variables
# Variables with Clear Boundary
CS.loc[CS['EquityMV_Common']<=0,'EquityMV_Common'] \
                =   np.nan
CS.loc[CS['CommonShares_Outstanding']<=0,'CommonShares_Outstanding'] \
                =   np.nan
CS.loc[CS['CurrentAssetRatio']<0,'CurrentAssetRatio'] \
                =   np.nan
CS.loc[CS['CurrentAssetRatio']>1,'CurrentAssetRatio'] \
                =   np.nan
# Variables to be Winsorized by Extreme Quantiles
VarList         =   ['Leverage','Diff_LogSales','Diff_LogAsset']

for Var in VarList:
    CS[Var]         =   TempFun_Winsorize(CS[Var],0.005,0.995)

## Summary Statistics after Winsorization
SumStat_2       =   CS.describe(percentiles=[0.005,0.01,0.1,0.25,0.5,0.75,0.9,0.99,0.995])
SumStat_2.loc['count',:] \
                =   SumStat_2.loc['count',:]/CS.shape[0]

## Generate the Quantile Category
QuantBin        =   [-0.01,0.25,0.75,1.01]  
# Variable List
TempVarList     =   ['Lag_Asset','Diff_LogSales','Diff_LogAsset','Equity_M2B']
# Generate the Quantile Categories
for TempVar in TempVarList:
    CS[TempVar+'_Quant'] \
                    =   CS[~pd.isna(CS[TempVar])] \
                        .groupby('CalendarQtr')[TempVar].rank(ascending=True,pct=True)
    CS[TempVar+'_Type'] \
                =   pd.cut(CS[TempVar+'_Quant'],bins=QuantBin,labels=range(1,len(QuantBin)))

# Generate the Quantile Category Dummy Variables
for Var in TempVarList:
    CS[Var+'_UppQuant']     =   0
    CS.loc[CS[Var+'_Type']==len(QuantBin)-1,Var+'_UppQuant'] \
                            =   1
    CS[Var+'_LowQuant']     =   0
    CS.loc[CS[Var+'_Type']==1,Var+'_LowQuant'] \
                            =   1
### Merge the Sample

## Records
SDC_CS          =   Link_SDC_CS.merge(right=CS,how='left',on='gvkey')

pickle.dump(SDC_CS,open(DataFolder+"SDC_CompustatQ.p","wb"))

## Firm Characteristics
SDC_CS_FirmInfo =   SDC_CS[['IssueID','gvkey','sic','naics', 'year1', 'year2','ipodate', \
                            'FF10_Code','FF10_Name','FF5_Code','FF5_Name']] \
                    .drop_duplicates(['IssueID'])
pickle.dump(SDC_CS_FirmInfo,open(DataFolder+"SDC_CompustatQ_FirmInfo.p","wb"))
# End of Section：
###############################################################################
