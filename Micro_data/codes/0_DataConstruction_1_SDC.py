#%% Load in the packages
from _Public import *

#%% Generating Raw Data


### Read-in 
DataFolder          =   "Micro_data\\datasets\\SDC\\"
DataFile            =   "Download_20190424.xls"

## SDC Data
TypeDict            =   {'CUSIP': str, '9-Digit\nCUSIP': str, \
                         'Immediate\nParent\nCUSIP': str, \
                         'Ulti-\nmate\nParent\nCUSIP': str, \
                         'Main\nSIC\nCode': str, \
                         'Ticker\nSymbol': str, \
                         }
Sample              =   pd.read_excel(open(DataFolder+DataFile,'rb'), \
                                      dtype=TypeDict)

## PPI Data
try:
    PPI_M           =   pd.read_pickle(DataFolder+'PPI_M.p')
except:
    fred            =   Fred('86cde3dec5dda5ffca44b58f01838b1e')
    PPI_M           =   pd.DataFrame(fred.get_series('PPIACO'))
    PPI_M.reset_index(inplace=True)
    PPI_M['index']  =   pd.to_datetime(PPI_M['index'])
    PPI_M.rename(columns={'index': 'MDate'},inplace=True)
    PPI_M.set_index('MDate',inplace=True)
    PPI_M.rename(columns={0: 'ppi'},inplace=True)
    PPI_M           =   PPI_M/100
    pickle.dump(PPI_M,open(DataFolder+'PPI_M.p','wb')) 

PPI_M.index                     =   PPI_M.index.map(lambda x: x.date())

## FF SIC Classification
SIC_FF5             =   pd.read_excel("Micro_data\\datasets\\SIC\\SIC_FF.xlsx", \
                                      sheet_name="FF5")
SIC_FF10            =   pd.read_excel("Micro_data\\datasets\\SIC\\SIC_FF.xlsx", \
                                      sheet_name="FF10")
### Clean Data

## Restrict the Sample and Rename the Variables
VarList             =   Sample.columns.tolist()
ReNameDict          =   {'Filing\nDate': 'FilingDate', \
                         'Issue\nDate': 'IssueDate', \
                         'Issuer': 'Issuer', \
                         'Main\nSIC\nCode': 'SIC', \
                         'Nation': 'Nation', \
                         'Ticker\nSymbol': 'TickerSymbol', \
                         "Primary\nExchange\nWhere\nIssuer's\nStock\nTrades": 'Exchange', \
                         'Principal\nAmount\n($ mil)': 'PrincipalAmount_ThisMarket', \
                         'Principal \nAmt - sum \nof all Mkts \n($ mil)': 'PrincipalAmount_AllMarket', \
                         'Proceeds\nAmt - in \nthis Mkt\n($ mil)': 'ProceedsAmount_ThisMarket',
                         'Proceeds \nAmt - sum \nof all Mkts\n($ mil)': 'ProceedsAmount_AllMarket', \
#                         'Offer\nPrice': 'OfferPrice', \
                         'Type\nof\nSecurity': 'SecurityType', \
                         'Cur-\nrency': 'Currency', \
                         'Shares \nFiled - \nin this Mkt': 'FiledShares_ThisMarket', \
                         'Shares \nFiled - \nsum of \nall Mkts': 'FiledShares_AllMarket', \
                         'Amt Filed - \nin this Mkt \n($ mil)': 'FiledAmount_ThisMarket', \
                         'Total Dollar\nAmount Filed': 'FiledAmount_AllMarket', \
                         'IPO\nFlag\n(Y/N)': 'IPO_Flag', \
                         'Total\nShares\nOffered\nIn This\nMarket': 'OfferedTotalShares_ThisMarket', \
                         'Primary \nShares \nOffered \n- in \nthis Mkt': 'OfferedPrimaryShares_ThisMarket', \
                         'Secondary \nShs Ofrd - \nin this Mkt': 'OfferedSecondaryShares_ThisMarket', \
                         'Shares \nOffered - \nsum of \nall Mkts': 'OfferedTotalShares_AllMarket', \
                         'CUSIP': 'CUSIP', \
                         '9-Digit\nCUSIP': 'CUSIP_9digit', \
                         'Immediate\nParent\nCUSIP': 'CUSIP_ImParent', \
                         'Ulti-\nmate\nParent\nCUSIP': 'CUSIP_UlParent', \
                         'Total\nAssets\nAfter\nthe\nOffering\n($ mil)': 'TotalAsset_AfterOffering', \
                         'Total\nAssets\nBefore\nthe\nOffering\n($ mil)': 'TotalAsset_BeforeOffering', \
                         'Total\nDebt\n($ mil)': 'TotalDebt', \
                         'Total\nEquity\n($ mil)': 'TotalEquity', \
                         'Market Value/\nMarket\nCapitalization': 'MarketValue_MarketCap', \
                         'Total\nCapital-\nization\n($ mil)': 'MarketCap', \
                         'Market\nValue\nBefore\nOffer\n($ mil)': 'MarketValue_BeforeOffering', \
                         'Shares\nOutstanding\nBefore\nOffering': 'TotalShares_BeforeOffering', \
                         'Shares\nOutstanding\nAfter\nthe\nOffering': 'TotalShares_AfterOffering', \
                         '% Of\nInsider\nShares\nBefore\nOffer': 'InsiderSharesPct_BeforeOffering', \
                         'Prim Shs as \n% of Shs Out\nBef Ofr - \nsum of \nall Mkts': 'PrimarySharesPct_BeforeOffering', \
                         'Prim Shs as \n% of Shs Out\nAft Ofr - sum\nof all Mkts': 'PrimarySharesPct_AfterOffering', \
                         'Prim Shs \nas % of Shs\nOfrd - sum \nof all Mkts': 'OfferedPrimarySharesPct', \
                         'Type\nof\nShares': 'ShareType', \
                         'Event\nHistory\nDate': 'EventHistoryDate', \
                         'Event\nHistory\nCode': 'EventHistoryCode', \
                         'Dates: Launch Date': 'LaunchDate', \
                         'Issue\nType': 'IssueType', \
                         'Issue\nType\nDescription': 'IssueTypeDescription', \
                         'Days In\nRegistration': 'DaysInRegistration', \
                         'Offering\nTechnique': 'OfferingTechnique', \
                         'Offering Technique\nDescription': 'OfferingTechniqueDescription', \
                         'Rights\nOffer\nFlag\n(Y/N)': 'RightsOfferFlag', \
                         'Rule\n415\nShelf': 'Rule415ShelfFlag', \
                         'Shelf Type': 'ShelfType', \
                         'Transaction\nType': 'TransactionType', \
                         'Use of Proceeds': 'ProceedsUse', \
                         }
