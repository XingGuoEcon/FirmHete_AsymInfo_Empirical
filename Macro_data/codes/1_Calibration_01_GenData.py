"""
Code Introduction:
    This code 
Version History:
    Created: Tuesday Oct 26 2021
    Current: 

@author: Xing Guo (guoxing.econ@gmail.com)

"""
#%% Import Moduels

## System Tools
import os
import numpy as np
import scipy as sp
from collections import OrderedDict
## I/O Tools
import pickle as pickle
## Data Process Tools
import pandas as pd
import datetime
## Graphs
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as figpdf
import matplotlib.dates as matdates
from matplotlib.ticker import MaxNLocator
## Statistical Tools
import statsmodels.formula.api as sm
from scipy.stats import mstats
import statsmodels.api as SMAPI
from statsmodels.tsa.tsatools import detrend as DeTrend
from statsmodels.tsa.filters.hp_filter import hpfilter as HPfilter
from statsmodels.tsa.filters.bk_filter import bkfilter as BKfilter
## Database API
from fredapi import Fred
## Numerical API
from scipy.interpolate import interp1d
## Regular Expression API
import re

import xml.etree.ElementTree as ET

import TimeSeries as MyTS
fred = Fred(api_key='86cde3dec5dda5ffca44b58f01838b1e')
# End of Section: Import Moduels
###############################################################################

#%% Setup Work Directory

# Change to the Project Folder
## Windows System Path
FolderList = ["D:\\Dropbox (Bank of Canada)\\Research Projects\\01_FinancialShocks_RFMvsHFM\\Empirics\\", \
              "B:\\Dropbox (Bank of Canada)\\Research Projects\\01_FinancialShocks_RFMvsHFM\\Empirics\\"]
for Folder in FolderList:
    if os.path.exists(Folder):
        os.chdir(Folder)    


# End of Section: Setup Work Directory
###############################################################################

Sample_Period = (datetime.datetime(1984,1,1), datetime.datetime(2017,1,1))
#%% Clean the Interest Rate
DS_Rate_M = pd.read_excel('DataSource/InterestRate_M.xlsx')
# Convert the Monthly Date to Quarterly Date
DS_Rate_M['QDate'] = DS_Rate_M['Date'].map(lambda x: datetime.datetime(x.year, (x.quarter-1)*3+1 ,1 ))
DS_Rate_Q = DS_Rate_M.groupby('QDate')[['FFR_EffectiveRate', 'WuXia_EffectiveRate']].mean()

pickle.dump(DS_Rate_Q, open('Data/InterestRate_Q.p', 'wb'))

#%% Clean the Details of Equity Issuance 
# Set up the FoF data parser
Folder_Z1 = '..\\..\\..\\Data\\FRB_Z1\\'

DS_EFinDetails = pd.read_csv(Folder_Z1+'equity-issuance-retirement-quarterly-historical.csv')

DS_EFinDetails['QDate'] = DS_EFinDetails['Date'].map(lambda x: datetime.datetime(int(x[0:4]),3*(int(x[-1])-1)+1,1) )

DS_EFinDetails = DS_EFinDetails.rename(columns={'Issuance, Net': 'CorEFin_NetIss', \
                                                'Issuance, Gross': 'CorEFin_GrossIss', \
                                                'Retirements, Repurchases': 'CorEFin_Repurchase', \
                                                'Retirement, Gross': 'CorEFin_Retirement'}) \
                 [['QDate', 'CorEFin_NetIss', 'CorEFin_GrossIss', 'CorEFin_Repurchase', 'CorEFin_Retirement']]
DS_EFinDetails[['CorEFin_NetIss', 'CorEFin_GrossIss', 'CorEFin_Repurchase', 'CorEFin_Retirement']] \
    = DS_EFinDetails[['CorEFin_NetIss', 'CorEFin_GrossIss', 'CorEFin_Repurchase', 'CorEFin_Retirement']]*4*1000

#%% New Issuance from Jeff Wurgler
TempDS = pd.read_excel('DataSource/NewIssuance_Wurgler.xlsx')
TempDS['Date'] = TempDS.apply(lambda x: datetime.datetime(int(x['year']), int(x['month']), 1), axis=1)
TempDS['QDate'] = TempDS['Date'].map(lambda x: datetime.datetime(x.year, 3*(x.quarter-1)+1,1 ))
TempDS = TempDS.groupby('QDate')[['e1', 'e temp', 'e_new', 'e_ref']].mean()*3


