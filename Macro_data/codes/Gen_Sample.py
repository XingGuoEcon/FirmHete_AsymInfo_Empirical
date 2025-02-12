# -*- coding: utf-8 -*-
"""
Code Introduction:
    This codes collect the data from 
        1. FRB Z1 table 
        2. Gross Issuance from Baker and Wurgler (2000)
        3. Details of equity issuance underlying the FRB Z1 aggregate flow
        4. NIPA time-series for Industrial Production, GDP, Investment
    and assemble these data into different data files. 
    
    There are main sections in this code:
        1. Data Collection
            - Download PPI, NIPA Flows
            - Extract Flow of Fund flows from the downloaded database
            - Detailed flows underlying the aggregate equity financing flow
            - Detailed time-sereis of IPO and SEO numbers
        2. Processing the Quarterly Data
            - Merge the quarterly FoF flows and Balance Sheet information
            - Merge the detailed quarterly flows into the data set
            - Clean the merged sample and generate the derived variables
        3. Processing the Monthly Data
        
Version History:
    Created: Thu Nov 30 12:47:27 2017
    Current: Thu Apr 25          2019

@author: Xing Guo (xingguo@umich.edu)

"""
#%% Import Modules
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
## XML Parse Tool
import xml.etree.ElementTree as ET
## Scientific Python
import scipy.signal as signal
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



#%% Data Processing: Quarterly Financing Flow Data

### Setup
DataFolder      =   '..\\temp\\'

dataset_FoF     =   pickle.load(open(DataFolder+'dataset_FoF.p','rb'))
EFinDetail_Q    =   pickle.load(open(DataFolder+'EFinDetail_Q.p','rb'))
GrossIss_Q      =   pickle.load(open(DataFolder+'GrossIss_Q.p','rb'))
NIPA_Q          =   pickle.load(open(DataFolder+'NIPA_Q.p','rb'))
IpoSeo_Q        =   pickle.load(open(DataFolder+'IpoSeo_Q.p','rb'))
AggIpoSeo_Q     =   pickle.load(open(DataFolder+'AggIpoSeo_Q.p','rb'))
AggCompustat_Q  =   pickle.load(open(DataFolder+'AggCompustat_Q.p','rb'))
### Quarterly flow data from FoF

## Equity Financing
EFin                        =   pd.concat([dataset_FoF['FA106121075.Q'], \
                                           dataset_FoF['FA103164103.Q'], \
                                           dataset_FoF['FA112090205.Q']],\
                                          axis=1,keys=['DivPayment_Cor', \
                                                       'EquityNetIssue_Cor', \
                                                       'EquityNetIssue_NonCor'])
EFin['EquityFin_Cor']       =   EFin['EquityNetIssue_Cor']-EFin['DivPayment_Cor']
EFin['EquityFin_NonCor']    =   EFin['EquityNetIssue_NonCor']
EFin['EquityNetIssue_Agg']  =   EFin['EquityNetIssue_Cor']+ \
                                EFin['EquityNetIssue_NonCor']
EFin['EquityFin_Agg']       =   EFin['EquityFin_Cor']+EFin['EquityFin_NonCor']

## Debt Financing
DFin                        =   pd.concat([dataset_FoF['FA104122005.Q'], \
                                           dataset_FoF['FA104123005.Q'], \
                                           dataset_FoF['FA114123005.Q']], \
                                          axis=1,keys=['DebtSecurity_Cor', \
                                                       'Loan_Cor', \
                                                       'Loan_NonCor'])
DFin['DebtFin_Cor']         =   DFin['DebtSecurity_Cor']+DFin['Loan_Cor']
DFin['DebtFin_NonCor']      =   DFin['Loan_Cor']

DFin['DebtFin_Agg']         =   DFin['DebtFin_Cor']+DFin['DebtFin_NonCor']

