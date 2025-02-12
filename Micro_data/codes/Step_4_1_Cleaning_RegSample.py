# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code merges the Abnormal Return, Aggregate Controls, Issuance Information,
    with the Issuance Event Dates, and construct the Sample for the Final Regression.
Version History:
    Created: Thu Apr  4 12:07:10 2019
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
              for xx in ["D:\\Dropbox (Bank of Canada)\\Research Projects\\", \
                         "B:\\Dropbox (Bank of Canada)\\Research Projects\\"] ]
for Folder in FolderList:
    if os.path.exists(Folder):
        os.chdir(Folder)    


# End of Section: Setup Working Directory
###############################################################################

#%% Setups


### Paths
DataFolder      =   "..\\temp\\"


### Read-in Data Sets

## Key Deal-level Information
DS_IssuanceInfo =   pickle.load(open(DataFolder+"SDC_IssuanceInfo.p","rb"))

## Response Variables: Daily/Accumulated Abnormal/Original Returns
DS_AbRet        =   pickle.load(open(DataFolder+"SDC_AbRet_Wide.p","rb"))
DS_Ret          =   pickle.load(open(DataFolder+"SDC_Ret_Wide.p","rb"))

## Shock Variables: Different Measure of Exposure to Monetary Shocks
DS_Ms           =   pickle.load(open(DataFolder+"SDC_UniqueEventDate2Ms.p","rb"))
DS_Ms           =   DS_Ms.reset_index().rename(columns={'index': 'EventDate'})

## Control 1: Aggregate Economic Conditions
DS_AggControl   =   pickle.load(open(DataFolder+"AggControl_Q.p","rb"))

### Control 2: Individual Stock Price Movement
#DS_RetHist      =   pickle.load(open(DataFolder+"SDC_Ret.p","rb"))
#DS_AbRet        =   pickle.load(open(DataFolder+"SDC_AbRet_Long.p","rb"))

## Control 3: Firm-Level Information
DS_FirmInfo     =   pickle.load(open(DataFolder+"SDC_CompustatQ_FirmInfo.p","rb"))
DS_CompustatQ   =   pickle.load(open(DataFolder+"SDC_CompustatQ.p","rb"))

### Key Variable Lists

## List of the Dictionaries of Different Event
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]

## Issuance Deal Information
DealInfoVarList =   [x+y for x in ['FilingDate','LaunchDate','IssueDate'] \
                         for y in ['','_Quarter','_Year']]+ \
                    [x+y for x in ['GapDays','GapBusDays'] \
                         for y in ['_F2I','_L2I','_F2L']]+ \
                    ['FiledAmount','ProceedsAmount', \
                     'FiledShares', 'OfferedTotalShares','OfferedPrimaryShares', \
                     # 'FF5_Code','FF5_Name', \
                     'PrimaryPct','PrimaryFlag','ShelfIssueFlag']
## Response Variables
AccRetVarList   =   [IF+'_AccRet_'+str(-x)+'_'+str(x) \
                     for IF in ['I','L','F'] for x in range(1,11)]+ \
                    [IF+'_AccRet_'+str(0)+'_'+str(x) \
                     for IF in ['I','L','F'] for x in range(0,11)]
AccAbRetVarList =   [IF+'_Acc'+AbRet+'_'+str(-x)+'_'+str(x) \
                     for AbRet in ['AbRet','UniAbRet'] \
                     for IF in ['I','L','F'] for x in range(1,11)]+ \
                    [IF+'_Acc'+AbRet+'_'+str(0)+'_'+str(x) \
                     for AbRet in ['AbRet','UniAbRet'] \
                     for IF in ['I','L','F'] for x in range(0,11)]

## Shock Variables: Different Types of Measurement and Statistics
MsVarList       =   ['Pre_MsWideHF','30d_MsWideHF','90d_MsWideHF', \
                     'Pre_MsRR','30d_MsRR','90d_MsRR']
MsInfoList      =   ['Sum', \
                     'MsDate_First','MsDate_Last', \
                     'GapDays_Min','GapDays_Max']