#==============================================================================
# Flow of Funds: FRB-Z1 
#==============================================================================
# %% Query the FRB-Z1 Data

# Set up the FoF data parser
Folder_Z1 = '..\\..\\..\\Data\\FRB_Z1\\'
## Run parser_define.py first
exec(open(Folder_Z1+'Z1PythonToolkit\\parser_define.py').read())

## Obtain Root Search
Z1_data_root = ET.parse(Folder_Z1+'Z1_LatestDataset\Z1_data.xml').getroot()

## Read-in the code list for the FoF variables to be checked
struc_FoF = pd.read_excel('DataSource/AggVarInfo.xlsx',sheet_name='Z1')

# Collect Data from FoF dataset            
StartFlag = True
for (ii,key) in enumerate(struc_FoF['Code']):
    search_id = genID(name_code=key)
    search_rst = ParseFRB(Z1_data_root,search_id,rst_type='data_only')
    if len(search_rst)==0:
      print('No search result returned for ',struc_FoF['Variable'][ii])
      continue
    
    data = search_rst[0]
    # The reason why I am using temp_date seperately is the precausionary 
    # handle with the potential date mismatch
    temp_date = pd.to_datetime(data.TIME_PERIOD)
    data['TIME'] = temp_date                                       
    data.loc[data[data['OBS_STATUS']!='A'].index,['OBS_VALUE']] = np.nan
    data.drop(['OBS_STATUS','TIME_PERIOD'],axis=1,inplace=True)   
    data.set_index('TIME',inplace=True)
    data.rename(columns={'OBS_VALUE': struc_FoF['Variable'][ii]},inplace=True)
    if StartFlag:
        dataset_FoF = data
        StartFlag = False
    else:
        dataset_FoF = dataset_FoF.join(data,how='outer')
dataset_FoF = dataset_FoF.astype(float)



# %% Clean the FRB-Z1 Data
DS_Z1 = dataset_FoF.reset_index()
DS_Z1['QDate'] = DS_Z1['TIME'].map(lambda x: datetime.datetime(x.year, 3*(x.quarter-1)+1,1 ))

# Construct the Financial Variables for Corporate and Non-corporate Sectors
## Balance Sheet Composition
DS_Z1['Debt_Cor'] = DS_Z1['DebtSecurity_Cor'] + DS_Z1['DebtLoan_Cor']
DS_Z1['Debt_NonCor'] = DS_Z1['DebtLoan_NonCor']
## Financial flows
DS_Z1['DFin_Cor'] = DS_Z1['DebtSecurityIss_Cor'] + DS_Z1['DebtLoanIss_Cor']
DS_Z1['DFin_NonCor'] = DS_Z1['DebtLoanIss_NonCor']
DS_Z1['EFin_Cor'] = DS_Z1['EquityIss_Cor']-DS_Z1['Dividend_Cor']
DS_Z1['EFin_NonCor'] = DS_Z1['EquityIss_NonCor']

## Details of Equity Financing
DS_Z1 = DS_Z1.merge(DS_EFinDetails, how='left', on='QDate')

DS_Z1['EquityGrossIss_Cor'] = DS_Z1['EquityIss_Cor']+DS_Z1['CorEFin_Retirement']
# DS_Z1['EquityGrossIss_NonCor'] = DS_Z1['EquityIss_NonCor']
DS_Z1['EquityGrossIss_NonCor'] = 0
## Aggregate
for vv in ['Asset', 'Debt', 'EFin', 'DFin', 'GrossValAdd', 'NetValAdd', 'CapExp', 'Depreciation', 'EquityGrossIss']:
    DS_Z1[vv] = DS_Z1[vv+'_Cor']+DS_Z1[vv+'_NonCor']

DS_Z1['EquityGrossIssAlt'] = DS_Z1['EquityGrossIss_Cor'] + DS_Z1['EquityIss_NonCor']

# Nominal to Real Value
## Funderal Funds Rate

## Price Index
GdpDef = fred.get_series('USAGDPDEFQISMEI')
GdpDef.index = pd.to_datetime(GdpDef.index)
DS_Z1 = DS_Z1.set_index('QDate')
DS_Z1 = DS_Z1.join(GdpDef.rename('GdpDef'))

