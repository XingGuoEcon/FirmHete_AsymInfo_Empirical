#%% Load in the packages
from _Public import *


#%% Generating the Sample for Running the 1-Factor Model Regression


### Raw Data Sets

## Read-in the SEO Deal Information and CRSP History Information
DataFolder          =   "Micro_data\\datasets\\SDC\\"
CRSP_SDC            =   pd.read_pickle(DataFolder+'CRSP_SDC.p')
CRSP_SP             =   pd.read_pickle(DataFolder+'CRSP_SP.p')
CRSP_FF             =   pd.read_pickle(DataFolder+'FF_FactorDaily.p')
# DataFolder          =   "..\\temp\\"
SDC_IssuanceInfo    =   pd.read_pickle(DataFolder+'SDC_IssuanceInfo.p')

## Download the Aggregate Economic History

# Daily Risk-free Interest Rate
try:
    RfRate          =   pd.read_pickle(DataFolder+"RfRate.p")
except:
    fred                =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
    RfRate              =   fred.get_series('DTB3')
    RfRate              =   pd.DataFrame(RfRate/100/365,columns=['Rf'])
    RfRate.reset_index(inplace=True)
    RfRate.rename(columns={'index': 'Date'},inplace=True)
    RfRate['Date']      =   pd.to_datetime(RfRate['Date'])
    pickle.dump(RfRate,open(DataFolder+"RfRate.p",'wb'))

## Cleaning the CRSP data
# FF factors 
CRSP_FF['Date']             =   pd.to_datetime(CRSP_FF['Date'])

# Construct the unique link between SDC search id (CUSIP, CUSIP_8digit) and CRSP id (CUSIP_CRSP)
CUSIP_Link =  CRSP_SDC[['CUSIP','CUSIP_8digit', 'CUSIP_CRSP']].drop_duplicates().reset_index(drop=True)
CRSP_UniquePriceHist = CRSP_SDC[['CUSIP_CRSP','Date','Price']].drop_duplicates().reset_index(drop=True)

## Construct the Price History Sample
TempIDVarList       =   ['IssueID','FilingDate','LaunchDate','IssueDate','CUSIP','CUSIP_8digit']

CRSP_SDC            =   SDC_IssuanceInfo[TempIDVarList] \
                        .merge(right=CUSIP_Link, how='left',on=['CUSIP','CUSIP_8digit'], indicator=True) 
CRSP_SDC['_merge'].value_counts(normalize=True)   
CRSP_SDC.drop(columns=['_merge'], inplace=True)                  

CRSP_SDC            =   CRSP_SDC.merge(right=CRSP_UniquePriceHist,how='left',on='CUSIP_CRSP', indicator=True) 
CRSP_SDC['_merge'].value_counts(normalize=True)
CRSP_SDC.drop(columns=['_merge'], inplace=True)

## Preliminary Date Cleaning
# Date Format
CRSP_SDC['Date']            =   pd.to_datetime(CRSP_SDC['Date'])
# .apply(lambda x: x.date())
# Sorted Panel
CRSP_SDC                    =   CRSP_SDC.sort_values(['IssueID','Date']).reset_index(drop=True)
# Price
'''
In CRSP, the reported daily price is typically the closing price of the trading
day. If there is no closing price available, the reported price will be the 
average bid/ask price, with a negative sign.
'''
CRSP_SDC['Price']           =   CRSP_SDC['Price'].abs()

# Eliminate the Replicated Obs.
'''
Check the remove the potential duplicated records 
'''
print('There are '+ \
      str(np.round(CRSP_SDC.duplicated(['IssueID','Date','Price'],keep=False).sum()/CRSP_SDC.shape[0]*100,2)) + \
      '% duplicated observations with same IssueID, Date and Price.')
print('There are '+ \
      str(np.round(CRSP_SDC.duplicated(['IssueID','Date'],keep=False).sum()/CRSP_SDC.shape[0]*100,2)) + \
      '% duplicated observations with same IssueID and Date.')

