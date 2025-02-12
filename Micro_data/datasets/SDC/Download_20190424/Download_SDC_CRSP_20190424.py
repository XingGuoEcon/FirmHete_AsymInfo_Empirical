# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Fri Apr 26 23:03:26 2019
    Current: 

@author: Xing Guo (xingguo@umich.edu)

"""
# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code merges the SEO deals from SDC with the price history information 
    around filing date from CRSP. Since the code automatically downloads data 
    from WRDS, user name and password will be needed.
Version History:
    Created: Sun Dec 10 21:41:34 2017
    Current: Wed Feb 21 22:14:00 2018

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





#%% Log-in WRDS
db                  =   wrds.Connection()
# End of Section:
###############################################################################
#%% Query and Download the Price History from CRSP


### Setup

## Target Folder
DataFolder      =   "..\\datasets\\SDC\\Download_20190424\\"
## Window Width
TimeWindow_Left =   265*2
TimeWindow_Right=   265*2

### Generate the List of CRSP and Date Range for Query

## Read in the List of Issuance to be Downloaded
IssuanceList    =   pickle.load(open(DataFolder+'IssueIDListForDownload.p','rb'))
IssuanceList    =   IssuanceList.reset_index(drop=True)

IssuanceList['MinDate'] \
                =   IssuanceList[['FilingDate','LaunchDate','IssueDate']] \
                    .apply(lambda x: min(x.dropna().values.tolist()),axis=1)
IssuanceList['MaxDate'] \
                =   IssuanceList[['FilingDate','LaunchDate','IssueDate']] \
                    .apply(lambda x: max(x.dropna().values.tolist()),axis=1)

## Generate the CusipDateList
CusipDateList   =   IssuanceList.groupby(['CUSIP','CUSIP_8digit']) \
                    .agg({'MinDate': 'min','MaxDate': 'max'}) \
                    .reset_index() \
                    .dropna(subset=['MinDate','MaxDate'])
CusipDateList['CRSP_Info'] \
                =   1


### Query from CRSP

## Initialization
SQLCounter_Total=   CusipDateList.shape[0]
SQLCounter_0    =   0
SQLCounter_1    =   0
SQLCounter_Clock=   1
for ii in CusipDateList.index:
    CUSIP_6digit=   CusipDateList.loc[ii,'CUSIP']
    CUSIP_8digit=   CusipDateList.loc[ii,'CUSIP_8digit']
    # Generate the RegExp for the CUSIP information
    CUSIP_RegExp=   CUSIP_8digit
    if CUSIP_6digit==CUSIP_8digit:
        CUSIP_RegExp    =   CUSIP_RegExp+'__'
    # Generate the Query Date Range
    Temp_Date1  =   np.busday_offset(CusipDateList.loc[ii,'MinDate'], \
                                     -TimeWindow_Left,roll='backward')
    Temp_Date2  =   np.busday_offset(CusipDateList.loc[ii,'MaxDate'], \
                                     TimeWindow_Right,roll='forward')
    # SQL Query in the CRSP Database                
    SQL_Text    =   "SELECT cusip,date,prc FROM crsp.dsf WHERE "+ \
                    "( cusip LIKE "+"\'"+CUSIP_RegExp+"\' )"+ \
                    " AND date between "+ \
                    "\'"+pd.to_datetime(Temp_Date1).strftime("%m/%d/%Y")+ \
                    "\'"+" and "+ \
                    "\'"+pd.to_datetime(Temp_Date2).strftime("%m/%d/%Y")+"\'"
    Temp_Data   =   db.raw_sql(SQL_Text)
    # Collect the Query Data    
    if Temp_Data.empty:
        CusipDateList.loc[ii,'CRSP_Info'] \
                        =   0
                        
        SQLCounter_0    =   SQLCounter_0+1
    else:
        
        CusipDateList.loc[ii,'CRSP_Info'] \
                        =   len(Temp_Data['cusip'].unique())
        # Clean Collected Data
        Temp_Data.rename(columns={'cusip': 'CUSIP_CRSP', \
                                  'prc': 'Price','date':'Date'},inplace=True)
        Temp_Data['CUSIP'] \
                        =   CUSIP_6digit
        Temp_Data['CUSIP_8digit'] \
                        =   CUSIP_8digit
        # Assemble Collected Data
        if SQLCounter_1==0:
            SDC_Data    =   Temp_Data
        else:
            SDC_Data    =   SDC_Data.append(Temp_Data,ignore_index=True)
        
        SQLCounter_1    =   SQLCounter_1+1                    
    # Update the in-time Information
    if (SQLCounter_0+SQLCounter_1)/SQLCounter_Total*100>=SQLCounter_Clock:
        SQLCounter_Clock=   SQLCounter_Clock+1
        
        pickle.dump(SDC_Data,open(DataFolder+"CRSP_SDC.p",'wb'))
        pickle.dump(CusipDateList,open(DataFolder+"SDC_CRSP_Info.p",'wb')) 
        
        print(str(np.round((SQLCounter_0+SQLCounter_1)/SQLCounter_Total*100,0))+ \
              '\%.'+'of deals have been searched, with hiting rate of '+ \
              str(np.round(SQLCounter_1/(SQLCounter_0+SQLCounter_1)*100,0))+'\%.')

## Final Save
pickle.dump(SDC_Data,open(DataFolder+"CRSP_SDC.p",'wb'))
pickle.dump(CusipDateList,open(DataFolder+"SDC_CRSP_Info.p",'wb')) 
print(str(np.round((SQLCounter_0+SQLCounter_1)/SQLCounter_Total*100,0))+ \
      '\%.'+'of deals have been searched, with hiting rate of '+ \
      str(np.round(SQLCounter_1/(SQLCounter_0+SQLCounter_1)*100,0))+'\%.')

# End of Section: 
###############################################################################

#%% Download other Datasets

### Setup

## Target Folder
DataFolder      =   "..\\temp\\"

### S&P 500 Index
SP_Data         =   db.raw_sql("SELECT caldt,spindx from crsp.dsp500")
SP_Data.rename(columns={'caldt': 'Date','spindx': 'SpIdx'},inplace=True)

pickle.dump(SP_Data,open(DataFolder+'CRSP_SP.p','wb'))


### Fama-French Factors
FF_Data         =   db.get_table(library='ff',table='factors_daily')
FF_Data.rename(columns={'date': 'Date'},inplace=True)

pickle.dump(FF_Data,open(DataFolder+'FF_FactorDaily.p','wb'))
# End of Section: 
###############################################################################