## Control 1: Aggregate Economic Conditions
AggControlList  =   ['GdpGrowth','Inflation','UnemploymentRate','FedFundsRate', \
                     'VIX','SpRet_Sum','SpRet_Mean','SpRet_Std','RecessionFlag']

## Control 3: Firm-Level Information
FirmInfoControlList = list(set(DS_FirmInfo.columns)-set(['IssueID','Date']))
FirmControlList =   list(set(DS_CompustatQ.columns)-set(['IssueID','Date'])-set(FirmInfoControlList))

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

## Temporary Function Generating the Shifted Calendar Quarter
def TempFun_ShiftQDate(Date,GapQ):
    if pd.isna(Date):
        QDate       =   Date
    else:
        Y   =   Date.year
        Q   =   int(np.ceil(Date.month/3))
        NumQ=   Y*4+Q+GapQ
        Qp  =   np.mod(NumQ,4)
        Yp  =   int((NumQ-Qp)/4)
        if Qp==0:
            Qp  =   4
            Yp  =   Yp-1
        
        QDate   =   datetime.date(Yp,Qp*3-2,1)
    
    return QDate
# End of Section:
###############################################################################


#%% Incorporate the Response Variables and Shock Variables


###  Step 1: Initiate the RegSample by Adding the Response Variables into Data Set
RegSample       =   DS_AbRet[['IssueID']+AccAbRetVarList].merge( \
                            right=DS_Ret[['IssueID']+AccRetVarList],on='IssueID') \
                    .reset_index(drop=True)
RegSample[AccAbRetVarList+AccRetVarList] \
                =   RegSample[AccAbRetVarList+AccRetVarList]*100
## Winsorize the Extreme Abnormal Return
def TempFun_Winsorize(InputS,LowQ,HighQ):
    S       =   InputS.copy()
    LowS    =   S.quantile(LowQ)
    HighS   =   S.quantile(HighQ)
    S[ (S<LowS) | (S>HighS) ]   =   np.nan
    return S

for Var in AccAbRetVarList+AccRetVarList:
    RegSample[Var]  =   TempFun_Winsorize(RegSample[Var],0.005,0.995)

### Step 2: Incorporate Shock Variables and the Related Information in to RegSample

## Clean Data
for MsVar in MsVarList:
    DS_Ms[MsVar+'_GapDays_Min']     =   pd.to_numeric(DS_Ms[MsVar+'_GapDays_Min'], \
                                                      errors='coerce',downcast='integer')
    DS_Ms[MsVar+'_GapDays_Max']     =   pd.to_numeric(DS_Ms[MsVar+'_GapDays_Max'], \
                                                      errors='coerce',downcast='integer')
    
## Merge Links: Issue/Filing Dates
TempVarList     =   ['IssueID']+DealInfoVarList
RegSample       =   RegSample.merge(right=DS_IssuanceInfo[TempVarList], \
                                    how='left', on='IssueID') 

## Merge 
TempVarList     =   [x+'_'+y for x in MsVarList for y in MsInfoList]

for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    DateVar     =   EventDict['DateVar']
    
    RegSample   =   RegSample.merge(right=DS_Ms[['EventDate']+TempVarList], \
                                    how='left', \
                                    left_on=DateVar,right_on='EventDate') \
                    .rename(columns={x: Suffix+'_'+x for x in TempVarList}) \
                    .rename(columns={Suffix+'_'+x+'_Sum': Suffix+'_'+x for x in MsVarList}) \
                    .drop(['EventDate'],axis=1)

# End of Section:
###############################################################################


#%% Incorporate the Key Control Variables


### Control 1: Aggregate Economic Conditions 
for EventDict in EventDictList:
    Suffix          =   EventDict['Suffix']
    for MsVar in MsVarList:
        MsSuffix    =   Suffix+'_'+MsVar
        # Merge 
        RegSample['Date'] \
                    =   RegSample[MsSuffix+'_MsDate_First'].map(TempFun_LagQDate)
        RegSample   =   RegSample.merge(right=DS_AggControl[['Date']+AggControlList], \
                                        how='left',on='Date') \
                        .drop(['Date'],axis=1) \
                        .rename(columns={x: MsSuffix+'_'+x for x in AggControlList})


