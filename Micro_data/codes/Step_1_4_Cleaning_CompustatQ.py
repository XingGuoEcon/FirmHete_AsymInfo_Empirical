# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created on Mon Aug 24, 2020
    Current: 

@author: Xing Guo (guoxing.econ@gmail.com)

"""

#%% Import Moduels

## System Tools
import os
import numpy as np
from collections import OrderedDict
## I/O Tools
import _pickle as pickle
## Data Process Tools
import pandas as pd
import datetime
## Graphs
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as figpdf
## Statistical Tools
import statsmodels.api as sm
## Database API
from fredapi import Fred
## Numerical API
from scipy.interpolate import interp1d

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


#%% Firm Sample


### Import the Data Sets
DataFolder = "..\\..\\..\\..\\..\\Data\\Compustat\\Dataset\\"

## NAMES
NAMES = pickle.load(open(DataFolder+"comp_names.p","rb"))
# Preliminary Cleaning
NAMES = NAMES.dropna(subset=['gvkey']).reset_index(drop=True)
NAMES[['gvkey','cusip','cik','naics']] \
= NAMES[['gvkey','cusip','cik','naics']].astype(str)
'''
year1/year2 is the first/last fiscal year with accounting records.
'''
NAMES[['year1','year2','sic']] = NAMES[['year1','year2','sic']].astype(int)

NAMES = NAMES.dropna(subset=['gvkey']).reset_index(drop=True)

## COMPANY
COMPANY = pickle.load(open(DataFolder+"comp_company.p",'rb'))
# Preliminary Cleaning
'''
'dlrsn' records the reason to delete the sample point. 
'dldte' records the date when the sample point is deleted.
'''
COMPANY[['gvkey','dlrsn','fic']] \
= COMPANY[['gvkey','dlrsn','fic']].astype(str)
COMPANY['sic'] = pd.to_numeric(COMPANY['sic'],downcast='signed',errors='coerce')
COMPANY['dldte'] = pd.to_datetime(COMPANY['dldte'])
COMPANY['dlrsn'] = COMPANY['dlrsn'].str.strip()
COMPANY['ipodate'] = pd.to_datetime(COMPANY['ipodate'],errors='coerce')

COMPANY = COMPANY.dropna(subset=['gvkey']).reset_index(drop=True)

## SECURITY File
SECURITY = pickle.load(open(DataFolder+"comp_security.p",'rb'))
# Preliminary Cleaning
'''
'excntry' and 'exchg' records the country and market where the stock is exchanged.
'''
SECURITY[['gvkey','excntry']] = SECURITY[['gvkey','excntry']].astype(str)
SECURITY['exchg'] = pd.to_numeric(SECURITY['exchg'],downcast='signed',errors='coerce')

SECURITY = SECURITY.dropna(subset=['gvkey']).reset_index(drop=True)


## FF Industry Classification
SIC_FileLocation = '..\\datasets\\'+'SIC_List\\SIC_FF.xlsx'
FF10 = pd.read_excel(SIC_FileLocation,sheet_name='FF10')
FF5 = pd.read_excel(SIC_FileLocation,sheet_name='FF5')


### Clean the Sample

## Assemble the Firm Sample
VarList_NAMES = ['gvkey','sic','naics','year1','year2']
VarList_COMPANY = ['gvkey','fic','ipodate']
VarList_SECURITY = []

FirmSample = NAMES[VarList_NAMES] 
if len(VarList_COMPANY)>0:
    FirmSample = FirmSample.merge(right=COMPANY[VarList_COMPANY],how='outer',on='gvkey')
if len(VarList_SECURITY)>0:
    FirmSample = FirmSample.merge(right=SECURITY[VarList_SECURITY],how='outer',on='gvkey')

## Drop Observations
FirmDropFlag = {'Country_NonUSA':True, \
                'Sector_Fin':True,'Sector_Utility':True,'Sector_QuasiGov':True, \
                'Outliner_GiantFour':False}
OriginalObsNum = FirmSample.shape[0]
FirmDropNum = {**{'Original': OriginalObsNum}, \
               **{xx:0 for xx in FirmDropFlag.keys()}}
# Drop non-USA firms
# Note: in the USA & CAN sample, around 17.35% of firms are CAN.
if FirmDropFlag['Country_NonUSA']:
    TempSize = FirmSample.shape[0]
    TempInd_USA = (FirmSample['fic']=='USA')
    FirmSample = FirmSample[TempInd_USA ].reset_index(drop=True)
    FirmDropNum['Country_NonUSA'] = (TempSize-FirmSample.shape[0])/OriginalObsNum*100
    

# Drop Financial sector
if FirmDropFlag['Sector_Fin']:
    TempSize = FirmSample.shape[0]
    FirmSample = FirmSample[(FirmSample['sic']<6000) | (FirmSample['sic']>6999)] \
                 .reset_index(drop=True)
    FirmDropNum['Sector_Fin'] = (TempSize-FirmSample.shape[0])/OriginalObsNum*100

# Drop Utilities sector
if FirmDropFlag['Sector_Utility']:
    TempSize = FirmSample.shape[0]
    FirmSample = FirmSample[(FirmSample['sic']<4900) | (FirmSample['sic']>4999)] \
                 .reset_index(drop=True)
    FirmDropNum['Sector_Utility'] = (TempSize-FirmSample.shape[0])/OriginalObsNum*100


# Drop Quasi-Governmental sector
if FirmDropFlag['Sector_QuasiGov']:
    TempSize = FirmSample.shape[0]
    FirmSample = FirmSample[(FirmSample['sic']<9000) | (FirmSample['sic']>9999)] \
                 .reset_index(drop=True)
    FirmDropNum['Sector_QuasiGov'] = (TempSize-FirmSample.shape[0])/OriginalObsNum*100     

# Drop the four Giant Auto-mobile Firms
'''
Note:   GE: gvkey==005047,          Ford: gvkey==004839, 
        Chrysler: gvkey==003022,    GM: gvkey==005073
'''
if FirmDropFlag['Outliner_GiantFour']:
    TempSize = FirmSample.shape[0]
    FirmSample = FirmSample[(FirmSample['gvkey']!='005047') & \
                            (FirmSample['gvkey']!='004839') & \
                            (FirmSample['gvkey']!='003022') & \
                            (FirmSample['gvkey']!='005073') ] \
                 .reset_index(drop=True)
    FirmDropNum['Outliner_GiantFour'] = (TempSize-FirmSample.shape[0])/OriginalObsNum*100


## Generate Industry Code and Names
MissingInd_sic = pd.isnull(FirmSample['sic'])
MissingInd_naics = pd.isnull(FirmSample['naics'])
# FF-10 Industry
FirmSample['FF10_Code'] = 10
FirmSample.loc[MissingInd_sic,'FF10_Code'] = np.nan
FirmSample['FF10_Name'] = 'Others'
FirmSample.loc[MissingInd_sic,'FF10_Name'] = ''
for i in FF10.index:
    TempInd = ( FirmSample['sic']>=FF10.loc[i,'SIC_Start'] ) & \
              ( FirmSample['sic']<=FF10.loc[i,'SIC_End'] ) 
                                
    FirmSample.loc[TempInd,'FF10_Code'] = FF10.loc[i,'FF10_Code']
    FirmSample.loc[TempInd,'FF10_Name'] = FF10.loc[i,'FF10_Name']
# FF-5 Industry
FirmSample['FF5_Code'] = 5
FirmSample.loc[MissingInd_sic,'FF5_Code'] = np.nan
FirmSample['FF5_Name'] = 'Others'
FirmSample.loc[MissingInd_sic,'FF5_Name'] = ''
for i in FF5.index:
    TempInd = ( FirmSample['sic']>=FF5.loc[i,'SIC_Start'] ) & \
              ( FirmSample['sic']<=FF5.loc[i,'SIC_End'] ) 
                                
    FirmSample.loc[TempInd,'FF5_Code'] = FF5.loc[i,'FF5_Code']
    FirmSample.loc[TempInd,'FF5_Name'] = FF5.loc[i,'FF5_Name']


# End of Section:
###############################################################################


#%% Firm Records: Quarterly

DataFolder = "..\\..\\..\\..\\..\\Data\\Compustat\\Dataset\\"

### Preliminary Cleaning
    
## Import the Data Sets
FirmRecord_Q = pickle.load(open(DataFolder+"comp_fundq.p","rb"))

## Rename the Variables
SheetNameList = ['Identifier','Stock','Flow','Price']
VarTableList = []
for Temp in SheetNameList:
    VarTableList.append(pd.read_excel(open(DataFolder+'VarInfo_Q.xlsx','rb'),sheet_name=Temp))

VarTable = pd.concat(VarTableList,axis=0,keys=SheetNameList)
VarTable['VarCode'] = VarTable['VarCode'].map(lambda x: x.lower().strip())
VarTable['VarName'] = VarTable['VarName'].map(lambda x: x.strip())
VarNameDict = {VarTable.loc[ii,'VarCode']: VarTable.loc[ii,'VarName'] for ii in VarTable.index}

FirmRecord_Q.rename(columns=VarNameDict,inplace=True)

## Drop the Obs. without ID or Date
FirmRecord_Q = FirmRecord_Q.dropna(subset=['gvkey','CalendarQtr','FiscalQtr']) \
                .reset_index(drop=True)

## Create Different Date Variable Representation: Calendar and Fiscal Quarter
for QtrVar in ['CalendarQtr','FiscalQtr']:
    FirmRecord_Q[QtrVar+'_Quarter'] = FirmRecord_Q[QtrVar].map(lambda x: int(x[-1]))
    FirmRecord_Q[QtrVar+'_Year'] = FirmRecord_Q[QtrVar].map(lambda x: int(x[0:4]))
    FirmRecord_Q[QtrVar+'_Date'] = FirmRecord_Q[QtrVar].map(lambda x: datetime.date(int(x[0:4]),int(x[-1])*3-2,1))
    FirmRecord_Q[QtrVar+'_Qnum'] = FirmRecord_Q[QtrVar].map(lambda x: int(x[0:4])*4+int(x[-1]))

## Drop Observations
RecDropFlag = {'Year': False, \
               'RecFmt_ind': True,'RecFmt_scf': True, \
               'Outliner_at': False,'Outliner_accidentity': False}
OriginalObsNum = FirmRecord_Q.shape[0]
RecDropNum = {**{'Original': OriginalObsNum}, \
              **{xx: 0 for xx in RecDropFlag.keys()}}
# Only keep the records after 1988
if RecDropFlag['Year']:
    TempSize = FirmRecord_Q.shape[0]
    FirmRecord_Q = FirmRecord_Q[FirmRecord_Q['CalendarQtr_Year']>=1988] \
                 .reset_index(drop=True)
    RecDropNum['Year'] = (TempSize-FirmRecord_Q.shape[0])/OriginalObsNum*100
# Only keep the records with INDFMT=INDL
if RecDropFlag['RecFmt_ind']:
    TempSize = FirmRecord_Q.shape[0]
    FirmRecord_Q = FirmRecord_Q[FirmRecord_Q['IndFmt'].str.strip()=='INDL'] \
                 .reset_index(drop=True)
    RecDropNum['RecFmt_ind'] = (TempSize-FirmRecord_Q.shape[0])/OriginalObsNum*100
    
FirmRecord_Q.drop(['IndFmt'],axis=1,inplace=True)
# Only keep the records with SCF Format Code == 7
'''
In the fiscal year of 1988, SFAS required the firms to report SCF. 
Starting from 1988Q4, firms start adopting the new reporting standard. Between
1988Q4 and 2000Q1, the percentage of SCFQ=7 is around 95%. Since 2000, almost 
all the firms use SCFQ=7.
'''
if RecDropFlag['RecFmt_scf']:
    TempSize = FirmRecord_Q.shape[0]
    FirmRecord_Q = FirmRecord_Q.loc[FirmRecord_Q['SCFQ']==7].reset_index(drop=True)
    RecDropNum['RecFmt_scf'] = (TempSize-FirmRecord_Q.shape[0])/OriginalObsNum*100

FirmRecord_Q.drop(['SCFQ'],axis=1,inplace=True)
# Drop the observation with missing Total Asset
if RecDropFlag['Outliner_at']:
    TempSize = FirmRecord_Q.shape[0]
    FirmRecord_Q = FirmRecord_Q[np.isfinite(FirmRecord_Q['Asset'])]
    RecDropNum['Outliner_at'] = (TempSize-FirmRecord_Q.shape[0])/OriginalObsNum*100

# Drop the records significantly violating the Accounting Identity Asset=Liability+Equity
if RecDropFlag['Outliner_accidentity']:
    TempSize = FirmRecord_Q.shape[0]
    FirmRecord_Q['Residual'] = FirmRecord_Q['Asset']-FirmRecord_Q['Liability']-FirmRecord_Q['Equity']
    FirmRecord_Q['Residual'] = FirmRecord_Q['Residual']/FirmRecord_Q['Asset']
    FirmRecord_Q = FirmRecord_Q[np.abs(FirmRecord_Q['Residual'])<0.1].reset_index(drop=True)
    FirmRecord_Q.drop('Residual',axis=1,inplace=True)
    RecDropNum['Outliner_accidentity'] = (TempSize-FirmRecord_Q.shape[0])/OriginalObsNum*100


### Categorize the Variables

## Flow Variables
Temp = VarTable.loc['Flow']
# Flows counted as Year to Date Figure
VarList_AccFlow = Temp.loc[Temp['VarCategory']=='Acc','VarName'].to_list()
# Flows counted as Quarterly Figure
FlowVarList_NonAcc = Temp.loc[Temp['VarCategory']=='NonAcc','VarName'].to_list()
# All Flow Variables
VarList_Flow = FlowVarList_NonAcc+VarList_AccFlow

## Stock Variables
VarList_Stock = VarTable.loc['Stock','VarName'].to_list()

## Price Variables
VarList_Price = VarTable.loc['Price','VarName'].to_list()

## Variables used as Identifiers for each Obs.
VarList_ID = ['gvkey','FiscalQtr','CalendarQtr', \
              'FiscalQtr_Quarter','FiscalQtr_Year','FiscalQtr_Date','FiscalQtr_Qnum', \
              'CalendarQtr_Quarter','CalendarQtr_Year','CalendarQtr_Date','CalendarQtr_Qnum']

## Drop the irrelevant Variables
VarList_TotalQ = VarList_ID+VarList_Flow+VarList_Stock+VarList_Price
FirmRecord_Q = FirmRecord_Q[VarList_TotalQ]


### Deeper Cleaning 

## Decompose the Accumulated Flows into Quarterly Flows
# Record Gap
FirmRecord_Q = FirmRecord_Q.sort_values(by=['gvkey','FiscalQtr_Qnum']).reset_index(drop=True)
for QtrVar in ['CalendarQtr','FiscalQtr']:
    FirmRecord_Q[QtrVar+'_Gap'] = FirmRecord_Q.groupby('gvkey')[QtrVar+'_Qnum'].diff()
# Check Replicates of (gvkey,CalendarQtr)
FirmRecord_Q.groupby(['gvkey','CalendarQtr']).apply(lambda x: x.shape[0]).value_counts(normalize=True)
TempCheck_UniqueID  =   FirmRecord_Q.groupby(['gvkey','CalendarQtr']).apply(lambda x: x.shape[0])
# Decompose the Accumulated Flow into the Quarterly Flow
VarList_QtrFlow = [x+'_'+'QFlow' for x in VarList_AccFlow]
FirmRecord_Q[VarList_QtrFlow] \
= FirmRecord_Q.groupby(['gvkey','FiscalQtr_Year'])[VarList_AccFlow].diff()

FirmRecord_Q.loc[FirmRecord_Q['FiscalQtr_Gap']>1,VarList_QtrFlow] = np.nan
TempInd_FQ1 = FirmRecord_Q[FirmRecord_Q['FiscalQtr_Quarter']==1].index

for ii in range(len(VarList_AccFlow)):
    FirmRecord_Q.loc[TempInd_FQ1,VarList_QtrFlow[ii]] \
    = FirmRecord_Q.loc[TempInd_FQ1,VarList_AccFlow[ii]]

FirmRecord_Q = FirmRecord_Q.drop(VarList_AccFlow,axis=1) \
             .rename(columns={xx+'_QFlow': xx for xx in VarList_AccFlow})
             
             
### Merge the Firm Sample with the Firm Records
Sample_Q = FirmSample.merge(right=FirmRecord_Q,on='gvkey',how='inner')


pickle.dump(Sample_Q,open('..\\temp\\Sample_CS_Q.p','wb'))

# End of Section:
###############################################################################