## Liquidity Accumulation
LiqAcc                      =   pd.concat([dataset_FoF['FA103020005.Q'], \
                                           dataset_FoF['FA103030003.Q'], \
                                           dataset_FoF['FA113020005.Q'], \
                                           dataset_FoF['FA113030003.Q']], \
                                          axis=1,keys=['Cash_Cor', \
                                                       'Deposites_Cor', \
                                                       'Cash_NonCor', \
                                                       'Deposites_NonCor'])

LiqAcc['LiqAcc_Cor']        =   LiqAcc['Cash_Cor']+LiqAcc['Deposites_Cor']
LiqAcc['LiqAcc_NonCor']     =   LiqAcc['Cash_NonCor']+LiqAcc['Deposites_NonCor']

LiqAcc['LiqAcc_Agg']        =   LiqAcc['LiqAcc_Cor']+LiqAcc['LiqAcc_NonCor']

## Value Added by Non-financial business
ValAdd                      =   pd.concat([dataset_FoF['FA106902501.Q'], \
                                           dataset_FoF['FA116902505.Q'], \
                                           dataset_FoF['FA106902605.Q'], \
                                           dataset_FoF['FA116902605.Q']], \
                                          axis=1,keys=['GrossValAdd_Cor', \
                                                       'GrossValAdd_NonCor', \
                                                       'NetValAdd_Cor', \
                                                       'NetValAdd_NonCor'])
ValAdd['GrossValAdd_Agg']   =   ValAdd['GrossValAdd_Cor']+ \
                                ValAdd['GrossValAdd_NonCor']
ValAdd['NetValAdd_Agg']     =   ValAdd['NetValAdd_Cor']+ \
                                ValAdd['NetValAdd_NonCor']
## Other Flow
OtherFlow       =   pd.concat([dataset_FoF['FA106000105.Q'], \
                               dataset_FoF['FA116000105.Q'], \
                               dataset_FoF['FA104090005.Q'], \
                               dataset_FoF['FA114090005.Q'], \
                               dataset_FoF['FA105050005.Q'], \
                               dataset_FoF['FA115050005.Q'], \
                               dataset_FoF['FA106060005.Q']], \
                              axis=1,keys=['GrossSaving_Cor', \
                                           'GrossSaving_NonCor', \
                                           'FinAssetAcquisition_Cor', \
                                           'FinAssetAcquisition_NonCor', \
                                           'CapExp_Cor', \
                                           'CapExp_NonCor', \
                                           'Profit_Cor'])
## Transform FoF Quarterly Flow Data from Million-AnnualRate to Billion-AnnualRate

EFin            =   EFin/1000
DFin            =   DFin/1000
ValAdd          =   ValAdd/1000
LiqAcc          =   LiqAcc/1000
OtherFlow       =   OtherFlow/1000

## Merge the different Flows from FoF
FoF_Q_Flow      =   pd.concat([EFin,DFin,LiqAcc,ValAdd,OtherFlow],axis=1)


### Quarterly Balance Sheet Snapshot Information

## Total Asset and Liability
FoF_Q_BalanceSheet          =   pd.concat([dataset_FoF['FL102000005.Q'], \
                                           dataset_FoF['FL112000005.Q'], \
                                           dataset_FoF['FL104190005.Q'], \
                                           dataset_FoF['FL114190005.Q']], \
                                          axis=1,keys=['TotalAsset_Cor', \
                                                       'TotalAsset_NonCor', \
                                                       'Liability_Cor', \
                                                       'Liability_NonCor'])
FoF_Q_BalanceSheet['TotalAsset_Agg'] \
                            =   FoF_Q_BalanceSheet['TotalAsset_Cor']+ \
                                FoF_Q_BalanceSheet['TotalAsset_NonCor']
FoF_Q_BalanceSheet['Liability_Agg'] \
                            =   FoF_Q_BalanceSheet['Liability_Cor']+ \
                                FoF_Q_BalanceSheet['Liability_NonCor']
                                
## Transform from Million to Billion
FoF_Q_BalanceSheet          =   FoF_Q_BalanceSheet/1000


### Merge the Quarterly Flow and Balance Sheet Datasets

