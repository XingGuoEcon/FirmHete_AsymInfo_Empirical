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
    Created: Sat May 11 11:10:43 2019
    Current: 

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


#%% Import Self-written Functions


# End of Section: Import Self-written Functions
###############################################################################

#%% Data Collection

### Setup

## Data Folder Path
DataFolder      =   '..\\temp\\'

## FRED API
fred                =   Fred('86cde3dec5dda5ffca44b58f01838b1e')


### PPI 

## Quarterly
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

## Monthly
try:
    PPI_M       =   pickle.load(open(DataFolder+'PPI_M.p','rb'))
except:
    PPI_M           =   pd.DataFrame(fred.get_series('PPIACO'))
    PPI_M.reset_index(inplace=True)
    PPI_M['index']  =   pd.to_datetime(PPI_M['index'])
    PPI_M.rename(columns={'index': 'MDate'},inplace=True)
    PPI_M.set_index('MDate',inplace=True)
    PPI_M.rename(columns={0: 'ppi'},inplace=True)
    PPI_M           =   PPI_M/100
    pickle.dump(PPI_M,open(DataFolder+'PPI_M.p','wb')) 
    

### NIPA Flows
try:
    Sample_NIPA     =   pickle.load(open(DataFolder+'NIPA_Q.p','rb'))
except:
    ## Nominal Flows
    # Nominal GDP
    NIPA_Q_GDP      =   pd.DataFrame(fred.get_series('NA000334Q'),columns=['GDP'])
    # Nominal Personal Consumption Expenditure
    NIPA_Q_PCE      =   pd.DataFrame(fred.get_series('NA000349Q'),columns=['PCE'])
    # Nominal Gross Private Domestic Investment
    NIPA_Q_Inv      =   pd.DataFrame(fred.get_series('NA000335Q'),columns=['INV'])
    # Assemble the Data
    NIPA_Q          =   pd.concat([NIPA_Q_GDP,NIPA_Q_PCE,NIPA_Q_Inv],axis=1)
    # Nominal to Real
    NIPA_Q          =   NIPA_Q.divide(PPI_Q['ppi'],axis=0)
    # Quarter-Million to Annual-Billion
    NIPA_Q          =   NIPA_Q/1000*4
    
    ## Add Real Industrial Production Index
    NIPA_Q_IndProd  =   pd.DataFrame(fred.get_series('IPB50001NQ'),columns=['IndProd'])
    NIPA_Q          =   NIPA_Q.merge(right=NIPA_Q_IndProd,how='outer', \
                                     left_index=True,right_index=True)
    pickle.dump(NIPA_Q,open(DataFolder+'NIPA_Q.p','wb'))


### Flow of Funds from Fed Z1 

##  Z1 Folder Path
Z1FolderPath    =   '..\\datasets\\Flow_of_Fund_FromFRB\\'
                  
## Run parser_define.py first
exec(open('Z1PythonToolkit\\parser_define.py').read())

## Obtain Root Search
Z1_data_root    =   ET.parse(Z1FolderPath+'Z1_LatestDataset\\Z1_data.xml').getroot()

## Read-in the code list for the FoF variables to be checked
CheckListFile   =   'DataProcessing_FoF_VariableCheckList.xlsx'
struct_FoF      =   pd.read_excel(pd.ExcelFile(CheckListFile,sheetname='FoF'))
struct_FoF      =   struct_FoF.drop_duplicates('Code').reset_index(drop=True)
## Data Collection from Main FoF        
i           =   1
for key in struct_FoF['Code']:
    search_id       =   genID(name_code=key)
    data            =   ParseFRB(Z1_data_root,search_id,rst_type='data_only')[0]
    # The reason why I am using temp_date seperately is the precausionary 
    # handle with the potential date mismatch
    temp_date       =   pd.to_datetime(data.TIME_PERIOD)
    #     =   pd.Series([str(date.year)+'Q'+str(date.quarter) \
    #                                        for date in temp_date])  
    data['TIME']    =   temp_date                                       
    data.loc[data[data['OBS_STATUS']!='A'].index,['OBS_VALUE']]     =   np.nan
    data.drop(['OBS_STATUS','TIME_PERIOD'],axis=1,inplace=True)   
    data.set_index('TIME',inplace=True)
    data.rename(columns={'OBS_VALUE':key},inplace=True)
    if i==1:
        dataset_FoF     =   data
        i               =   2
    else:
        dataset_FoF     =   dataset_FoF.join(data,how='outer')
