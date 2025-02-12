# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code computes the Exposure of each Issuance Event to Monetary Shocks.
    
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

#%% Read-in and Merge the High-Frequency Monetary Shock Data

### Load Data

## High-frequency Monetary Shocks
DataFolder      =   "..\\datasets\\HighFreqMonetaryShock\\"
GW_Data         =   pd.read_excel(DataFolder+"MS_GorodnichenkoWeber.xlsx", \
                                  sheet_name='Sheet2')
GW_Data['Date'] =   GW_Data['Date'].apply(lambda x: x.date())
GSS_Data        =   pd.read_excel(DataFolder+"MS_GurkaynakSackSwanson.xlsx", \
                                  sheet_name='Sheet2')
GSS_Data['Date']=   GSS_Data['Date'].apply(lambda x: x.date())

### Clean Data

## Convert bp to pct in GSS
VarList_MS      =   ['tight_surprise','wide_surprise']
for MsVar in VarList_MS:
    GSS_Data[MsVar]     =   pd.to_numeric(GSS_Data[MsVar],errors='coerce')/100
GSS_SubSet      =   GSS_Data['Date']<datetime.date(1994,2,4)

## Merge two datasets
MsHF            =   GW_Data[VarList_MS+['Date','actual change']] \
                    .append(GSS_Data.loc[GSS_SubSet,VarList_MS+['Date']], \
                            ignore_index=True,sort=True) \
                    .sort_values(by='Date').reset_index(drop=True) \
                    .rename(columns={'actual change': 'InterestRateChange', \
                                     'tight_surprise': 'MsTightHF', \
                                     'wide_surprise': 'MsWideHF'})

## Save Data of High-frequency Monetary Shocks
MsHF            =   MsHF[['Date','MsTightHF','MsWideHF','InterestRateChange']]
pickle.dump(MsHF,open('..\\temp\\MsHF.p','wb'))

# End of Section: 
###############################################################################


#%% Clean Romer and Romer Monetary Shocks on FOMC Dates

## Read-in the Data Sets
DataFolder          =   "..\\..\\Macro_data\\datasets\\MonetaryShocks_FromWieland\\"
MsRR_FOMC           =   pd.read_stata(DataFolder+"RR_FOMC.dta")
MsRR_AggM           =   pd.read_stata(DataFolder+"RR_monetary_shock_monthly.dta")

## Clean the Data Sets
# FOMC
MsRR_FOMC           =   MsRR_FOMC[['meeting_date','resid','resid_full','resid_romer']] \
                        .dropna(subset=['meeting_date']) \
                        .rename(columns={'meeting_date':'Date'})
MsRR_FOMC['Date']   =   MsRR_FOMC['Date'].dt.date
MsRR_FOMC['MDate']  =   MsRR_FOMC['Date'].map(lambda x: datetime.date(x.year,x.month,1))
MsRR_FOMC_AggM      =   MsRR_FOMC.groupby('MDate')['resid','resid_full','resid_romer'].sum()
# Reported Monthly Aggregated Time-sereis
MsRR_AggM           =   MsRR_AggM.rename(columns={'date': 'MDate'})
MsRR_AggM['MDate']  =   MsRR_AggM['MDate'].dt.date
MsRR_AggM.set_index('MDate',inplace=True)
# Check whether MsRR_AggM is consistent with MsRR_FOMC_AggM
MsRR_AggM.corrwith(MsRR_FOMC_AggM)
# Only Keep resid_full as the Monetary Shocks
MsRR                =   MsRR_FOMC[['Date','resid_full']] \
                        .rename(columns={'resid_full': 'MsRR'})
## Save the Data
DataFolder          =   '..\\temp\\'
pickle.dump(MsRR,open(DataFolder+'MsRR.p','wb'))

# End of Section:
###############################################################################



#%% Measure the Pass-through of Ms to Interest Rate


### Preliminaries

## Load in Data
DataFolder      =   "..\\temp\\"
MsHF            =   pickle.load(open(DataFolder+'MSHF.p','rb'))
MsRR            =   pickle.load(open(DataFolder+'MSRR.p','rb'))

## Merged Data
Ms              =   MsHF.merge(right=MsRR,how='outer',on='Date') \
                    .sort_values(by='Date').reset_index(drop=True)
# RR Sample
Ms_70_07        =   Ms.loc[( Ms['Date']>=datetime.date(1970,1,1) ) & \
                           ( Ms['Date']<=datetime.date(2007,6,30) ), \
                           ['MsRR','MsTightHF','MsWideHF','InterestRateChange']]
Ms_94_07        =   Ms.loc[( Ms['Date']>=datetime.date(1994,1,1) ) & \
                           ( Ms['Date']<=datetime.date(2007,6,30) ), \
                           ['MsRR','MsTightHF','MsWideHF','InterestRateChange']]