## Generate the Sample
# Equity Financing Details
temp_1          =   EFinDetail_Q.drop('EquityNetIssue_Cor',axis=1)
# Equity Gross Issuance of Corporate Sector
temp_2          =   GrossIss_Q.rename(columns={'Equity':'EquityGrossIssue_Cor', \
                                               'Debt':'DebtGrossIssue_Cor', \
                                               'EShare': 'EShare_Cor'})
# IPO and SEO Number
temp_3          =   IpoSeo_Q.rename(columns={'IPO': 'IpoNum_Cor', \
                                             'SEO': 'SeoNum_Cor'})
# Aggregated IPO and SEO Number and Total Sum from SDC
temp_4          =   AggIpoSeo_Q.rename(columns={'IpoNum': 'AggIpoNum_Cor', \
                                                'SeoNum': 'AggSeoNum_Cor', \
                                                'IpoSum': 'AggIpoSum_Cor', \
                                                'SeoSum': 'AggSeoSum_Cor'})
# Aggregated Repurchase and Dividend
temp_5          =   AggCompustat_Q[['StockRepurchase','Dividend']].copy() \
                    .rename(columns={'StockRepurchase': 'AggRepurchaseSum_Cor', \
                                     'Dividend': 'AggDivPaymentSum_Cor'})
# Merge the Datasets
Sample_Q        =   pd.concat([FoF_Q_Flow,FoF_Q_BalanceSheet, \
                               temp_1,temp_2,temp_3,temp_4,temp_5, \
                               NIPA_Q],axis=1)


### Clean the Sample

## Generate the Variables Tracking the Budget Constraint
Sample_Q['OperateFlow_Cor'] =   Sample_Q['GrossSaving_Cor']+ \
                                Sample_Q['DivPayment_Cor']
Sample_Q['OperateFlow_NonCor']= Sample_Q['GrossSaving_NonCor']
Sample_Q['OperateFlow_Agg'] =   Sample_Q['OperateFlow_Cor']+ \
                                Sample_Q['OperateFlow_NonCor']

Sample_Q['Inv_Cor']         =   Sample_Q['CapExp_Cor']
Sample_Q['Inv_NonCor']      =   Sample_Q['CapExp_NonCor']
Sample_Q['Inv_Agg']         =   Sample_Q['Inv_Cor']+Sample_Q['Inv_NonCor']

Sample_Q['FinAssetAcquisition_Agg'] \
                            =   Sample_Q['FinAssetAcquisition_Cor']+ \
                                Sample_Q['FinAssetAcquisition_NonCor']

Sample_Q['ExternalFin_Cor'] =   Sample_Q['EquityFin_Cor']+Sample_Q['DebtFin_Cor']
Sample_Q['ExternalFin_NonCor'] \
                            =   Sample_Q['EquityFin_NonCor']+Sample_Q['DebtFin_NonCor']
Sample_Q['ExternalFin_Agg'] =   Sample_Q['EquityFin_Agg']+Sample_Q['DebtFin_Agg']

Sample_Q['TotalGrossIssue_Cor'] \
                            =   Sample_Q['EquityGrossIssue_Cor']+ \
                                Sample_Q['DebtGrossIssue_Cor']

for FinVar in ['DebtFin','ExternalFin']:
    for SecVar in ['Cor','NonCor','Agg']:
        Sample_Q[FinVar+'NetLiqAcc'+'_'+SecVar] \
                            =   Sample_Q[FinVar+'_'+SecVar]- \
                                Sample_Q['LiqAcc'+'_'+SecVar]
                                
## Generate the Normalized Variables
# The Lagged Variables as Denumerator: Total Asset
for LagVar in ['TotalAsset']:
    for SecVar in ['Cor','NonCor','Agg']:
        TempVar     =   LagVar+'_'+SecVar
        Sample_Q['Lag'+TempVar] \
                    =   Sample_Q[TempVar].shift(1)