dataset_FoF   =   dataset_FoF.astype(float)

dataset_FoF.index       =   dataset_FoF.index.map(lambda x: datetime.datetime(x.year,x.quarter*3-2,1))

## Nomial to Real 
dataset_FoF             =   dataset_FoF.divide(PPI_Q['ppi'],axis=0)

## Save the Data Sets into Pickle Files
pickle.dump(dataset_FoF,open(DataFolder+'dataset_FoF.p','wb'))


### FoF Equity Financing Details

##  Z1 Equity Flow Details Folder Path
EFinDetailFolderPath    =   '..\\datasets\\Flow_of_Fund_FromFRB\\Z1_EquityFlowDetails\\'
## Original Data
EFinDetail_Q            =   pd.read_csv(EFinDetailFolderPath+ \
                                        'equity-issuance-retirement-quarterly-historical.csv')
EFinDetail_M            =   pd.read_csv(EFinDetailFolderPath+ \
                                        'equity-issuance-retirement-monthly-historical.csv')

## Cleaning: Generate Date Format
# Quarterly
EFinDetail_Q['QDate']   =   pd.to_datetime(EFinDetail_Q['Date'])
EFinDetail_Q.drop('Date',axis=1,inplace=True)
EFinDetail_Q['QDate']   =   EFinDetail_Q['QDate'].apply(lambda x: datetime.datetime(x.year,(x.quarter-1)*3+1,1))
EFinDetail_Q.set_index('QDate',inplace=True)
# Monthly 
EFinDetail_M['MDate']   =   pd.to_datetime(EFinDetail_M['Date'])
EFinDetail_M['MDate']   =   EFinDetail_M['MDate'].apply(lambda x: datetime.datetime(x.year,x.month,1))
EFinDetail_M['QDate']   =   EFinDetail_M['MDate'].apply(lambda x: datetime.datetime(x.year,int(np.ceil(x.month/3))*3-2,1))
EFinDetail_M.drop(['Date','Quarter'],axis=1,inplace=True)
# Merge the Monthly Information into the Quarterly Data
temp                    =   EFinDetail_M.groupby('QDate').mean()*3
EFinDetail_Q            =   pd.merge(left=EFinDetail_Q,right=temp, \
                                     left_index=True, right_index=True, \
                                     how='outer')
# Rename the Variable Names
EFinDetail_Q.rename(columns={'Issuance, Net': 'EquityNetIssue_Cor', \
                             'Issuance, Gross': 'EquityIssue_Cor', \
                             'Retirement, Gross': 'EquityRetire_Cor', \
                             'Retirement, Repurchases': 'EquityRepurchase_Cor', \
                             'Retirement, Mergers and Acquisitions': 'EquityMA_Cor', \
                             'Issuance, IPO': 'EquityIssueIPO_Cor', \
                             'Issuance, SEO': 'EquityIssueSEO_Cor'}, \
                    inplace=True)
EFinDetail_M.rename(columns={'Issuance, IPO': 'EquityIssueIPO_Cor', \
                             'Issuance, SEO': 'EquityIssueSEO_Cor'}, \
                    inplace=True)
# Generate the Derived Variables
EFinDetail_Q['EquityIssuePublic_Cor'] \
                =   EFinDetail_Q['EquityIssueIPO_Cor']+ \
                    EFinDetail_Q['EquityIssueSEO_Cor']
EFinDetail_Q['EquityIssuePrivate_Cor'] \
                =   EFinDetail_Q['EquityIssue_Cor']- \
                    EFinDetail_Q['EquityIssuePublic_Cor']
EFinDetail_Q['EquityNetIssueExMA_Cor'] \
                =   EFinDetail_Q['EquityIssue_Cor']-EFinDetail_Q['EquityRepurchase_Cor']
EFinDetail_M.set_index('MDate',inplace=True)
EFinDetail_M.drop('QDate',axis=1,inplace=True)
# Nominal to Real
EFinDetail_M    =   EFinDetail_M.divide(PPI_M['ppi'],axis=0)*12
EFinDetail_Q    =   EFinDetail_Q.divide(PPI_Q['ppi'],axis=0)*4