Sample              =   Sample[list(ReNameDict.keys())].rename(columns=ReNameDict)

## Date-Time Variables
for DateVar in ['IssueDate','FilingDate','LaunchDate']:
    Sample[DateVar]             =   pd.to_datetime(Sample[DateVar])
    Sample[DateVar+'Flag']      =   ~pd.isna(Sample[DateVar])
    TempInd                     =   ~pd.isna(Sample[DateVar])
    Sample.loc[TempInd,DateVar+'_Year'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,1,1))
    Sample.loc[TempInd,DateVar+'_Quarter'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,x.quarter*3-2,1))
    Sample.loc[TempInd,DateVar+'_Month'] \
                                =   Sample.loc[TempInd,DateVar] \
                                    .map(lambda x: datetime.date(x.year,x.month,1))
                                    
    Sample[DateVar]             =   pd.to_datetime(Sample[DateVar]).map(lambda x: x.date())
    Sample[DateVar+'_Year']     =   pd.to_datetime(Sample[DateVar+'_Year']).map(lambda x: x.date())
    Sample[DateVar+'_Quarter']  =   pd.to_datetime(Sample[DateVar+'_Quarter']).map(lambda x: x.date())
    Sample[DateVar+'_Month']    =   pd.to_datetime(Sample[DateVar+'_Month']).map(lambda x: x.date())
    
## Gap Days between Filing or Launch Date and Issuance Date
Sample['GapDays_F2I'] \
                    =   (Sample['IssueDate']-Sample['FilingDate']).map(lambda x: x if pd.isnull(x) else x.days)
Sample['GapDays_L2I'] \
                    =   (Sample['IssueDate']-Sample['LaunchDate']).map(lambda x: x if pd.isnull(x) else x.days)
Sample['GapDays_F2L'] \
                    =   (Sample['LaunchDate']-Sample['FilingDate']).map(lambda x: x if pd.isnull(x) else x.days)
## Gap Business Days between Filing or Launch Date and Issuance Date
TempInd             =   ~ (pd.isna(Sample['FilingDate']) | pd.isna(Sample['IssueDate']))
Sample.loc[TempInd,'GapBusDays_F2I'] \
                    =   Sample.loc[TempInd,:] \
                        .apply(lambda x: np.busday_count(x['FilingDate'],x['IssueDate']),axis=1)