# The Trend and Deviation of Some Variables
for TrVar in ['TotalAsset']:
    for SecVar in ['Cor','NonCor','Agg']:
        TempVar     =   TrVar+'_'+SecVar
        Temp        =   np.log(Sample_Q[TempVar])
        Temp.dropna(inplace=True)
        Temp        =   pd.concat(list(sm.tsa.filters.hpfilter(Temp,lamb=1600)), \
                                  axis=1, \
                                  keys=['LogDev_'+TempVar,'LogTrend_'+TempVar])
        Temp['Trend_'+TempVar] \
                    =   np.exp(Temp['LogTrend_'+TempVar])
        Sample_Q    =   Sample_Q.merge(Temp,how='outer', \
                                       left_index=True,right_index=True)
for TrVar in ['EquityGrossIssue','DebtGrossIssue','TotalGrossIssue']:
    for SecVar in ['Cor']:
        TempVar     =   TrVar+'_'+SecVar
        Temp        =   np.log(Sample_Q[TempVar])
        Temp.dropna(inplace=True)
        Temp        =   pd.concat(list(sm.tsa.filters.hpfilter(Temp,lamb=1600)), \
                                  axis=1, \
                                  keys=['LogDev_'+TempVar,'LogTrend_'+TempVar])
        Temp['Trend_'+TempVar] \
                    =   np.exp(Temp['LogTrend_'+TempVar])
        Sample_Q    =   Sample_Q.merge(Temp,how='outer', \
                                       left_index=True,right_index=True)    
# The Normalized Variables with Sector-wise Aggregate as Normalizer
        
FlowVarList_Cor =   ['EquityIssue','EquityIssuePublic','EquityIssuePrivate', \
                     'EquityIssueIPO','EquityIssueSEO', \
                     'EquityNetIssueExMA', \
                     'EquityRetire','EquityRepurchase','EquityMA', \
                     'DivPayment','DebtSecurity', \
                     'EquityGrossIssue','DebtGrossIssue','TotalGrossIssue', \
                     'Profit', \
                     'AggIpoSum','AggSeoSum','AggRepurchaseSum','AggDivPaymentSum']
FlowVarList_Agg =   ['OperateFlow','Inv','FinAssetAcquisition', \
                     'EquityNetIssue','EquityFin','DebtFin','ExternalFin', \
                     'LiqAcc','DebtFinNetLiqAcc','ExternalFinNetLiqAcc']
for NormVar in ['LagTotalAsset', \
                'Trend_TotalAsset','TotalAsset','GrossValAdd','Inv']:
    # Only for Corporate Sector
    for FlowVar in FlowVarList_Cor:
        Sample_Q[FlowVar+'_'+NormVar+'_Cor']  = \
                Sample_Q[FlowVar+'_Cor']/Sample_Q[NormVar+'_Cor']
    # For all Sectors
    for FlowVar in FlowVarList_Agg:
        for SecVar in ['Cor','NonCor','Agg']:
            Sample_Q[FlowVar+'_'+NormVar+'_'+SecVar]  = \
                Sample_Q[FlowVar+'_'+SecVar]/Sample_Q[NormVar+'_'+SecVar]
# The Normalized Variables with Aggregate-Level Aggregate as Normalizer
for NormVar in ['LagTotalAsset', \
                'Trend_TotalAsset','TotalAsset','GrossValAdd']:
    # Only for Corporate Sector
    for FlowVar in FlowVarList_Cor:
        Sample_Q[FlowVar+'_Agg'+NormVar+'_Cor']  = \
                Sample_Q[FlowVar+'_Cor']/Sample_Q[NormVar+'_Agg']
    # For all Sectors
    for FlowVar in FlowVarList_Agg:
        for SecVar in ['Cor','NonCor','Agg']:
            Sample_Q[FlowVar+'_Agg'+NormVar+'_'+SecVar]  = \
                Sample_Q[FlowVar+'_'+SecVar]/Sample_Q[NormVar+'_Agg']
