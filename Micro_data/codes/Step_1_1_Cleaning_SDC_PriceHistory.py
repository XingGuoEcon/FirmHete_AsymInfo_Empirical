# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code merges the information of Issuance Information from SDC and the 
    Price History around the Issuance Event from CRSP.
Version History:
    Created: Mon Apr 22 13:09:01 2019
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



#%% Import Self-written Functions
CodeFolder      =   'Toolkit\\'
exec(open(CodeFolder+'Toolbox_Graph.py').read())
idx             =   pd.IndexSlice
# End of Section: Import Self-written Functions
###############################################################################


#%% Return/Accumulated Return History within the Event Window


### Raw Data Sets

## Read-in the SEO Deal Information and CRSP History Information
DataFolder          =   "..\\datasets\\SDC\\Download_20190424\\"
SDC_IssuanceSample  =   pickle.load(open(DataFolder+'IssuanceSample.p','rb'))
SDC_CRSP_Info       =   pickle.load(open(DataFolder+'SDC_CRSP_Info.p','rb'))


### Construct the Sample of Issuance Information
DataFolder          =   "..\\temp\\"

## Merge the SDC_CRSP_Info into the Selected Issuance Sample
SDC_IssuanceInfo    =   SDC_IssuanceSample \
                        .merge(right=SDC_CRSP_Info[['CUSIP','CUSIP_8digit','CRSP_Info']], \
                               how='left',on=['CUSIP','CUSIP_8digit'])
                        
## Select the Deals with Good CRSP History (with unique CRSP query result)
'''
Around 74.48% of the Query get unique return and only 0.14% get two returns and 
the rest get no return.
'''
SDC_IssuanceInfo['CRSP_Info'].value_counts(normalize=True)

TempInd             =   SDC_IssuanceInfo['CRSP_Info']==1
SDC_IssuanceInfo    =   SDC_IssuanceInfo[TempInd].reset_index(drop=True)

## Generate the Derived Variables and Clean the Data
# Ratio of Primary Shares in the Total Offered Shares
SDC_IssuanceInfo['PrimaryPct'] \
                =   SDC_IssuanceInfo['OfferedPrimaryShares']/ \
                    SDC_IssuanceInfo['OfferedTotalShares']*100
# Flag for Primary Shares
SDC_IssuanceInfo.loc[~np.isnan(SDC_IssuanceInfo['PrimaryPct']),'PrimaryFlag'] \
                =   0
SDC_IssuanceInfo.loc[SDC_IssuanceInfo['PrimaryPct']>=100,'PrimaryFlag'] \
                =   1
SDC_IssuanceInfo.loc[SDC_IssuanceInfo['PrimaryPct']<=0,'PrimaryFlag'] \
                =   -1
# On-Shelf Registration
'''
The DaysInRegistration is one-to-one mapped to GapDays_F2I.
'''
SDC_IssuanceInfo.loc[SDC_IssuanceInfo['Rule415ShelfFlag']=='No','ShelfIssueFlag'] \
                =   0
SDC_IssuanceInfo.loc[SDC_IssuanceInfo['Rule415ShelfFlag']=='Yes','ShelfIssueFlag'] \
                =   1

## Save the Deal Information for the Selected Deal Sample
pickle.dump(SDC_IssuanceInfo,open(DataFolder+'SDC_IssuanceInfo.p','wb'))
# End of Section: 
###############################################################################