### Descriptive Evidence of Monetary Shocks

## Summary Statistics
SumStat_70_07   =   Ms_70_07.agg(['count','mean','std',lambda x: (x==0).sum()/x.count()*100]) \
                    .rename(index={'<lambda>': 'Pct(Ms==0)'})
SumStat_94_07   =   Ms_94_07.agg(['count','mean','std',lambda x: (x==0).sum()/x.count()*100]) \
                    .rename(index={'<lambda>': 'Pct(Ms==0)'})

## Regression Coefficients
MsVarList       =   ['MsRR','MsTightHF','MsWideHF']

for MsVar in MsVarList:
    TempRegResult   =   sm.OLS(Ms_94_07['InterestRateChange'], \
                               sm.add_constant(Ms_94_07[MsVar]), \
                               missing='drop').fit()
    SumStat_94_07.loc['Reg_Const',MsVar] \
                    =   TempRegResult.params['const']
    SumStat_94_07.loc['Reg_Beta',MsVar] \
                    =   TempRegResult.params[MsVar]
                    
    TempRegResult   =   sm.OLS(Ms_70_07['InterestRateChange'], \
                               sm.add_constant(Ms_70_07[MsVar]), \
                               missing='drop').fit()
    SumStat_70_07.loc['Reg_Const',MsVar] \
                    =   TempRegResult.params['const']
    SumStat_70_07.loc['Reg_Beta',MsVar] \
                    =   TempRegResult.params[MsVar]


## Merged Data
SumStat         =   pd.concat([SumStat_70_07,SumStat_94_07],axis=1, \
                              keys=['1970-2007','1994-2007'])

TableFolder     =   '..\\results\\TableGraph\\SumStat\\'
ExcelWriter     =   pd.ExcelWriter(TableFolder+'Ms.xlsx')
SumStat.to_excel(ExcelWriter,float_format='%.3f')
ExcelWriter.save()
# End of Section:
###############################################################################

#%% Measure the Exposure to Monetary Shocks of the Sample of Unique Dates


### Read-in the Information about the Issuance Deals and the Monetary Shocks

## SDC Deals Extracted from SDC
DataFolder      =   "..\\temp\\"
Sample          =   pickle.load(open(DataFolder+'SDC_IssuanceInfo.p','rb'))
Sample          =   Sample[['IssueID','FilingDate','LaunchDate','IssueDate']] \
                    .reset_index(drop=True)
## Monetary Shocks
DataFolder      =   "..\\temp\\"
MsHF            =   pickle.load(open(DataFolder+'MSHF.p','rb'))
MsRR            =   pickle.load(open(DataFolder+'MSRR.p','rb'))

MsHF            =   MsHF.dropna().reset_index(drop=True)
MsRR            =   MsRR.dropna().reset_index(drop=True)

### Functions Constructing the Exposure to Monetary Shocks

## For a Single Event Date
def TempFun_UnitMsInfo(TempDate,MsParam,MsDF,MsDateVar,MsVar):
    ActiveMsDF      =   MsDF.copy()
    
    if pd.isna(TempDate):
        # Not a valid Event Date
        ReturnFlag      =   0
    elif TempDate<MsDF[MsDateVar].min():
        # The Event Date is too Early
        ReturnFlag      =   -2
    elif TempDate>MsDF[MsDateVar].max():
        # The Event Date is too late
        ReturnFlag      =   -1
    else:
        # The Event Date is Covered by the List of Ms Date
        ReturnFlag      =   1
        ActiveMsDF      =   MsDF.loc[MsDF[MsDateVar]<=TempDate,[MsDateVar,MsVar]] \
                            .copy().sort_values(MsDateVar).reset_index(drop=True)
    if ReturnFlag==1:
        ActiveMsDF['GapDays']   =   ( TempDate-MsDF[MsDateVar] ).dt.days
        if MsParam['Type']=='Num_Days':
            ActiveMsDF      =   ActiveMsDF[ActiveMsDF['GapDays']<=MsParam['MaxNum']]
        elif MsParam['Type']=='Num_Ms':
            ActiveMsDF['Ms_Order']  =   ActiveMsDF['GapDays'].rank()
            ActiveMsDF      =   ActiveMsDF[ActiveMsDF['Ms_Order']<=MsParam['MaxNum']]
        
        Obs     =   ActiveMsDF[MsVar].count()
        if Obs>0:
            ActiveMsDF['Weight']    =   1/(1+ActiveMsDF['GapDays']**MsParam['WeightParam'])
            ActiveMsDF['Weight']    =   ActiveMsDF['Weight']/ActiveMsDF['Weight'].sum()
            Avg_W                   =   ( ActiveMsDF['Weight']*ActiveMsDF[MsVar] ).sum()
            Avg                     =   ActiveMsDF[MsVar].mean()
            Sum_W                   =   Avg_W*Obs
            Sum                     =   Avg*Obs
            GapDays_Min             =   ActiveMsDF['GapDays'].min()
            GapDays_Max             =   ActiveMsDF['GapDays'].max()
            MsDate_Last             =   ActiveMsDF[MsDateVar].max()
            MsDate_First            =   ActiveMsDF[MsDateVar].min()
        else:
            Avg_W                   =   0
            Avg                     =   0
            Sum_W                   =   0
            Sum                     =   0
            GapDays_Min             =   MsParam['MaxNum']
            GapDays_Max             =   MsParam['MaxNum']
            TempStartDate           =   TempDate+datetime.timedelta(days=-MsParam['MaxNum'])
            MsDate_Last             =   TempStartDate
            MsDate_First            =   TempStartDate
            
    else:
        Obs                     =   np.nan
        Avg_W                   =   np.nan
        Avg                     =   np.nan
        Sum_W                   =   np.nan
        Sum                     =   np.nan
        GapDays_Min             =   np.nan
        GapDays_Max             =   np.nan
        MsDate_Last             =   np.nan
        MsDate_First            =   np.nan
    
    StatList    =   [Obs,Avg_W,Avg,Sum_W,Sum,GapDays_Min,GapDays_Max,MsDate_Last,MsDate_First]
    TagList     =   ['Obs','Avg_W','Avg','Sum_W','Sum','GapDays_Min','GapDays_Max','MsDate_Last','MsDate_First']
    TagList     =   [MsParam['Tag']+'_'+MsVar+'_'+x for x in TagList]
    AggMsInfo   =   pd.DataFrame({TagList[ii]: StatList[ii] for ii in range(len(TagList))}, \
                                  index=[TempDate],columns=TagList)
    
    return AggMsInfo