TempInd             =   ~ (pd.isna(Sample['LaunchDate']) | pd.isna(Sample['IssueDate']))
Sample.loc[TempInd,'GapBusDays_L2I'] \
                    =   Sample.loc[TempInd,:] \
                        .apply(lambda x: np.busday_count(x['LaunchDate'],x['IssueDate']),axis=1)
TempInd             =   ~ (pd.isna(Sample['FilingDate']) | pd.isna(Sample['LaunchDate']))
Sample.loc[TempInd,'GapBusDays_F2L'] \
                    =   Sample.loc[TempInd,:] \
                        .apply(lambda x: np.busday_count(x['FilingDate'],x['LaunchDate']),axis=1)
## String Variables
Sample.loc[(Sample['CUSIP']=='nan') | (pd.isna(Sample['CUSIP'])), 'CUSIP'] \
                    =   ''
Sample.loc[(Sample['CUSIP_9digit']=='nan') | (pd.isna(Sample['CUSIP_9digit'])), 'CUSIP_9digit'] \
                    =   ''

## Numerical Variables
NumVarList          =   ['TotalShares_BeforeOffering','TotalShares_AfterOffering']
Sample[NumVarList]  =   Sample[NumVarList].apply(pd.to_numeric,errors='coerce')

Sample['SIC']       =   Sample['SIC'].apply(pd.to_numeric,errors='coerce',downcast='signed')

## Only Keep the Issuance within US Markets and by US Firms
# Check Currency: 'US'
Sample['Currency'].value_counts(normalize=True)
Sample              =   Sample[Sample['Currency']=='US']
# Check Nation: 'United States'
Sample['Nation'].value_counts(normalize=True)
# Check Exchange: 'Nasdaq', 'New York', 
Sample['Exchange'].value_counts(normalize=True)
Sample              =   Sample[ (Sample['Exchange']=='Nasdaq') | \
                                (Sample['Exchange']=='New York') | \
                                (Sample['Exchange']=='American')]

## Only Keep the Issuance of Common or Ordinary Shares
Sample['SecurityType'].value_counts(normalize=True)
KeepTypeList        =   ['Common Shares','Ord/Common Shs.']
Sample              =   Sample[Sample['SecurityType'].isin(KeepTypeList)]

## Identifier
# Genarate the ID for each Issuance Deal
Sample['CUSIP_1_6'] =   Sample['CUSIP'].map(lambda x: x[0:6])
Sample['CUSIP_7_8'] =   Sample['CUSIP_9digit'].map(lambda x: x[6:8])
Sample['CUSIP_8digit']= Sample['CUSIP_1_6']+Sample['CUSIP_7_8']
Sample['IssueID']   =   Sample['CUSIP_1_6']+'_'+ \
                        Sample['CUSIP_7_8']+'_'+ \
                        Sample['LaunchDate'].map(lambda x: x.strftime('%Y%m%d'))+'_'+ \
                        Sample['IssueDate'].map(lambda x: x.strftime('%Y%m%d'))
# Evaluate the Ratio of Complete 6-digit and 8-digit CUSIP Code
print('Percentage with Missing CUSIP 1-6: '+ \
      str(np.round((Sample['CUSIP_1_6']=='').sum()/Sample.shape[0]*100,2))+'%' )
print('Percentage with Missing CUSIP 7-8: '+ \
      str(np.round((Sample['CUSIP_7_8']=='').sum()/Sample.shape[0]*100,2))+'%' )
# Assign the Types of CUSIP in terms of Their Completeness
Sample['CUSIP_DigitNum'] \
                    =   8
Sample.loc[(Sample['CUSIP_1_6']!='') & (Sample['CUSIP_7_8']==''),'CUSIP_DigitNum'] \
                    =   6
Sample.loc[(Sample['CUSIP_1_6']=='') & (Sample['CUSIP_7_8']==''),'CUSIP_DigitNum'] \
                    =   0

## Check the Uniqueness of IssueID
# Count the Observation Number with the Same Issuance ID
TempSample          =   Sample.set_index('IssueID')
TempSample['IssueID_ObsNum'] \
                    =   TempSample.index.value_counts()
# Tabulate the Observation Numbers
TempSample['IssueID_ObsNum'].value_counts(normalize=True)