# The Normalized Variables with NIPA Flow Aggregate as Normalizer
for NormVar in ['GDP']:
    # Only for Corporate Sector
    for FlowVar in FlowVarList_Cor:
        Sample_Q[FlowVar+'_'+NormVar+'_Cor']  = \
                Sample_Q[FlowVar+'_Cor']/Sample_Q[NormVar]
    # For all Sectors
    for FlowVar in FlowVarList_Agg:
        for SecVar in ['Cor','NonCor','Agg']:
            Sample_Q[FlowVar+'_'+NormVar+'_'+SecVar]  = \
                Sample_Q[FlowVar+'_'+SecVar]/Sample_Q[NormVar]


### Save the Merged Data Set               
Sample_Q        =   Sample_Q[Sample_Q.index>=datetime.datetime(1960,1,1)]
pickle.dump(Sample_Q,open(DataFolder+'Sample_Q.p','wb')) 
# END OF SECTION: 
###############################################################################

#%% Quarterly Financing Flows: Compustat Sample

DataFolder      =   '..\\temp\\'

## Read in the data sets
DS_Compustat    =   pickle.load(open(DataFolder+"AggCompustat_Q.p",'rb'))
DS_IpoSeo       =   pickle.load(open(DataFolder+"AggIpoSeo_Q.p",'rb'))

## Merge into the Quarterly Sample
Sample_CS_Q     =   DS_Compustat.merge(right=DS_IpoSeo,how='outer', \
                                       left_index=True,right_index=True) \
                    .rename(columns={'IpoSum': 'EquityIssuance_Ipo', \
                                     'SeoSum': 'EquityIssuance_Seo'}) \
                    .sort_index()

## Generate the Variables of Interest
Sample_CS_Q['EquityIssuance_IpoSeo'] \
                =   Sample_CS_Q['EquityIssuance_Ipo']+Sample_CS_Q['EquityIssuance_Seo']

## Normalize the Flows by Lagged Total Asset
Sample_CS_Q['LagTotalAsset'] \
                =   Sample_CS_Q['Asset'].shift()
FlowVarList     =   ['StockIssuance', 'StockRepurchase', 'Dividend',
                     'Equity_NetIssuance', 'EquityFinancing', 'LongTermDebt_Issuance',
                     'LongTermDebt_Reduction', 'CurrentDebt_NetIssuance',
                     'LongTermDebt_NetIssuance', 'DebtFinancing', \
                     'EquityIssuance_Ipo', 'EquityIssuance_Seo', 'EquityIssuance_IpoSeo']
for FlowVar in FlowVarList:
    Sample_CS_Q[FlowVar+'_'+'LagTotalAsset'] \
                    =   Sample_CS_Q[FlowVar]/Sample_CS_Q['LagTotalAsset']

### Save the Merged Data Set               
Sample_CS_Q     =   Sample_CS_Q[Sample_CS_Q.index>=datetime.datetime(1984,1,1)]
pickle.dump(Sample_CS_Q,open(DataFolder+'Sample_CS_Q.p','wb'))
# End of Section:
###############################################################################

#%% Data Processing: Monthly Financial Flows


### Setup
DataFolder      =   '..\\temp\\'

Sample_Q        =   pickle.load(open(DataFolder+'Sample_Q.p','rb'))
EFinDetail_M    =   pickle.load(open(DataFolder+'EFinDetail_M.p','rb'))
GrossIss_M      =   pickle.load(open(DataFolder+'GrossIss_M.p','rb'))


### Monthly Gross Issuance

## Priliminary Cleaning
GrossIss_M              =   GrossIss_M[['Equity','Debt','EShare']].dropna()
GrossIss_M              =   GrossIss_M[GrossIss_M.index>=datetime.datetime(1960,1,1)]

## Normalize the Monthly Gross Issuance 
# Merge the lag book value asset into the flow dataset
GrossIss_M['QDate']     =   GrossIss_M.index.map(lambda x: \
                                datetime.datetime(x.year,int(np.ceil(x.month/3))*3-2,1))