CRSP_SDC                    =   CRSP_SDC.drop_duplicates(subset=['IssueID','Date'], \
                                                         keep='first') \
                                .sort_values(['IssueID','Date']) \
                                .reset_index(drop=True)

## Compute the Daily Return
CRSP_SDC['LogPrice']        =   np.log(CRSP_SDC['Price'])
CRSP_SDC['DiffLogPrice']    =   CRSP_SDC.groupby('IssueID')['LogPrice'].diff()

CRSP_SDC['DiffDate']        =   CRSP_SDC.groupby('IssueID')['Date'].diff().dt.days

CRSP_SDC['LagDate']         =   CRSP_SDC.groupby('IssueID')['Date'].shift()
TempInd                     =   ~(pd.isna(CRSP_SDC['Date']) | pd.isna(CRSP_SDC['LagDate']))
CRSP_SDC.loc[TempInd,'DiffBusDate'] \
                            =   np.busday_count(CRSP_SDC.loc[TempInd,'LagDate'].dt.date.values.tolist(), \
                                                CRSP_SDC.loc[TempInd,'Date'].dt.date.values.tolist())

CRSP_SDC['Ret_NAdj']        =   CRSP_SDC['DiffLogPrice']/CRSP_SDC['DiffDate']
CRSP_SDC['Ret_Adj']         =   CRSP_SDC['DiffLogPrice']/CRSP_SDC['DiffBusDate']

## Compute the Relative Date
"""
Note: some event date might be a non-business day, in this case we might have two business days with 0 gap business days.
To deal with this, we will define the adjusted relative date as the number of business days 
between a given date and the first business day after the event date.
"""
def next_business_day(date):
    if pd.tseries.offsets.BDay().is_on_offset(date):
        return date
    else:
        return date + pd.tseries.offsets.BDay(1)
    
EventDictList               =   [{'DateVar': 'FilingDate','Suffix': 'F'}, \
                                 {'DateVar': 'LaunchDate','Suffix': 'L'}, \
                                 {'DateVar': 'IssueDate','Suffix': 'I'}]
for EventDict in EventDictList:
    CRSP_SDC[EventDict['DateVar']] = pd.to_datetime(CRSP_SDC[EventDict['DateVar']])
    TempInd                     =   ~( pd.isna(CRSP_SDC[EventDict['DateVar']]) | \
                                       pd.isna(CRSP_SDC['Date']) )
    CRSP_SDC[EventDict['Suffix']+'Date_NAdj'] \
                                =   (CRSP_SDC['Date']-CRSP_SDC[EventDict['DateVar']]).dt.days
    CRSP_SDC.loc[TempInd,EventDict['Suffix']+'Date_Adj'] \
                                =   np.busday_count(CRSP_SDC.loc[TempInd,EventDict['DateVar']].map(next_business_day).dt.date.values.tolist(), \
                                                    CRSP_SDC.loc[TempInd,'Date'].dt.date.values.tolist())
    

### Prepare the SP500 Return History

## Preliminary Cleaning
# Date Format
CRSP_SP['Date']             =   pd.to_datetime(CRSP_SP['Date'])
# Sorted Panel
CRSP_SP                     =   CRSP_SP.drop_duplicates(['Date']).sort_values(['Date']) \
                                .reset_index(drop=True)
## Compute the Return
CRSP_SP['DiffLogSpIdx']     =   np.log(CRSP_SP['SpIdx']).diff()
CRSP_SP['DiffDate']         =   CRSP_SP['Date'].diff().dt.days
CRSP_SP['LagDate']          =   CRSP_SP['Date'].shift()
TempInd                     =   ~(pd.isna(CRSP_SP['Date']) | pd.isna(CRSP_SP['LagDate']))
CRSP_SP.loc[TempInd,'DiffBusDate'] \
                            =   np.busday_count(CRSP_SP.loc[TempInd,'LagDate'].dt.date.values.tolist(), \
                                                CRSP_SP.loc[TempInd,'Date'].dt.date.values.tolist())