## Merge the Interest Rate
DS_Z1 = DS_Z1.merge(DS_Rate_Q, how='left', left_index=True, right_index=True)
## Conversion
VarList_Z1 = ['EFin', 'DFin', 'GrossValAdd', 'NetValAdd', 'CapExp', 'Debt', 'Asset', 'Depreciation', 'EquityGrossIss', 'EquityGrossIssAlt']
for vv in VarList_Z1:
    DS_Z1[vv] = DS_Z1[vv]/DS_Z1['GdpDef']

VarList_Z1 = ['EFin', 'DFin', 'GrossValAdd', 'NetValAdd', 'CapExp', 'Debt', 'Asset', 'Depreciation', 'EquityGrossIss']
for vv in VarList_Z1:
    DS_Z1[vv+'_Cor'] = DS_Z1[vv+'_Cor']/DS_Z1['GdpDef']
    DS_Z1[vv+'_NonCor'] = DS_Z1[vv+'_NonCor']/DS_Z1['GdpDef']
## Compute the Capital (Total)
Temp = DS_Z1.loc[:,['CapExp', 'Depreciation', 'GrossValAdd']]
Temp = Temp.loc[(Temp.index>=datetime.datetime(1952,1,1)) & (Temp.index<datetime.datetime(2017,1,1)),:].dropna().reset_index()
Temp = Temp.reset_index().rename(columns={'index': 'T'})

CapExp_0 = Temp.loc[0, 'CapExp']
def GenCapital(K0):
    Temp['Capital'] = np.nan
    Temp.loc[0, 'Capital'] = K0
    for tt in range(1,Temp.shape[0]):
        Temp.loc[tt,'Capital'] = Temp.loc[tt-1, 'Capital'] + (Temp.loc[tt, 'CapExp'] - Temp.loc[tt, 'Depreciation'])/4
    Temp['K_Y'] = Temp['Capital']/Temp['GrossValAdd']
    
    return Temp
def TempFun(x):
    Temp = GenCapital(CapExp_0/x)
    RegFit = sm.ols('K_Y~T', Temp).fit()
    Trend = RegFit.params['T']
    return Trend 

xx = np.linspace(0.01,0.99,num=10)
yy = [TempFun(x) for x in xx]
plt.plot(xx,yy)

x_0 = sp.optimize.bisect(TempFun,0.01,0.2)
Temp = GenCapital(CapExp_0/x_0)
Capital = Temp.set_index('QDate')['Capital']

## Compute the Capital (Corporate Sector)
Temp = DS_Z1.loc[:,['CapExp_Cor', 'Depreciation_Cor', 'GrossValAdd_Cor']] \
        .rename(columns={xx+'_Cor': xx for xx in ['CapExp', 'Depreciation', 'GrossValAdd']})
Temp = Temp.loc[(Temp.index>=datetime.datetime(1952,1,1)) & (Temp.index<datetime.datetime(2017,1,1)),:].dropna().reset_index()
Temp = Temp.reset_index().rename(columns={'index': 'T'})

CapExp_0 = Temp.loc[0, 'CapExp']
def GenCapital(K0):
    Temp['Capital'] = np.nan
    Temp.loc[0, 'Capital'] = K0
    for tt in range(1,Temp.shape[0]):
        Temp.loc[tt,'Capital'] = Temp.loc[tt-1, 'Capital'] + (Temp.loc[tt, 'CapExp'] - Temp.loc[tt, 'Depreciation'])/4
    Temp['K_Y'] = Temp['Capital']/Temp['GrossValAdd']
    
    return Temp
def TempFun(x):
    Temp = GenCapital(CapExp_0/x)
    RegFit = sm.ols('K_Y~T', Temp).fit()
    Trend = RegFit.params['T']
    return Trend 

xx = np.linspace(0.01,0.99,num=10)
yy = [TempFun(x) for x in xx]
plt.plot(xx,yy)

x_0 = sp.optimize.bisect(TempFun,0.01,0.3)
Temp = GenCapital(CapExp_0/x_0)
Capital_Cor = Temp.set_index('QDate')['Capital'].rename('Capital_Cor')


DS_Z1 = DS_Z1.join(Capital).join(Capital_Cor)