## Save the Data Sets of Equity Issuance Details into Pickle Files
pickle.dump(EFinDetail_Q,open(DataFolder+'EFinDetail_Q.p','wb'))
pickle.dump(EFinDetail_M,open(DataFolder+'EFinDetail_M.p','wb'))


### IPO and SEO Number (from Jay Ritters)
## Folder Path
IpoSeoFolderPath=   '..\\datasets\\Flow_of_Fund_FromFRB\\IpoSeoNumber\\'

## IPO
IPO_M           =   pd.read_excel(IpoSeoFolderPath+'IPO_Number_Monthly.xls')
IPO_M['MDate']  =   IPO_M['Date'].map(lambda x: datetime.datetime(x.year,x.month,1))
IPO_M.rename(columns={'Gross Number of IPOs': 'IPO'},inplace=True)
IPO_M           =   IPO_M[['MDate','IPO']]

## SEO
SEO_M           =   pd.read_excel(IpoSeoFolderPath+'SEO_Number_Monthly.xlsx')
SEO_M['day']    =   1
SEO_M['MDate']  =   pd.to_datetime(SEO_M[['year','month','day']])   
SEO_M.rename(columns={'SEO_Number': 'SEO'},inplace=True)
SEO_M           =   SEO_M[['MDate','SEO']]  

## Merged Data
IpoSeo_M        =   pd.merge(IPO_M,SEO_M,how='inner',on='MDate')
IpoSeo_M['QDate']   = \
                    IpoSeo_M['MDate'].map(lambda x: datetime.datetime(x.year,(x.quarter-1)*3+1,1))
IpoSeo_Q                    =   IpoSeo_M.groupby('QDate').agg({ 'IPO':'mean',
                                                                'SEO':'mean'}) 
IpoSeo_Q[['IPO','SEO']] \
                =   IpoSeo_Q[['IPO','SEO']]*3 

## Clean the Data
IpoSeo_M.drop('QDate',axis=1,inplace=True)
IpoSeo_M.set_index('MDate',inplace=True)

## Save the IPO/SEO Data Sets into Pickle Files
pickle.dump(IpoSeo_Q,open(DataFolder+'IpoSeo_Q.p','wb'))
pickle.dump(IpoSeo_M,open(DataFolder+'IpoSeo_M.p','wb'))


### Gross Issuance Data from Baker and Wurgler (2000)

## Folder Path
GrossIssFolderPath  =   '..\\datasets\\GrossIssuance_BakerWurgler\\'

## Read-in Data
GrossIss_M      =   pd.read_excel(GrossIssFolderPath+'GrossIssuance.xlsx',sheet_name='Month')
GrossIss_M['MDate'] \
                =   GrossIss_M[['year','month']] \
                    .apply(lambda x: pd.datetime(x['year'],x['month'],1),axis=1)
GrossIss_M['QDate'] \
                =   GrossIss_M['MDate'].apply(lambda x: pd.datetime(x.year,x.quarter*3-2,1))
GrossIss_Q      =   GrossIss_M.groupby('QDate')[['Equity','Debt']].mean()*3
GrossIss_M.set_index('MDate',inplace=True)
GrossIss_M.drop(['yearmo','year','month','QDate'],axis=1,inplace=True)

## From nominal Million to Billion, Annulize
GrossIss_Q      =   GrossIss_Q/1000*4
GrossIss_M      =   GrossIss_M/1000*12

## Nominal to Real
GrossIss_M      =   GrossIss_M.divide(PPI_M['ppi'],axis=0)
GrossIss_Q      =   GrossIss_Q.divide(PPI_Q['ppi'],axis=0)

## Equity Share
GrossIss_M['EShare'] \
                =   GrossIss_M['Equity']/(GrossIss_M['Equity']+GrossIss_M['Debt'])
GrossIss_Q['EShare'] \
                =   GrossIss_Q['Equity']/(GrossIss_Q['Equity']+GrossIss_Q['Debt'])
#GrossIss_M                  =   GrossIss_M.divide(PPI_M['ppi'],axis=0)
#GrossIss_Q                  =   GrossIss_Q.divide(PPI_Q['ppi'],axis=0)

## Save the Gross Issuance Data Sets into Pickle Files
pickle.dump(GrossIss_M,open(DataFolder+'GrossIss_M.p','wb')) 
pickle.dump(GrossIss_Q,open(DataFolder+'GrossIss_Q.p','wb')) 
# END OF SECTION: Set up the FoF data parser & Collect data from FoF
###############################################################################