'''
There are around 0.5% of the observations with multiple Issuance ID, i.e. the 
same CUSIP code, filing date and issuance date. For these observations, I will 
recompute some variables for them and delete the duplicated observations.
'''

### Output the List of IssueID and their Corresponding Dates
OutputVarList       =   ['CUSIP','CUSIP_8digit','FilingDate','LaunchDate','IssueDate']
OutputSample        =   TempSample[OutputVarList].drop_duplicates(subset=['CUSIP','CUSIP_8digit','LaunchDate','IssueDate'])
OutputSample        =   OutputSample.reset_index().drop_duplicates()
pickle.dump(OutputSample,open(DataFolder+'IssueIDListForDownload.p','wb'))


### Recompute the Key Variables with Considering the Obs. with Duplicated ID

## Information about the Issuance Transaction
# Principal Amount
TempSample['PrincipalAmount']   =   TempSample.groupby([TempSample.index.get_level_values(0)])['PrincipalAmount_ThisMarket'].sum()
# Filed Amount
TempSample['FiledAmount']       =   TempSample.groupby([TempSample.index.get_level_values(0)])['FiledAmount_ThisMarket'].sum()
# Proceeds Amount
TempSample['ProceedsAmount']    =   TempSample.groupby([TempSample.index.get_level_values(0)])['ProceedsAmount_ThisMarket'].sum()
# Filed Shares
TempSample['FiledShares']       =   TempSample.groupby([TempSample.index.get_level_values(0)])['FiledShares_ThisMarket'].sum()
# Offered Shares
TempSample['OfferedTotalShares']=   TempSample.groupby([TempSample.index.get_level_values(0)])['OfferedTotalShares_ThisMarket'].sum()
# Offered Shares-Primary
TempSample['OfferedPrimaryShares'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['OfferedPrimaryShares_ThisMarket'].sum()
# Offered Shares-Secondary
TempSample['OfferedSecondaryShares'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['OfferedSecondaryShares_ThisMarket'].sum()
# Offered Average Price
TempSample['OfferAvgPrice']     =   TempSample['ProceedsAmount']/TempSample['OfferedTotalShares']*(10**6)

## Information about the Firm
# SIC FF5 Classification
SIC_FF5             =   SIC_FF5.sort_values('SIC_Start').reset_index(drop=True)

TempSample.loc[~pd.isna(TempSample['SIC']),'FF5_Code'] \
                    =   0
TempSample.loc[~pd.isna(TempSample['SIC']),'FF5_Name'] \
                    =   'Others'
for ii in SIC_FF5.index:
    TempSample.loc[(TempSample['SIC']>=SIC_FF5.loc[ii,'SIC_Start']) & \
                   (TempSample['SIC']<=SIC_FF5.loc[ii,'SIC_End']),'FF5_Code'] \
                    =   SIC_FF5.loc[ii,'FF5_Code']
    TempSample.loc[(TempSample['SIC']>=SIC_FF5.loc[ii,'SIC_Start']) & \
                   (TempSample['SIC']<=SIC_FF5.loc[ii,'SIC_End']),'FF5_Name'] \
                    =   SIC_FF5.loc[ii,'FF5_Name']

# SIC FF10 Classification
SIC_FF10            =   SIC_FF10.sort_values('SIC_Start').reset_index(drop=True)

TempSample.loc[~pd.isna(TempSample['SIC']),'FF10_Code'] \
                    =   0
TempSample.loc[~pd.isna(TempSample['SIC']),'FF10_Name'] \
                    =   'Others'
for ii in SIC_FF10.index:
    TempSample.loc[(TempSample['SIC']>=SIC_FF10.loc[ii,'SIC_Start']) & \
                   (TempSample['SIC']<=SIC_FF10.loc[ii,'SIC_End']),'FF10_Code'] \
                    =   SIC_FF10.loc[ii,'FF10_Code']
    TempSample.loc[(TempSample['SIC']>=SIC_FF10.loc[ii,'SIC_Start']) & \
                   (TempSample['SIC']<=SIC_FF10.loc[ii,'SIC_End']),'FF10_Name'] \
                    =   SIC_FF10.loc[ii,'FF10_Name']
# Market Value
'''
I find in the downloaded sample, the reported market value is basically equal to 
 the total shares before offering x the stock price 1 day before offering
The reported market capitalization and market value/market capitalization are 
very hard to understand what they actually are.
'''
TempSample['MarketValue']       =   TempSample.groupby([TempSample.index.get_level_values(0)])['MarketValue_BeforeOffering'].max()
# Book Asset and Equity
'''
I also find that the sum of the Total Debt and Total Equity is quite different 
both the TotalAsset_BeforeOffering and TotalAsset_AfterOffering. Overall, the 
magnitude is kind of similar, but the difference is definitely large. In the 
variable definition published online, the definition for the total Debt and Equity
is not clear at all, especially, there is no information about the timing of 
these two variables. Therefore, when calculating the leverage change, we have to
assume the report debt is the debt before stock issuance and there is no change 
of debt stock which is associated with the equity issuance.
'''
TempSample['TotalAsset_BeforeOffering'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalAsset_BeforeOffering'].max()
TempSample['TotalAsset_AfterOffering'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalAsset_AfterOffering'].max()
TempSample['TotalDebt']         =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalDebt'].max()
TempSample['TotalEquity']       =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalEquity'].max()
TempSample['Leverage_BeforeOffering'] \
                                =   TempSample['TotalDebt']/TempSample['TotalAsset_BeforeOffering']
TempSample['Leverage_AfterOffering'] \
                                =   TempSample['TotalDebt']/TempSample['TotalAsset_AfterOffering']
TempSample['DiffLeverage']      =   TempSample['Leverage_AfterOffering']- \
                                    TempSample['Leverage_BeforeOffering']
# Share Structure
'''
I find the difference between the total shares before and after offering is not
really consistent with the reported total offered shares.
'''
TempSample['TotalShares_BeforeOffering'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalShares_BeforeOffering'].apply(np.nanmin)
TempSample['TotalShares_AfterOffering'] \
                                =   TempSample.groupby([TempSample.index.get_level_values(0)])['TotalShares_AfterOffering'].apply(np.nanmax)
TempSample['Ratio_OfferedShares2TotalShares'] \
                                =   TempSample['OfferedTotalShares']/TempSample['TotalShares_BeforeOffering']

## Drop the Duplicated Observations
TempSample                      =   TempSample[~TempSample.index.duplicated(keep='first')]

# Save the Number of IPO and SEO Deals-Full Sample
IpoSeoNum_F                     =   TempSample.groupby(['FilingDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'FilingDate_Quarter':'QDate','CUSIP_1_6':'F'})
IpoSeoNum_L                     =   TempSample.groupby(['LaunchDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'LaunchDate_Quarter':'QDate','CUSIP_1_6':'L'})
IpoSeoNum_I                     =   TempSample.groupby(['IssueDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'IssueDate_Quarter':'QDate','CUSIP_1_6':'I'})

IpoSeoNum                       =   IpoSeoNum_F.merge(right=IpoSeoNum_L,how='outer', \
                                                      on=['QDate','IPO_Flag']) \
                                               .merge(right=IpoSeoNum_I,how='outer', \
                                                      on=['QDate','IPO_Flag'])
IpoSeoNum.loc[IpoSeoNum['IPO_Flag']=='Yes','IPO_Flag'] \
                                =   'IPO'
IpoSeoNum.loc[IpoSeoNum['IPO_Flag']=='No','IPO_Flag'] \
                                =   'SEO'
IpoSeoNum                       =   IpoSeoNum.pivot(index='QDate',columns='IPO_Flag',values=['F','L','I'])
IpoSeoNum.columns               =   [IPO_Flag+'_'+Date_Type+'_All' \
                                     for IPO_Flag, Date_Type in \
                                     zip(IpoSeoNum.columns.get_level_values(1), \
                                         IpoSeoNum.columns.get_level_values(0))]
IpoSeoNum_All                   =   IpoSeoNum.copy()
## Drop the Financial and Utility Firms
# Financial Sector
TempInd_Finance                 =   ( TempSample['SIC']>=6000 ) & (TempSample['SIC']<=6999)
# Utility Sector
TempInd_Utility                 =   ( TempSample['SIC']>=4900 ) & (TempSample['SIC']<=4999)
# Quasi-government Sector
TempInd_QuasiGov                =   ( TempSample['SIC']>=9000 ) & (TempSample['SIC']<=9999)

TempInd_Drop                    =   (TempInd_Finance | TempInd_Utility | TempInd_QuasiGov)
TempSample                      =   TempSample[~TempInd_Drop]

# Save the Number of IPO and SEO Deals-Selected SIC Group
IpoSeoNum_F                     =   TempSample.groupby(['FilingDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'FilingDate_Quarter':'QDate','CUSIP_1_6':'F'})
IpoSeoNum_L                     =   TempSample.groupby(['LaunchDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'LaunchDate_Quarter':'QDate','CUSIP_1_6':'L'})
IpoSeoNum_I                     =   TempSample.groupby(['IssueDate_Quarter','IPO_Flag']) \
                                    ['CUSIP_1_6'].count() \
                                    .to_frame().reset_index() \
                                    .rename(columns={'IssueDate_Quarter':'QDate','CUSIP_1_6':'I'})

IpoSeoNum                       =   IpoSeoNum_F.merge(right=IpoSeoNum_L,how='outer', \
                                                      on=['QDate','IPO_Flag']) \
                                               .merge(right=IpoSeoNum_I,how='outer', \
                                                      on=['QDate','IPO_Flag']) 
IpoSeoNum.loc[IpoSeoNum['IPO_Flag']=='Yes','IPO_Flag'] \
                                =   'IPO'
IpoSeoNum.loc[IpoSeoNum['IPO_Flag']=='No','IPO_Flag'] \
                                =   'SEO'
IpoSeoNum                       =   IpoSeoNum.pivot(index='QDate',columns='IPO_Flag',values=['F','L','I'])
IpoSeoNum.columns               =   [IPO_Flag+'_'+Date_Type+'_Sample' \
                                     for IPO_Flag, Date_Type in \
                                     zip(IpoSeoNum.columns.get_level_values(1), \
                                         IpoSeoNum.columns.get_level_values(0))]
IpoSeoNum                       =   IpoSeoNum.merge(right=IpoSeoNum_All,how='outer', \
                                                    left_index=True,right_index=True)
pickle.dump(IpoSeoNum,open(DataFolder+'IpoSeoNum.p','wb'))

## Drop the IPO Deals
TempInd_Drop                    =   (TempSample['IPO_Flag']=='Yes')
TempSample                      =   TempSample[~TempInd_Drop]
### Output the Sample

## Reset the Index
TempSample.reset_index(inplace=True)

## List of Variables for Output Sample
VarList_ID                      =   ['IssueID','IssueID_ObsNum']+ \
                                    [x+y \
                                     for x in ['FilingDate','LaunchDate','IssueDate'] \
                                     for y in ['','Flag','_Year','_Quarter','_Month']]+ \
                                    [x+'_'+y \
                                     for x in ['GapDays','GapBusDays'] \
                                     for y in ['F2I','L2I','F2L']]+ \
                                    ['SIC','FF5_Name','FF5_Code','FF10_Name','FF10_Code']+ \
                                    ['Issuer','Nation','Exchange', \
                                     'CUSIP', 'CUSIP_9digit', \
                                     'CUSIP_1_6', 'CUSIP_7_8', 'CUSIP_8digit', 'CUSIP_DigitNum', \
                                     'TickerSymbol']+ \
                                    ['DaysInRegistration','RightsOfferFlag','Rule415ShelfFlag', \
                                     'ProceedsUse']
VarList_CashFlow                =   ['PrincipalAmount','FiledAmount','ProceedsAmount']
VarList_RealCashFlow            =   ['Real'+x for x in VarList_CashFlow]
VarList_Others                  =   ['FiledShares', 'OfferedTotalShares', \
                                     'OfferedPrimaryShares','OfferedSecondaryShares', \
#                                     'OfferPrice', \
                                     'OfferAvgPrice', \
                                     'OfferedPrimarySharesPct','ShareType', \
                                     'TotalAsset_AfterOffering','TotalAsset_BeforeOffering', \
                                     'TotalDebt', 'TotalEquity','MarketValue', \
                                     'TotalShares_BeforeOffering', 'TotalShares_AfterOffering', \
                                     'InsiderSharesPct_BeforeOffering', \
                                     'PrimarySharesPct_BeforeOffering','PrimarySharesPct_AfterOffering', \
                                     'Leverage_BeforeOffering', 'Leverage_AfterOffering']

## Nominal to Real
TempSample                      =   TempSample.merge(right=PPI_M,how='left', \
                                                     left_on='IssueDate_Month',right_index=True)
TempSample[VarList_RealCashFlow]=   TempSample[VarList_CashFlow].divide(TempSample['ppi'],axis=0)

pickle.dump(TempSample[VarList_ID+VarList_CashFlow+VarList_RealCashFlow+VarList_Others], \
            open(DataFolder+'IssuanceSample.p','wb'))
# End of Section: 
###############################################################################