## Compute the Debt Stock
# Temp = DS_Z1.loc[:,['Debt', 'DFin', 'FFR_EffectiveRate', 'Capital']]
# Temp = Temp.loc[(Temp.index>=datetime.datetime(1960,1,1)) & (Temp.index<datetime.datetime(2017,1,1)),:].dropna().reset_index()
# Temp = Temp.reset_index().rename(columns={'index': 'T'})

# def GenDebtStock(D0):
#     Temp['DebtStock'] = np.nan
#     Temp.loc[0, 'DebtStock'] = D0
#     for tt in range(1,Temp.shape[0]):
#         Temp.loc[tt,'DebtStock'] = Temp.loc[tt-1, 'DebtStock']/(1+Temp.loc[tt-1, 'FFR_EffectiveRate']/100/4) + Temp.loc[tt, 'DFin']/4
#     Temp['D_K'] = Temp['DebtStock']/Temp['Capital'].shift()
#     return Temp

# Financial Ratio
SizeVar = 'Capital'
# SizeVar = 'Asset'
Fin_Lev = DS_Z1['Debt']/DS_Z1[SizeVar]
Fin_EFin_K = DS_Z1['EFin']/DS_Z1[SizeVar].shift()
Fin_DFin_K = DS_Z1['DFin']/DS_Z1[SizeVar].shift()
Fin_CapExp_K = DS_Z1['CapExp']/DS_Z1[SizeVar].shift()
Fin_EquGrossIss_K = DS_Z1['EquityGrossIss']/DS_Z1[SizeVar].shift()
Fin_EquGrossIssAlt_K = DS_Z1['EquityGrossIssAlt']/DS_Z1[SizeVar].shift()

Fin_EquGrossIss_K_Cor = DS_Z1['EquityGrossIss_Cor']/DS_Z1['Capital_Cor'].shift()
Fin_EFin_K_Cor = DS_Z1['EFin_Cor']/DS_Z1['Capital_Cor'].shift()

FinRatio = pd.concat([Fin_Lev, Fin_EFin_K, Fin_DFin_K, Fin_CapExp_K, Fin_EquGrossIss_K, Fin_EquGrossIssAlt_K, Fin_EquGrossIss_K_Cor, Fin_EFin_K_Cor], axis=1, \
                     keys=['Leverage','EFin_K', 'DFin_K', 'CapExp_K', 'EquityGrossIss_K', 'EquityGrossIssAlt_K', 'EquityGrossIss_K_Cor', 'EFin_K_Cor'])*100
FinRatio['Diff_Leverage'] = FinRatio['Leverage'].diff()
# Tranform the Data
DS_Original = DS_Z1.merge(FinRatio, how='left', left_index=True, right_index=True)
TempVarList = ['CapExp', 'GrossValAdd', 'Leverage', 'Diff_Leverage', 'EFin_K', 'DFin_K', 'CapExp_K', \
               'EquityGrossIss_K', 'EquityGrossIssAlt_K', 'EquityGrossIss_K_Cor', 'EFin_K_Cor']

DS_ToBeFiltered = DS_Original.loc[:,TempVarList]
DS_ToBeFiltered = DS_ToBeFiltered.loc[(DS_ToBeFiltered.index>=Sample_Period[0]) & \
                                      (DS_ToBeFiltered.index<=Sample_Period[1]), :].sort_index()
for vv in ['CapExp', 'GrossValAdd']:
    DS_ToBeFiltered[vv] = np.log(DS_ToBeFiltered[vv])*100

AggDS_Dict = MyTS.FilterTimeSeries(DS_ToBeFiltered)

AggDS_Dict['Original'] = DS_Original

pickle.dump(AggDS_Dict, open('TempData/AggDS_Dict_Z1.p', 'wb'))

#==============================================================================
# EBP Financial Shocks and NIPA Items
#==============================================================================
# %% NIPA Items

# Financial Shocks based on EBP
GZ_FinShock_M = pd.read_csv('Data/FinancialShocks/GZ_M_August_2016.csv')
CRSP_Return_M = pd.read_csv('Data/FinancialShocks/CRSP_Return_Monthly.csv')

def MDate2QDate(MDate):
    yymm = [int(xx) for xx in MDate.split('m')]
    yy = yymm[0]
    mm = yymm[1]

    return datetime.date(yy,int(np.floor((mm-1)/3)*3+1),1)

GZ_FinShock_M['QDate'] = GZ_FinShock_M['date'].map(MDate2QDate)
GZ_FinShock_Q = GZ_FinShock_M.groupby('QDate')['ebp_oa'].mean().rename('GZ_FinShock')