## For a List of Event Dates
def TempFun_SeriesMsInfo(DateList,MsParam,MsDF,MsDateVar,MsVar):
    InitiateFlag    =   1
    for TempDate in DateList:
        UnitAggMsInfo   =   TempFun_UnitMsInfo(TempDate,MsParam,MsDF,MsDateVar,MsVar)
        if InitiateFlag:
            AggMsInfo       =   UnitAggMsInfo
            InitiateFlag    =   0
        else:
            AggMsInfo       =   AggMsInfo.append(UnitAggMsInfo)
            
    
    return AggMsInfo


### Construct Different Monetary Shock Exposures to the Event Dates
DataFolder      =   "..\\temp\\"

## List of Unique Filing and Issue Dates
EventDateList       =   Sample['FilingDate'].dropna().unique().tolist()+ \
                        Sample['LaunchDate'].dropna().unique().tolist()+ \
                        Sample['IssueDate'].dropna().unique().tolist()
                        
EventDateList       =   list(set(EventDateList))
EventDateList.sort()

## Compute the Different Agg-Ms of Different Event Dates
# High Frequency Ms: Most Previous One
MsParam         =   {'Type': 'Num_Ms', 'MaxNum': 1, 'Tag': 'Pre', 'WeightParam': 0}
AggMs_PreHF     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsHF,'Date','MsWideHF')
# High Frequency Ms: 30d
MsParam         =   {'Type': 'Num_Days', 'MaxNum': 30, 'Tag': '30d', 'WeightParam': 0}
AggMs_30dHF     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsHF,'Date','MsWideHF')
# High Frequency Ms: 90d
MsParam         =   {'Type': 'Num_Days', 'MaxNum': 90, 'Tag': '90d', 'WeightParam': 0}
AggMs_90dHF     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsHF,'Date','MsWideHF')
# RR Ms: Most Previous One
MsParam         =   {'Type': 'Num_Ms', 'MaxNum': 1, 'Tag': 'Pre', 'WeightParam': 0}
AggMs_PreRR     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsRR,'Date','MsRR')
# RR Ms: 30d
MsParam         =   {'Type': 'Num_Days', 'MaxNum': 30, 'Tag': '30d', 'WeightParam': 0}
AggMs_30dRR     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsRR,'Date','MsRR')
# RR Ms: 90d
MsParam         =   {'Type': 'Num_Days', 'MaxNum': 90, 'Tag': '90d', 'WeightParam': 0}
AggMs_90dRR     =   TempFun_SeriesMsInfo(EventDateList,MsParam,MsRR,'Date','MsRR')

## Merge the Data Sets
AggMs           =   pd.concat([AggMs_PreHF,AggMs_30dHF,AggMs_90dHF, \
                               AggMs_PreRR,AggMs_30dRR,AggMs_90dRR], \
                              axis=1,join='outer') \
                    .dropna(how='all')

pickle.dump(AggMs,open(DataFolder+'SDC_UniqueEventDate2Ms.p','wb'))

# End of Section:
###############################################################################