GrossIss_M              =   GrossIss_M.merge(right=Sample_Q[['LagTotalAsset_Cor', \
                                                             'GDP', \
                                                             'GrossValAdd_Agg', \
                                                             'GrossValAdd_Cor']], \
                                             how='left', \
                                             left_on='QDate',right_index=True)
for FlowVar in ['Equity','Debt']:
    # by the Book Value Asset in the Last Quarter
    GrossIss_M[FlowVar+'_LagTotalAsset_Cor'] \
                =   GrossIss_M[FlowVar]/GrossIss_M['LagTotalAsset_Cor']
    # by its own HP Trend
    Temp        =   GrossIss_M[FlowVar]
    Temp.dropna(inplace=True)
    Temp        =   pd.concat(list(sm.tsa.filters.hpfilter(Temp,lamb=1600*3**4)), \
                              axis=1, \
                              keys=['LogDev_'+FlowVar,'LogTrend_'+FlowVar])
    Temp['Trend_'+FlowVar] \
                =   np.exp(Temp['LogTrend_'+FlowVar])
    GrossIss_M  =   GrossIss_M.merge(Temp,how='outer', \
                                     left_index=True,right_index=True)
    # by the NIPA-GDP in the Current Quarter
    GrossIss_M[FlowVar+'_GDP'] \
                =   GrossIss_M[FlowVar]/GrossIss_M['GDP']
    # by the Aggregate Gross Value Added in the Current Quarter
    GrossIss_M[FlowVar+'_GrossValAdd_Agg'] \
                =   GrossIss_M[FlowVar]/GrossIss_M['GrossValAdd_Agg']
    # by the Corporate Sector Gross Value Added in the Current Quarter
    GrossIss_M[FlowVar+'_GrossValAdd_Cor'] \
                =   GrossIss_M[FlowVar]/GrossIss_M['GrossValAdd_Cor']
    
GrossIss_M.drop('QDate',axis=1,inplace=True)


### Monthly  Equity Financing Flows Details

## Priliminary Cleaning
EFinDetail_M            =   EFinDetail_M[['EquityIssueIPO_Cor','EquityIssueSEO_Cor']]
EFinDetail_M.dropna(inplace=True)
EFinDetail_M            =   EFinDetail_M[EFinDetail_M.index>=datetime.datetime(1960,1,1)]

## Normalize the Monthly Gross Issuance 
# Merge the lag book value asset into the flow dataset
EFinDetail_M['QDate']   =   EFinDetail_M.index.map(lambda x: \
                                datetime.datetime(x.year,int(np.ceil(x.month/3))*3-2,1))
EFinDetail_M            =   EFinDetail_M.merge(right=Sample_Q[['LagTotalAsset_Cor']],how='left', \
                                             left_on='QDate',right_index=True)
for FlowVar in ['EquityIssueIPO','EquityIssueSEO']:
    # by the Book Value Asset in the Last Quarter
    EFinDetail_M[FlowVar+'_LagTotalAsset_Cor'] \
                =   EFinDetail_M[FlowVar+'_Cor']/EFinDetail_M['LagTotalAsset_Cor']
    # by its own HP Trend
    Temp        =   EFinDetail_M[FlowVar+'_Cor']
    Temp.dropna(inplace=True)
    Temp        =   pd.concat(list(sm.tsa.filters.hpfilter(Temp,lamb=1600*3**4)), \
                              axis=1, \
                              keys=['LogDev_'+FlowVar,'LogTrend_'+FlowVar])
    Temp['Trend_'+FlowVar] \
                =   np.exp(Temp['LogTrend_'+FlowVar])
    EFinDetail_M=   EFinDetail_M.merge(Temp,how='outer', \
                                       left_index=True,right_index=True)
EFinDetail_M.drop('QDate',axis=1,inplace=True)

### Merge the Data
Sample_M        =   GrossIss_M.merge(right=EFinDetail_M,how='outer',left_index=True,right_index=True)
pickle.dump(Sample_M,open(DataFolder+'Sample_M.p','wb'))
# End of Section:
###############################################################################