CRSP_Return_M['QDate'] = CRSP_Return_M['MDate'].map(lambda x: datetime.date(int(str(x)[0:4]),int(np.floor((int(str(x)[4:6])-1)/3)*3+1),1))
CRSP_Return_Q = CRSP_Return_M.groupby('QDate')['CRSP_Return'].mean()*100

# Effective Interest Rate 
InterestRate_M = pd.read_excel('DataSource/InterestRate_M.xlsx')
InterestRate_M['QDate'] = InterestRate_M['Date'].map(lambda x: datetime.datetime(x.year, (x.quarter-1)*3+1 ,1 ))
InterestRate_Q = InterestRate_M.groupby('QDate')['WuXia_EffectiveRate'].mean()

pickle.dump(DS_Rate_Q, open('Data/InterestRate_Q.p', 'wb'))

# Data from FRED
class FredTS:
    def __init__(self,FredCode,Label,SA=True,LogLin='Lin',Diff=False):
        self.Code = FredCode
        self.Label = Label
        self.SA = SA            # whether needs seasonal adjustment
        self.LogLin = LogLin    # Log or Lin deviation around the steady state
        self.Diff = Diff        # whether needs to take difference

# Download Data from FRED
VarInfo = {'PCE': FredTS('PCECC96','Real Private Consumption',LogLin='Log',Diff=True), \
           'PDI': FredTS('GPDIC1','Real Gross Private Domestic Investment', LogLin='Log', Diff=True), \
           'BFI': FredTS('PNFIC1','Real Private Nonresidential Fixed Investment', LogLin='Log', Diff=True), \
           'GCE': FredTS('GCEC1','Real Government Expenditure and Investment', LogLin='Log', Diff=True), \
           'GDP': FredTS('GDPC1', 'Real GDP', LogLin='Log', Diff=True), \
           'GdpPerCap': FredTS('A939RX0Q048SBEA', 'Real GDP per Capita', LogLin='Log', Diff=True), \
           'PcePerCap': FredTS('A794RX0Q048SBEA', 'Real PCE per Capita', LogLin='Log', Diff=True), \
           'Hours': FredTS('HOHWMN02USQ065S', 'Hours', LogLin='Log', Diff=True), \
           'Wage': FredTS('USAHOUREAQISMEI','Nominal wage', LogLin='Log', Diff=True), \
           'Earning': FredTS('LES1252881600Q', 'Real weekly earning', LogLin='Log', Diff=True), \
           'GdpDef': FredTS('USAGDPDEFQISMEI','GDP Deflator',LogLin='Log', Diff=True), \
           'InvPrice': FredTS('INVDEF','Relative Price of Investment Goods',LogLin='Log', Diff=True), \
           'FedFundRate': FredTS('FEDFUNDS', 'Effective Federal Funds Rates'), \
           'LongTermRate': FredTS('GS10','10-Year Treasury Yield'), \
           'UnemploymentRate': FredTS('UNRATE','Unemployment Rate') }
Data_Fred = {}
for vv in VarInfo.keys():
    print('Download data for ',VarInfo[vv].Label)
    Data_Fred[vv] = fred.get_series(VarInfo[vv].Code).rename(vv)

# Clean the Data from NIPA
TS_Dict = {}

## Ten-year Treasury Yield
Temp = Data_Fred['LongTermRate'].to_frame().reset_index().rename(columns={'index': 'MDate'})
Temp['QDate'] = Temp['MDate'].map(lambda x: datetime.date(x.year,3*int(np.floor((x.month-1)/3))+1,1))

TS_Dict['NomRate_LT'] = Temp.groupby('QDate')['LongTermRate'].mean()
## Effective Federal Funds Rate
Temp = Data_Fred['FedFundRate'].to_frame().reset_index().rename(columns={'index': 'MDate'})
Temp['QDate'] = Temp['MDate'].map(lambda x: datetime.date(x.year,3*int(np.floor((x.month-1)/3))+1,1))