CRSP_SP['SpRet_NAdj']       =   CRSP_SP['DiffLogSpIdx']/CRSP_SP['DiffDate']
CRSP_SP['SpRet_Adj']        =   CRSP_SP['DiffLogSpIdx']/CRSP_SP['DiffBusDate']


### Construct the Data Sample for Factor Model Regression
## Assemble all the aggregate returns  
Ret_Agg = CRSP_SP.merge(RfRate, how='left', on='Date').merge(CRSP_FF, how='left', on='Date') \
                 .rename(columns={'Rf': 'rf_3m'})

## Merge Different Data sets into CRSP_SDC
#+ Aggregate returns 
CRSP_SDC_VarList            =   ['IssueID', 'FilingDate', 'LaunchDate', 'IssueDate', \
                                 'Date','Ret_NAdj','Ret_Adj', 'DiffLogPrice']+ \
                                [x+'Date_'+y for x in ['F','L','I'] for y in ['NAdj','Adj']]
Ret_VarList                 =   ['Date','SpRet_NAdj','SpRet_Adj', 'DiffLogSpIdx', \
                                 'rf_3m', 'mktrf', 'smb', 'hml', 'rmw', 'cma', 'rf', 'umd']

SDC_Ret                     =   CRSP_SDC[CRSP_SDC_VarList] \
                                .merge(right=Ret_Agg[Ret_VarList],how='left',on='Date')

## Compute the Excess Return
for RetVar in ['DiffLogPrice','DiffLogSpIdx']:
    SDC_Ret['Ex'+RetVar]    =   SDC_Ret[RetVar]-SDC_Ret['rf']

for RetVar in ['Ret','SpRet']:
    for Type in ['NAdj','Adj']:
        SDC_Ret['Ex'+RetVar+'_'+Type]   =   SDC_Ret[RetVar+'_'+Type]-SDC_Ret['rf']

## Sorted Panel
SDC_Ret                     =   SDC_Ret.sort_values(['IssueID','Date']) \
                                .reset_index(drop=True)

pickle.dump(SDC_Ret,open(DataFolder+'SDC_Ret.p','wb'))
# End of Section: 
###############################################################################


# #%% Generate the Wide Panel of Return and Accumulated Return


# ### Setup

# ## Load-in the Data
# DataFolder      =   "..\\temp\\"
# DS_Ret          =   pickle.load(open(DataFolder+"SDC_Ret.p",'rb'))

# ## Setup
# StartEndDate    =   [-100,160]
# DateVar         =   'Date_Adj'
# RetVar          =   'Ret_Adj'

# ### Collect the Information about the Event Coverage

# ## Temporary Function Computing the Start/End day and number of days before/after the event date
# def TempFun_DateSumStat(DS,StartEndDate,DateType,DateVar,RetVar):
#     TempDateVar     =   DateType+DateVar
#     TempRetVar      =   RetVar
#     TempDS          =   DS[['IssueID',TempDateVar,TempRetVar]] \
#                         .dropna(subset=[TempRetVar]) \
#                         .reset_index(drop=True)
#     TempDS['Obs_L'] =   (TempDS[TempDateVar]<0) & (TempDS[TempDateVar]>=StartEndDate[0])
#     TempDS['Obs_R'] =   (TempDS[TempDateVar]>0) & (TempDS[TempDateVar]<=StartEndDate[1])
    
#     TempSumStat_0   =   TempDS.groupby('IssueID')[TempDateVar].agg(['min','max']) \
#                         .rename(columns={'min': DateType+'_MinDate','max': DateType+'_MaxDate'})
#     TempSumStat_1   =   TempDS.groupby('IssueID')[['Obs_L','Obs_R']].sum() \
#                         .rename(columns={'Obs_L': DateType+'_Obs_L','Obs_R': DateType+'_Obs_R'})
#     TempSumStat     =   TempSumStat_0.merge(right=TempSumStat_1,how='outer', \
#                                             left_index=True,right_index=True) \
#                         .reset_index()
#     return TempSumStat