### Control 2: Individual Stock Price History
WinLeft         =   -70
WinRight        =   -10
InitiateFlag    =   True
for EventDict in EventDictList:
    Suffix          =   EventDict['Suffix']
    TempAbRetVarList=   [Suffix+'_AbRet_'+str(x) for x in range(WinLeft,WinRight+1)]
    TempAbRetVarList=   list( set(TempAbRetVarList) & set(DS_AbRet.columns.tolist()) )
    TempRetVarList  =   [Suffix+'_Ret_'+str(x) for x in range(WinLeft,WinRight+1)]
    TempRetVarList  =   list( set(TempRetVarList) & set(DS_Ret.columns.tolist()) )
    
    # Convert the Unit of Return to % Convert to pct Unit
    TempAbRetDS     =   DS_AbRet.set_index('IssueID')[TempAbRetVarList]*100
    TempRetDS       =   DS_Ret.set_index('IssueID')[TempRetVarList]*100
    # Calculate the Statistics
    TempStat_AbRet  =   TempAbRetDS.T.agg(['mean','std']).T \
                        .rename(columns={'mean': Suffix+'_AbRetRunup', \
                                         'std': Suffix+'_AbRetStd'})
    TempStat_Ret    =   TempRetDS.T.agg(['mean','std']).T \
                        .rename(columns={'mean': Suffix+'_RetRunup', \
                                         'std': Suffix+'_RetStd'})
    # Convert the Mean to the Total Return within the Window
    TempStat_AbRet[Suffix+'_AbRetRunup'] \
                    =   TempStat_AbRet[Suffix+'_AbRetRunup']*(WinRight-WinLeft+1)
    TempStat_Ret[Suffix+'_RetRunup'] \
                    =   TempStat_Ret[Suffix+'_RetRunup']*(WinRight-WinLeft+1)
    # Merge into one Data Set
    TempRunupDS     =   TempStat_AbRet.merge(right=TempStat_Ret,how='outer', \
                                             left_index=True,right_index=True)
    if InitiateFlag:
        DS_Runup    =   TempRunupDS
        InitiateFlag=   False
    else:
        DS_Runup    =   DS_Runup.merge(TempRunupDS,how='outer', \
                                       left_index=True,right_index=True)
DS_Runup        =   DS_Runup.reset_index().rename(columns={'index':'IssueID'})

RegSample       =   RegSample.merge(right=DS_Runup,how='left',on='IssueID')


### Control 3: Firm-level Controls (Fixed Firm Characteristics)
RegSample       =   RegSample.merge(right=DS_FirmInfo[['IssueID']+FirmInfoControlList],how='left',on='IssueID')

### Control 4: Firm-level Records
for EventDict in EventDictList:
    Suffix          =   EventDict['Suffix']
    for MsVar in MsVarList:
        MsSuffix    =   Suffix+'_'+MsVar
        TempMsDate  =   MsSuffix+'_MsDate_First'
        # Lagged Quarter Date
        RegSample['Date'] \
                    =   RegSample[TempMsDate].map(TempFun_LagQDate)
        # Merge 
        RegSample   =   RegSample.merge(right=DS_CompustatQ[['IssueID','Date']+FirmControlList], \
                                        how='left', \
                                        left_on=['IssueID','Date'],right_on=['IssueID','Date']) \
                        .drop(['Date'],axis=1) \
                        .rename(columns={x: MsSuffix+'_'+x for x in FirmControlList})
        # Generate Derived Variables
        for TempVar in ['FiledAmount','ProceedsAmount']:
            RegSample[MsSuffix+'_'+TempVar+'DivByEquity_MV'] \
                        =   RegSample[TempVar]/RegSample[MsSuffix+'_EquityMV_Common']*100
            RegSample[MsSuffix+'_'+TempVar+'DivByAsset'] \
                        =   RegSample[TempVar]/RegSample[MsSuffix+'_Asset']*100
                        
        for TempVar in ['FiledShares','OfferedTotalShares','OfferedPrimaryShares']:
            RegSample[MsSuffix+'_'+TempVar+'DivByCommonShares_Outstanding'] \
                        =   RegSample[TempVar]/(10**6)/RegSample[MsSuffix+'_CommonShares_Outstanding']*100