TS_Dict['NomRate_ST'] = Temp.groupby('QDate')['FedFundRate'].mean()
## Excess Return of Stock Market
TS_Dict['CRSP_Ret'] = CRSP_Return_Q
## Wu and Xia Effective Rate 
TS_Dict['WuXiaRate'] = InterestRate_Q
## Unemployment
Temp = Data_Fred['UnemploymentRate'].to_frame().reset_index().rename(columns={'index': 'MDate'})
Temp['QDate'] = Temp['MDate'].map(lambda x: datetime.date(x.year,3*int(np.floor((x.month-1)/3))+1,1))
TS_Dict['UnEmpRate'] = Temp.groupby('QDate')['UnemploymentRate'].mean()
## Others
for vv in ['PCE', 'PDI', 'BFI', 'GCE', 'GDP', 'GdpPerCap', 'PcePerCap', 'Hours', 'GdpDef', 'InvPrice', 'Wage', 'Earning']:
    TS_Dict[vv] = Data_Fred[vv]

DS_Original = pd.concat(TS_Dict, axis=1).sort_index()
DS_Original['RealInvPrice'] = DS_Original['InvPrice']/DS_Original['GdpDef']
DS_Original['RealWage'] = DS_Original['Wage']/DS_Original['GdpDef']
# Tranform the data
DS_ToBeFiltered = DS_Original.copy()
DS_ToBeFiltered.index = pd.to_datetime(DS_ToBeFiltered.index)

## Take Logs 
for vv in ['PCE', 'PDI', 'BFI', 'GCE', 'GDP', 'GdpPerCap', 'PcePerCap', 'Hours', 'GdpDef', 'InvPrice', 'RealInvPrice', 'Wage', 'RealWage', 'Earning']:
    DS_ToBeFiltered[vv] = np.log(DS_ToBeFiltered[vv])*100
    DS_ToBeFiltered['Growth_'+vv] = DS_ToBeFiltered[vv].diff(1)
    if vv in ['GdpDef', 'InvPrice', 'RealInvPrice', 'Wage', 'RealWage', 'Earning']:
        DS_ToBeFiltered['Growth_'+vv] = DS_ToBeFiltered['Growth_'+vv] * 4

DS_ToBeFiltered = DS_ToBeFiltered.loc[(DS_ToBeFiltered.index>=Sample_Period[0]) & \
                                      (DS_ToBeFiltered.index<=Sample_Period[1]), :].sort_index()
## Filter the Data
AggDS_Dict = MyTS.FilterTimeSeries(DS_ToBeFiltered)
AggDS_Dict['Original'] = DS_Original

pickle.dump(AggDS_Dict, open('TempData/AggDS_Dict_AggPQ.p', 'wb'))


#==============================================================================
# Measurement used in Justiniano et. al. 
#==============================================================================

#%% Different Measures of Inflation and Price Index

# Preliminaries

## Temporary Function
def TempFun_QDate(Date):
    return datetime.datetime(Date.year,3*(int(np.floor((Date.month-1)/3))+1)-2,1)

# TFP

## Aggregate TFP (Log-diff)
TFP = pickle.load(open('Data\\TFP_Quarterly.p','rb')).dropna()
TFP = TFP/100.0
TFP = TFP[['dtfp','dtfp_util']] .rename(columns={'dtfp': 'dLog_TFP','dtfp_util': 'dLog_TFP_Adj'})
for vv in TFP.columns:
    Temp = SMAPI.tsa.x13_arima_analysis(TFP[vv],log=False)
    TFP[vv] = Temp.seasadj


# Hours
Hours = pd.DataFrame(fred.get_series('HOHWMN02USQ065S')).rename(columns={0: 'Hours'})


# GDP
## Nominal GDP
NGDP = pd.DataFrame(fred.get_series('GDP')).rename(columns={0: 'NGDP'})
## Nominal Gross Value Added
NValAdd_Cor = pd.DataFrame(fred.get_series('A455RC1Q027SBEA')).rename(columns={0: 'NValAdd_Cor'})
NValAdd_NonCor = pd.DataFrame(fred.get_series('NNBGAVQ027S')).rename(columns={0: 'NValAdd_NonCor'})/1e3    # Million to Billion
## GDP Deflator (2012=100)
GdpDef = pd.DataFrame(fred.get_series('GDPDEF')).rename(columns={0: 'GdpDef'})
                    
                    
# Price and Quantities of Investment and Consumption Goods

## Deflator for the Numerie Consumption Good (2012=100)
# Non-durable Goods
Pdef_NdCon = pd.DataFrame(fred.get_series('DNDGRD3Q086SBEA')).rename(columns={0: 'P_NdCon'})
# Service
Pdef_Serv = pd.DataFrame(fred.get_series('DSERRD3Q086SBEA')).rename(columns={0: 'P_Serv'})

