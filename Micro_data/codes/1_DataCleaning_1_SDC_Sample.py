#%% Load in the packages
from _Public import *


#%% Return/Accumulated Return History within the Event Window


### Raw Data Sets

## Read-in the SEO Deal Information and CRSP History Information
DataFolder          =   "Micro_data\\datasets\\SDC\\"
SDC_IssuanceSample  =   pd.read_pickle(DataFolder+'IssuanceSample.p')
SDC_CRSP_Info       =   pd.read_pickle(DataFolder+'SDC_CRSP_Info.p')


### Construct the Sample of Issuance Information
# DataFolder          =   "..\\temp\\"

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