### Control 5: Industry Classification Dummy
# for ii in range(1,5):
#     RegSample.loc[~pd.isna(RegSample['FF5_Code']),'FF5_'+str(ii)]   =   0
#     RegSample.loc[RegSample['FF5_Code']==ii,'FF5_'+str(ii)]         =   1


### Control 6: Issuance Type Dummy
RegSample.loc[~pd.isna(RegSample['PrimaryFlag']),'PrimarySecondaryFlag']    =   0
RegSample.loc[RegSample['PrimaryFlag']==0,'PrimarySecondaryFlag']           =   1
RegSample.loc[~pd.isna(RegSample['PrimaryFlag']),'OnlySecondaryFlag']       =   0
RegSample.loc[RegSample['PrimaryFlag']==-1,'OnlySecondaryFlag']             =   1


### Save the Sample for Regression Analysis
pickle.dump(RegSample,open(DataFolder+"RegSample.p","wb"))
# End of Section:
###############################################################################

#%% Incorporate More Control Variables with Different Timing for Descriptive Evidence


SumStatSample   =   RegSample.copy()


### The Aggregate Controls based on the Event Date
for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    EventDateVar=   EventDict['DateVar']
    for LagNum in [0,1,2]:
        TempSuffix              =   Suffix+'_Lag'+str(LagNum)+'_'
        # Lagged Quarter Dates
        SumStatSample['Date']   =   SumStatSample[EventDateVar].map(lambda x: TempFun_ShiftQDate(x,-LagNum))
        # Merge
        SumStatSample           =   SumStatSample.merge(right=DS_AggControl[['Date']+AggControlList], \
                                                        how='left',on='Date') \
                                    .drop(['Date'],axis=1) \
                                    .rename(columns={x: TempSuffix+x for x in AggControlList})

### Firm-level Balance Sheet Information Controls
for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    EventDateVar=   EventDict['DateVar']
    for LagNum in [0,1,2]:
        TempSuffix              =   Suffix+'_Lag'+str(LagNum)+'_'
        # Lagged Quarter Dates
        SumStatSample['Date']   =   SumStatSample[EventDateVar].map(lambda x: TempFun_ShiftQDate(x,-LagNum))
        # Merge
        SumStatSample           =   SumStatSample.merge(right=DS_CompustatQ[['IssueID','Date']+FirmControlList], \
                                                        how='left', \
                                                        left_on=['IssueID','Date'],right_on=['IssueID','Date']) \
                                    .drop(['Date'],axis=1) \
                                    .rename(columns={x: TempSuffix+x for x in FirmControlList})
        # Generate Derived Variables
        for TempVar in ['FiledAmount','ProceedsAmount']:
            SumStatSample[TempSuffix+TempVar+'DivByEquity_MV'] \
                        =   SumStatSample[TempVar]/SumStatSample[TempSuffix+'EquityMV_Common']*100
            SumStatSample[TempSuffix+TempVar+'DivByAsset'] \
                        =   SumStatSample[TempVar]/SumStatSample[TempSuffix+'Asset']*100
                        
        for TempVar in ['FiledShares','OfferedTotalShares','OfferedPrimaryShares']:
            SumStatSample[TempSuffix+TempVar+'DivByCommonShares_Outstanding'] \
                        =   SumStatSample[TempVar]/(10**6)/SumStatSample[TempSuffix+'CommonShares_Outstanding']*100
        
        
### Save the Sample for Regression Analysis
pickle.dump(SumStatSample,open(DataFolder+"RegSample.p","wb"))
# End of Section:
###############################################################################


#%% Output to Stata File 
DS = pickle.load(open("..\\temp\\RegSample.p","rb"))
TempList = ["I_AccAbRet_"+str(-n)+'_'+str(n) for n in range(1,5)]
TempDS = DS.loc[:, ['gvkey', 'IssueDate' ]+TempList] \
        .rename(columns={"I_AccAbRet_"+str(-n)+'_'+str(n): "I_AccAbRet_"+str(n) for n in range(1,5)})
TempDS['IssueDate'] = pd.to_datetime(TempDS['IssueDate'])
TempDS.to_stata("../temp/AbRet.dta")
# %%