## Deflator for the Investment Good
# Consumption of Durable Goods
Pdef_DCon = pd.DataFrame(fred.get_series('DDURRD3Q086SBEA')).rename(columns={0: 'P_DCon'})
# Domestic Private Investment
Pdef_PInv = pd.DataFrame(fred.get_series('A006RD3Q086SBEA')).rename(columns={0: 'P_PInv'})

## Nominal Quantity for Numerie Consumption Goods
# Non-durable Goods
Q_NdCon = pd.DataFrame(fred.get_series('PCND')).rename(columns={0: 'NQ_NdCon'})
# Service
Q_Serv  = pd.DataFrame(fred.get_series('PCESV')).rename(columns={0: 'NQ_Serv'})

## Deflator for the Investment Good
# Consumption of Durable Goods
Q_DCon = pd.DataFrame(fred.get_series('PCDG')).rename(columns={0: 'NQ_DCon'})
# Domestic Private Investment
Q_PInv = pd.DataFrame(fred.get_series('GPDI')).rename(columns={0: 'NQ_PInv'})


### Initiate the Data Set
## Merge the Deflators and Quantity Indexes into a Single Dataset
DSList = [Pdef_NdCon,Pdef_Serv,Pdef_DCon,Pdef_PInv, \
          Q_NdCon,Q_Serv,Q_DCon,Q_PInv, \
          NGDP,NValAdd_Cor,NValAdd_NonCor,GdpDef, \
          Hours, TFP]
DS_Fred = pd.concat(DSList,axis=1)

## Generate the Real Quantities
DS_Fred['Q_NdCon'] = DS_Fred['NQ_NdCon']/DS_Fred['P_NdCon']
DS_Fred['Q_Serv'] = DS_Fred['NQ_Serv']/DS_Fred['P_Serv']
DS_Fred['Q_Con'] = DS_Fred['Q_NdCon']+DS_Fred['Q_Serv']
DS_Fred['Q_DCon'] = DS_Fred['NQ_DCon']/DS_Fred['P_DCon']
DS_Fred['Q_PInv'] = DS_Fred['NQ_PInv']/DS_Fred['P_PInv']
DS_Fred['Q_Inv'] = DS_Fred['Q_DCon']+DS_Fred['Q_PInv']
DS_Fred['Q_ConInv'] = DS_Fred['Q_Inv']+DS_Fred['Q_Con']
DS_Fred['GDP'] = DS_Fred['NGDP']/DS_Fred['GdpDef']

## Generate the Weighted Average Deflators/Prices
#DS_FredPQ['AvgP_Con'] \
#                =   ( DS_FredPQ['P_NdCon']+DS_FredPQ['P_Serv'] )/2
#DS_FredPQ['AvgP_Inv'] \
#                =   ( DS_FredPQ['P_DCon']+DS_FredPQ['P_PInv'] )/2

DS_Fred['WAvgP_Con'] = ( DS_Fred['P_NdCon']*DS_Fred['Q_NdCon']+ \
                       DS_Fred['P_Serv']*DS_Fred['Q_Serv'] )/ \
                     ( DS_Fred['Q_NdCon']+DS_Fred['Q_Serv'] )
DS_Fred['WAvgP_Inv'] = ( DS_Fred['P_DCon']*DS_Fred['Q_DCon']+ \
                       DS_Fred['P_PInv']*DS_Fred['Q_PInv'] )/ \
                     ( DS_Fred['Q_DCon']+DS_Fred['Q_PInv'] )

DS_Fred['WAvgP_Inv_Real'] = DS_Fred['WAvgP_Inv']/DS_Fred['GdpDef']
                    
DS_Fred = DS_Fred.reset_index()
DS_Fred['QDate'] = DS_Fred['index'].apply(lambda x: TempFun_QDate(x))
DS_Fred.drop('index',axis=1,inplace=True)

# Transform the data
DS_Original = DS_Fred.set_index('QDate')