# ## List of IssueID which has good coverage of the event
# '''
# 4 requirement: start before the left window end, end after the right window end,
# enough days before and after the event date and between the window ends.
# '''
# DS_Ret_Info     =   TempFun_DateSumStat(DS_Ret,StartEndDate,'F',DateVar,RetVar) \
#                     .merge(right=TempFun_DateSumStat(DS_Ret,StartEndDate,'L',DateVar,RetVar), \
#                            how='outer',on='IssueID') \
#                     .merge(right=TempFun_DateSumStat(DS_Ret,StartEndDate,'I',DateVar,RetVar), \
#                            how='outer',on='IssueID')
# GoodIssueID     =   {}
# for ILF in ['F','L','I']:
#     GoodIssueID[ILF]    =   DS_Ret_Info.loc[ ( DS_Ret_Info[ILF+'_MinDate']<=StartEndDate[0] ) & \
#                                              ( DS_Ret_Info[ILF+'_MaxDate']>=StartEndDate[1] ) & \
#                                              ( DS_Ret_Info[ILF+'_Obs_L']>=2/3*np.abs(StartEndDate[0]) ) & \
#                                              ( DS_Ret_Info[ILF+'_Obs_R']>=2/3*np.abs(StartEndDate[1]) ), \
#                                              'IssueID'].tolist()


# ### Compute the Return or Accumulated Return History within Event Window
# WindowList      =   [[StartEndDate[0],x] for x in range(StartEndDate[0],StartEndDate[1]+1)]+ \
#                     [[0,x] for x in range(0,10+1)]+ \
#                     [[-x,x] for x in range(1,10+1)]
# ## RetHist for Different Types of Event Date
# RetHistDict     =   {}

# for Suffix in ['F','L','I']:
#     # Setup
#     RelDateVar          =   Suffix+'Date_Adj'
#     # Eliminate Irrelevant Relative Periods
#     TempInd             =   ( DS_Ret[RelDateVar]>=StartEndDate[0] ) & \
#                             ( DS_Ret[RelDateVar]<=StartEndDate[1] )
#     TempDS              =   DS_Ret.loc[TempInd,['IssueID',RelDateVar,RetVar]] \
#                             .sort_values(['IssueID',RelDateVar])
    
#     # Transform the Long Table to Wide Table
#     TempDS              =   TempDS.pivot(index='IssueID',columns=RelDateVar,values=RetVar)
#     TempDS.columns      =   [Suffix+'_Ret_'+str(int(x)) for x in TempDS.columns]
#     TempDS.dropna(how='all',inplace=True)
#     # Generate the Accumulated Abnormal Return
#     for Window in WindowList:
#         WinStart            =   Window[0]
#         WinEnd              =   Window[1]
#         ColList             =   [Suffix+'_Ret_'+str(int(x)) for x in range(WinStart,WinEnd+1)]
#         VarName             =   Suffix+'_AccRet_'+str(WinStart)+'_'+str(WinEnd)
#         TempDS[VarName]     =   TempDS[ColList].sum(axis=1)/TempDS[ColList].count(axis=1)* \
#                                 ( WinEnd-WinStart+1 )
    
#     RetHistDict[Suffix] =   TempDS.sort_index().copy()


# ## Merge the Data Set
# RetHist         =   RetHistDict['F'].loc[GoodIssueID['F'],:] \
#                     .merge(right=RetHistDict['L'].loc[GoodIssueID['L'],:], \
#                            how='outer',left_index=True,right_index=True) \
#                     .merge(right=RetHistDict['I'].loc[GoodIssueID['I'],:], \
#                            how='outer',left_index=True,right_index=True) \
#                     .reset_index()

# DataFolder      =   "..\\temp\\"
# pickle.dump(RetHist,open(DataFolder+'SDC_Ret_Wide.p','wb'))
# # End of Section:
# ###############################################################################
