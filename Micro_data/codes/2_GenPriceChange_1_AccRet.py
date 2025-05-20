
#%% Load in the packages
from _Public import *

#%% Load in the data 
DataFolder          =   "Micro_data\\datasets\\SDC\\"
SDC_IssuanceInfo    =   pd.read_pickle(DataFolder+"SDC_IssuanceInfo.p")
SDC_RetPanel        =   pd.read_pickle(DataFolder+"SDC_Ret.p")
SDC_AbRetPanelDict  =   pd.read_pickle(DataFolder+"SDC_AbRet_Panel.p") 

#%% Clean the Return information 
def tempfun(df, suffix):
    df = df.loc[:, idx[:,'AbRet']]
    df.columns = [xx[1]+'_' + xx[0] + '_'+suffix for xx in df.columns]   
    
    return df

AbRet = pd.concat([tempfun(SDC_AbRetPanelDict[xx], xx) for xx in SDC_AbRetPanelDict.keys()], axis=1, join='outer')

#%% Construct the sample
# Sample restriction:
# 1. Sample period: 1985Q1-2018Q2
SamplePeriod  = (datetime.date(1985,1,1), datetime.date(2018,12,31))
TempInd = (SDC_IssuanceInfo['IssueDate'] >= SamplePeriod[0]) & (SDC_IssuanceInfo['IssueDate'] <= SamplePeriod[1])
# 2. Only primary share offering 
TempInd = TempInd & (SDC_IssuanceInfo['ShareType']=='Primary')
# 3. Filing date has to be before the launch and issue date 
TempInd = TempInd & (SDC_IssuanceInfo['FilingDate'] <= SDC_IssuanceInfo['LaunchDate']) &\
          (SDC_IssuanceInfo['FilingDate'] <= SDC_IssuanceInfo['IssueDate'])

SDC_Sample = SDC_IssuanceInfo.loc[TempInd, :].copy()

# Generate other variables
SDC_Sample['s_Share'] = SDC_Sample['OfferedTotalShares'] / SDC_Sample['TotalShares_BeforeOffering']
SDC_Sample['s_Funding'] = SDC_Sample['ProceedsAmount'] / SDC_Sample['MarketValue']
SDC_Sample['LogK'] = np.log(SDC_Sample['TotalAsset_BeforeOffering'])
SDC_Sample['LogMV'] = np.log(SDC_Sample['MarketValue'])
SDC_Sample['LogProceeds'] = np.log(SDC_Sample['ProceedsAmount'])

# Generate the return panel 
TempVarList = ['IssueID', 'Date', 'DiffLogPrice', ] + [xx+'Date_Adj' for xx in ['F', 'L', 'I']]
RetPanel = SDC_Sample.merge(SDC_RetPanel[TempVarList], on='IssueID', how='left') \
                     .rename(columns={'DiffLogPrice': 'Ret', \
                                      'FDate_Adj': 'FDate', 'LDate_Adj': 'LDate', 'IDate_Adj': 'IDate'})

## Drop the dates that are not necessary to compute the price changes
EventDateWindow = (-120, 60)
TempInd = (RetPanel['FDate'] >= EventDateWindow[0]) & (RetPanel['IDate'] <= EventDateWindow[1])
RetPanel = RetPanel.loc[TempInd, :].reset_index(drop=True)

## Merge various abnormal returns into the return panel 
RetPanel = RetPanel.merge(AbRet.reset_index(), on=['IssueID', 'Date'], how='left', indicator=True)
RetPanel['_merge'].value_counts()
RetPanel.drop(columns=['_merge'], inplace=True)

## Starting of the event window
RetPanel['EventDate'] = RetPanel['FDate']

TempInd = RetPanel['ShelfIssueFlag'] == 1
RetPanel.loc[TempInd, 'EventDate'] = RetPanel.loc[TempInd, 'LDate']

## Ending of the event window 
RetPanel['EventDate_End'] = RetPanel['GapBusDays_F2I']
RetPanel.loc[TempInd, 'EventDate_End'] = RetPanel.loc[TempInd, 'GapBusDays_L2I']

#%% Measure the stock price changes associated with stock issuance: Baseline
def KeyRetStat(df):
    Num_Total = df.count()
    # Fraction of zero, positive, and negative values 
    Frac_0 = (df==0).sum()/Num_Total
    Frac_Pos = (df>0).sum()/Num_Total
    Frac_Neg = (df<0).sum()/Num_Total
    FracStat = pd.Series([Frac_0, Frac_Pos, Frac_Neg], index=['Frac_0', 'Frac_Pos', 'Frac_Neg'])
    # Mean, median, and standard deviation
    DescStat = df.describe(percentiles=[0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])

    return pd.concat([FracStat, DescStat], axis=0)