TempVarList_P = ['P_NdCon', 'P_Serv', 'P_DCon', 'P_PInv', 'GdpDef', 'WAvgP_Con', 'WAvgP_Inv', 'WAvgP_Inv_Real']
TempVarList_Q = ['Q_NdCon', 'Q_Serv', 'Q_Con', 'Q_DCon', 'Q_PInv', 'Q_Inv', 'Q_ConInv', 'GDP', 'Hours']
TempVarList_TFP = ['dLog_TFP', 'dLog_TFP_Adj']

DS_ToBeFiltered = DS_Original.loc[:, TempVarList_P+TempVarList_Q+TempVarList_TFP]

for vv in TempVarList_P:
    DS_ToBeFiltered[vv] = np.log(DS_ToBeFiltered[vv])*100
    DS_ToBeFiltered['Growth_'+vv] = DS_ToBeFiltered[vv].diff()*4

for vv in TempVarList_Q:
    DS_ToBeFiltered[vv] = np.log(DS_ToBeFiltered[vv])*100
    DS_ToBeFiltered['Growth_'+vv] = DS_ToBeFiltered[vv].diff()

DS_ToBeFiltered = DS_ToBeFiltered.loc[(DS_ToBeFiltered.index>=Sample_Period[0]) & \
                                      (DS_ToBeFiltered.index<=Sample_Period[1]), :].sort_index()
                                      
AggDS_Dict = MyTS.FilterTimeSeries(DS_ToBeFiltered)

AggDS_Dict['Original'] = DS_Original

pickle.dump(AggDS_Dict, open('TempData/AggDS_Dict_AltAggPQ.p','wb'))

# %% Shocks

# TFP Shocks
TFP = pickle.load(open('Data\\TFP_Quarterly.p','rb')).dropna()
TFP = TFP/100.0
TFP = TFP[['dtfp','dtfp_util']] .rename(columns={'dtfp': 'dLog_TFP','dtfp_util': 'dLog_TFP_Adj'})
for vv in TFP.columns:
    Temp = SMAPI.tsa.x13_arima_analysis(TFP[vv],log=False)
    TFP[vv] = Temp.seasadj


# Financial Shocks based on EBP
GZ_FinShock_M = pd.read_csv('Data/FinancialShocks/GZ_M_August_2016.csv')

def MDate2QDate(MDate):
    yymm = [int(xx) for xx in MDate.split('m')]
    yy = yymm[0]
    mm = yymm[1]

    return datetime.date(yy,int(np.floor((mm-1)/3)*3+1),1)

GZ_FinShock_M['QDate'] = GZ_FinShock_M['date'].map(MDate2QDate)
GZ_FinShock_Q = GZ_FinShock_M.groupby('QDate')['ebp_oa'].mean().rename('EBP')

# Monetary Policy Shocks
## Romer & Romer Shock
AggTS_MS_RR = pd.read_stata('DataSource/RR_monetary_shock_quarterly.dta')
AggTS_MS_RR = AggTS_MS_RR.set_index('date')['resid_full'].rename('MS_RR')
## High-frequency shocks 
AggTS_MS_Pablo = pd.read_excel('DataSource/MonetaryShock_HF_OttonelloWinberry.xlsx')
AggTS_MS_Pablo['QDate'] = AggTS_MS_Pablo['dateq'].map(lambda x: datetime.datetime(int(x[0:4]),3*(int(x[-1])-1)+1,1))
AggTS_MS_Pablo = AggTS_MS_Pablo.rename(columns={'Main shock (sum)': 'MS_HF_OW_sum', 'Main shock (smoothed)': 'MS_HF_OW_smoothed'}) \
                .set_index('QDate').drop('dateq', axis=1)*100

AggTS_MS_Wenting = pd.read_stata('DataSource/monetary_shocks_WentingSong.dta')
AggTS_MS_Wenting['QDate'] = AggTS_MS_Wenting['datetime'].dropna().map(lambda x: datetime.datetime(x.year, int((x.quarter-1)*3+1),1))
AggTS_MS_Wenting = AggTS_MS_Wenting.groupby('QDate')['mpshock_wt'].sum().rename('MS_HF_SS')

AggTS_MS = pd.concat([AggTS_MS_RR, AggTS_MS_Wenting, AggTS_MS_Pablo], axis=1).sort_index()

# Aggregate Shocks
AggDS_Shocks = pd.concat([TFP, GZ_FinShock_Q, AggTS_MS], axis=1).sort_index()
pickle.dump(AggDS_Shocks, open('TempData/AggDS_Shocks.p', 'wb'))


# %%