# Different measures of price changes associated with stock issuance
"""
We should look at three types of stock price changes for each event date:

1. Non-exclusive stock price change for each event date $t$: $\log(P_{t+1})- \log(P_{t-1})$;
2. Total stock price change from the starting event to the issue date: $\log(P_{t_{end}+1})-\log(P_{t_{start}-1})$
   * For non-shelf-registered issuance, the starting event is filing date
   * For shelf-registered issuance, the starting event is launch date
3. Exclusive stock price change for each event date:
   * For non-shelf-registered issuance, 
      * Filing date $t^{F}$: $\log(P_{t^{F}+1})- \log(P_{t^{F}-1})$
      * Launch date $t^{L}$: $\log(P_{t^{L}+1})- \log(\max\{P_{t^{L}-1}, P_{t^{F}+1} \})$
      * Issue date $t^{I}$: $\log(P_{t^{I}+1})- \log(\max\{P_{t^{I}-1}, P_{t^{L}+1} \})$
   * For shelf-registered issuance,
      * Filing date $t^{F}$: N.A. if $t^{F}<t^{L}-1$ else $\log(P_{t^{F}+1})- \log(P_{t^{L}-1})$   
      * Launch date $t^{L}$: $\log(P_{t^{L}+1})- \log(\max\{P_{t^{L}-1}, P_{t^{F}+1} \})$
      * Issue date $t^{I}$: $\log(P_{t^{I}+1})- \log(\max\{P_{t^{I}-1}, P_{t^{L}+1} \})$
"""
## Functions to calculate the price changes
def PriceChange_ByEventDate_NonExclusive(df, DateWindow=(-1, 1), RetVar='Ret'):
    PriceChange = pd.Series([df.loc[(df[xx+'Date']>DateWindow[0]) & (df[xx+'Date']<=DateWindow[1]) , RetVar].sum() \
                             for xx in ['F', 'L', 'I']], index=['F', 'L', 'I'])
    return PriceChange

def PriceChange_WithinEventWindow_Total(df, DateWindow=(-1, 1), RetVar='Ret'):
    return df.loc[(df['EventDate']>DateWindow[0]) & (df['EventDate']<=df['EventDate_End']+DateWindow[1]) , RetVar].sum()

def PriceChange_WithinEventWindow_First(df, DateWindow=(-1, 1), RetVar='Ret'):
    return df.loc[(df['EventDate']>DateWindow[0]) & (df['EventDate']<=DateWindow[1]) , RetVar].sum()

def PriceChange_WithinEventWindow_ByEventDate_Exclusive(df, DateWindow=(-1, 1), RetVar='Ret'):
    TempDict = {}
    for ET  in ['F', 'L', 'I']:
        if ET == 'F':
            tempind = (df[ET+'Date']>=DateWindow[0]) & (df[ET+'Date']<=DateWindow[1])
            Date_1 = df.loc[tempind, 'EventDate'].min()
            Date_2 = df.loc[tempind, 'EventDate'].max()

            Date_1 = max(Date_1, DateWindow[0])
            Date_2 = min(Date_2, df['EventDate_End'].values[0] + DateWindow[1])

            tempind = (df['EventDate']>Date_1) & (df['EventDate']<=Date_2)

            TempDict[ET] = df.loc[tempind, RetVar].sum() if tempind.sum()>0 else np.nan 

            Date_2_pre = Date_2
        else:
            tempind = (df[ET+'Date']>=DateWindow[0]) & (df[ET+'Date']<=DateWindow[1])
            Date_1 = df.loc[tempind, 'EventDate'].min()
            Date_2 = df.loc[tempind, 'EventDate'].max()

            Date_1 = max(Date_1, Date_2_pre)
            Date_2 = min(Date_2, df['EventDate_End'].values[0] + DateWindow[1])

            tempind = (df['EventDate']>Date_1) & (df['EventDate']<=Date_2)

            TempDict[ET] = df.loc[tempind, RetVar].sum() if tempind.sum()>0 else np.nan

            Date_2_pre = Date_2

    return pd.Series(TempDict)

## Alternative versions of price changes 
def PriceChange_AssembleDifferentMeasures(df, DateWindow=(-1, 1), RetVar='Ret'):
    PriceChange_NonExcl = df.groupby('IssueID').apply(lambda x: PriceChange_ByEventDate_NonExclusive(x, DateWindow=DateWindow, RetVar=RetVar), include_groups=False)

    PriceChange_Runup = RetPanel.groupby('IssueID').apply(lambda x: PriceChange_WithinEventWindow_Total(x, DateWindow=(-91, -1), RetVar=RetVar), include_groups=False)

    PriceChange_Total = RetPanel.groupby('IssueID').apply(lambda x: PriceChange_WithinEventWindow_Total(x, DateWindow=DateWindow, RetVar=RetVar), include_groups=False)

    PriceChange_First = RetPanel.groupby('IssueID').apply(lambda x: PriceChange_WithinEventWindow_First(x, DateWindow=DateWindow, RetVar=RetVar), include_groups=False)

    PriceChange_Excl = RetPanel.groupby('IssueID').apply(lambda x: PriceChange_WithinEventWindow_ByEventDate_Exclusive(x, DateWindow=DateWindow, RetVar=RetVar), include_groups=False)

    PriceChange = pd.concat([PriceChange_NonExcl.rename(columns={'F': 'PC_NonExcl_F', 'L': 'PC_NonExcl_L', 'I': 'PC_NonExcl_I'}), \
                            PriceChange_Total.rename('PC_Total'), PriceChange_First.rename('PC_FirstEvent'), \
                            PriceChange_Runup.rename('PC_Runup'), \
                            PriceChange_Excl.rename(columns={'F': 'PC_Excl_F', 'L': 'PC_Excl_L', 'I': 'PC_Excl_I'})], axis=1, join='outer')

    PriceChange['PC_Total_Event'] = PriceChange[['PC_Excl_'+vv for vv in ['F', 'L', 'I']]].sum(axis=1)

    return PriceChange

# PriceChange_NonExcl = RetPanel.groupby('IssueID').apply(PriceChange_ByEventDate_NonExclusive, include_groups=False)
# PriceChange_NonExcl.hist(bins=20)

# PriceChange_Runup = RetPanel.groupby('IssueID').apply(lambda x: PriceChange_WithinEventWindow_Total(x, DateWindow=(-91, -1)), include_groups=False)
# PriceChange_Runup.hist(bins=20)

# PriceChange_Total = RetPanel.groupby('IssueID').apply(PriceChange_WithinEventWindow_Total, include_groups=False)
# PriceChange_Total.hist(bins=20)

# PriceChange_First = RetPanel.groupby('IssueID').apply(PriceChange_WithinEventWindow_First, include_groups=False)
# PriceChange_First.hist(bins=20)

# PriceChange_Excl = RetPanel.groupby('IssueID').apply(PriceChange_WithinEventWindow_ByEventDate_Exclusive, include_groups=False)
# PriceChange_Excl.hist(bins=20)

# PriceChange = pd.concat([PriceChange_NonExcl.rename(columns={'F': 'PC_NonExcl_F', 'L': 'PC_NonExcl_L', 'I': 'PC_NonExcl_I'}), \
#                          PriceChange_Total.rename('PC_Total'), PriceChange_First.rename('PC_FirstEvent'), \
#                          PriceChange_Runup.rename('PC_Runup'), \
#                          PriceChange_Excl.rename(columns={'F': 'PC_Excl_F', 'L': 'PC_Excl_L', 'I': 'PC_Excl_I'})], axis=1, join='outer')

# PriceChange['PC_Total_Event'] = PriceChange[['PC_Excl_'+vv for vv in ['F', 'L', 'I']]].sum(axis=1)

PriceChange = PriceChange_AssembleDifferentMeasures(RetPanel, DateWindow=(-1, 1), RetVar='Ret')


#%% Alternative measures of price changes 
RegList = ['_'.join([xx, yy]) for xx in ['FF1', 'FF3', 'FF5'] for yy in ['PreEvent', 'PostEvent']]
ColIndexList = pd.MultiIndex.from_product([RegList, ['F', 'L', 'I']], names=['RegType', 'EventDateType'])

PriceChange_Alt = pd.concat([PriceChange_AssembleDifferentMeasures(RetPanel, DateWindow=(-1, 1), RetVar='_'.join(['AbRet', col[1], col[0]])) \
                             for col in ColIndexList], axis=1, join='outer', keys=ColIndexList)

PriceChange_Alt.columns = ['_'.join([col[2], col[0], col[1]]) for col in PriceChange_Alt.columns]

#%% Combine all the data sets 
DS = SDC_Sample.merge(pd.concat([PriceChange, PriceChange_Alt], axis=1, join='outer').reset_index(), on='IssueID', how='left')

pickle.dump(DS, open(DataFolder+'PriceChange.p', 'wb'))