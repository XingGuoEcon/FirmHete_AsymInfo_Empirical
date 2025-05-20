
#%% Load in the packages
from _Public import *

#%% Load in the data 
DataFolder = "Micro_data\\datasets\\SDC\\"
# Return history panels
RetPanel = pd.read_pickle(DataFolder+"SDC_Ret.p")
# Estimated Alpha and Beta 
SDC_AlphaBeta = pd.read_pickle(DataFolder+"SDC_AlphaBeta.p")


#%% Compute the Abnormal Return History 
### Functions  
## Given one factor model specification, compute the Abnormal Return History
def TempFun_ComputeAbRet(DS, AlphaBeta, EventDateType='F', \
                         RetVar='DiffLogPrice', \
                         FactorVarList=['mktrf', 'smb', 'hml', 'rmw', 'cma'], \
                         RfVar='rf', \
                         HistWindow=(-100, 160), \
                         RelativeDateType='Adj', MinObs=30):
    
    # Only keep the observations within the specified window
    RelDateVar      =   EventDateType+'Date_'+RelativeDateType
    TempVarList     =   ['IssueID', 'Date', RelDateVar, RetVar, RfVar] + FactorVarList
    # TempInd         =   DS[RelDateVar].between(HistWindow[0], HistWindow[1])
    # TempDS = DS.loc[TempInd, ['IssueID', RelDateVar, RetVar, RfVar] + FactorVarList].dropna()
    TempDS = DS.loc[:, TempVarList].dropna()
    # Incoporate the Alpha and Beta information
    TempDS = TempDS.merge(AlphaBeta.reset_index(), how='left', on='IssueID')
    TempDS.loc[TempDS['Obs']<MinObs, ['Alpha']+['Beta_'+vv for vv in FactorVarList]] = np.nan
    # Compute the Abnormal Return
    TempDS['AbRet'] = TempDS[RfVar] + TempDS['Alpha'] 
    for vv in FactorVarList:
        TempDS['AbRet'] += TempDS['Beta_'+vv] * TempDS[vv]
    TempDS['AbRet'] = TempDS[RetVar] - TempDS['AbRet'] 
    TempDS = TempDS.loc[:, ['IssueID', 'Date', RelDateVar, 'AbRet']] \
                .rename(columns={RelDateVar: 'RelDate'}) \
                .set_index(['IssueID', 'Date']).sort_index()
    
    return TempDS

def TempFun_ComputeAbRet_AllEventType(DS, AlphaBeta_AllEventType, \
                         RetVar='DiffLogPrice', \
                         FactorVarList=['mktrf', 'smb', 'hml', 'rmw', 'cma'], \
                         RfVar='rf', \
                         HistWindow=(-100, 160), \
                         RelativeDateType='Adj', MinObs=30):
    def tempfun(EventType):
        return TempFun_ComputeAbRet(DS, AlphaBeta_AllEventType.loc[:, EventType], EventDateType=EventType, \
                                    RetVar=RetVar, FactorVarList=FactorVarList, RfVar=RfVar, \
                                    HistWindow=HistWindow, RelativeDateType=RelativeDateType, MinObs=MinObs)
    TempDS = pd.concat([tempfun(EventType) for EventType in ['F', 'L', 'I']], axis=1, join='outer', keys=['F', 'L', 'I']).sort_index()
    
    return TempDS
    

InputList = ['RetVar','FactorVarList','RfVar', 'RelativeDateType']
FactorModelList = SDC_AlphaBeta['RegResultDict'].keys() 
RetPanelDict = {}
for FactorModel in FactorModelList:
    print(f"Computing the Abnormal Return History with facotr model: {FactorModel}")
    RetPanelDict[FactorModel] = TempFun_ComputeAbRet_AllEventType(RetPanel, SDC_AlphaBeta['RegResultDict'][FactorModel], \
                                                                  **{xx: SDC_AlphaBeta['RegSetupDict'][FactorModel][xx] for xx in InputList}, \
                                                                  HistWindow=(-160, 160), MinObs=30)

pickle.dump(RetPanelDict, open(DataFolder+"SDC_AbRet_Panel.p", 'wb')) 


#%% Compute the cumulated abnormal return 

### Load in the data of abnormal return panel 
# RetPanelDict = pd.read_pickle(DataFolder+"SDC_AbRet_Panel.p")

# RetPanel = pd.concat(RetPanelDict, axis=1, join='outer')
# AccRet = RetPanel.loc[idx[:, [0,1]], :].groupby('IssueID').sum() 
# AccRet_NA = RetPanel.loc[idx[:, [0,1]], :].groupby('IssueID').count() 
# for vv in AccRet_NA.columns:
#     AccRet.loc[AccRet_NA[vv]==0, vv] = np.nan

# AccRet.rename(columns={'Ret': 'AccRet', 'AbRet': 'AccAbRet'}, level=2, inplace=True)

# AccRet.columns = ['_'.join(vv) for vv in AccRet.columns]

# pickle.dump(AccRet, open(DataFolder+"SDC_AccAbRet.p", 'wb')) 
# #%% Abnormal Return History


# ### Setup

# ## Read-in Data
# DataFolder      =   "..\\temp\\"
# RegSample       =   pickle.load(open(DataFolder+'SDC_Ret.p','rb'))
# RegResult       =   pickle.load(open(DataFolder+'SDC_AlphaBeta.p','rb'))

# ## Window, Minimum Observations for Effective Information
# # Window for Event Study
# StartEndDate    =   [-100,160]
# # Minimum Obs. for the Alpha/Beta to be Effective
# MinObs          =   100


# ### Extract the List of IssueID which has good Coverage of the Event Window

# ## Temporary Function Computing the Start/End day and number of days before/after the event date
# def TempFun_DateSumStat(DS,StartEndDate,DateType):
#     TempDateVar     =   DateType+'Date_Adj'
#     TempRetVar      =   'Ret_Adj'
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
# DS_Ret_Info     =   TempFun_DateSumStat(RegSample,StartEndDate,'F') \
#                     .merge(right=TempFun_DateSumStat(RegSample,StartEndDate,'L'), \
#                            how='outer',on='IssueID') \
#                     .merge(right=TempFun_DateSumStat(RegSample,StartEndDate,'I'), \
#                            how='outer',on='IssueID')
# GoodIssueID     =   {}      
# for ILF in ['F','L','I']:
#     TempList        =   DS_Ret_Info.loc[ ( DS_Ret_Info[ILF+'_MinDate']<=StartEndDate[0] ) & \
#                                          ( DS_Ret_Info[ILF+'_MaxDate']>=StartEndDate[1] ) & \
#                                          ( DS_Ret_Info[ILF+'_Obs_L']>=2/3*np.abs(StartEndDate[0]) ) & \
#                                          ( DS_Ret_Info[ILF+'_Obs_R']>=2/3*np.abs(StartEndDate[1]) ), \
#                                         'IssueID'].tolist()
#     GoodIssueID[ILF]=   TempList

# ### Long-Table: Compute the Abnormal History

# ## Eliminate the Irrelevant Periods
# TempInd             =   ( ( RegSample['FDate_Adj']>=StartEndDate[0] ) & \
#                           ( RegSample['FDate_Adj']<=StartEndDate[1] ) ) | \
#                         ( ( RegSample['LDate_Adj']>=StartEndDate[0] ) & \
#                           ( RegSample['LDate_Adj']<=StartEndDate[1] ) ) | \
#                         ( ( RegSample['IDate_Adj']>=StartEndDate[0] ) & \
#                           ( RegSample['IDate_Adj']<=StartEndDate[1] ) )
# SDC_AbRet_Long      =   RegSample[TempInd]

# ## Merge with the Alpha/Beta Information
# SDC_AbRet_Long      =   SDC_AbRet_Long.merge(right=RegResult,how='left', \
#                                              left_on='IssueID',right_on='IssueID')

# ## Calculate the Excess Return in the Relevant Periods

# AbRetVarList        =   []
# for Type_Date in ['F','L','I']:
#     Var_Date        =   Type_Date+'Date_Adj'
#     TempInd_1       =   ( ( SDC_AbRet_Long[Var_Date]>=StartEndDate[0] ) & \
#                           ( SDC_AbRet_Long[Var_Date]<=StartEndDate[1] ) )
#     # Based on Event Specific Alpha/Beta
#     for Type_Adj in ['NAdj','Adj']:
#         Var_ExRet           =   'ExRet_'+Type_Adj
#         Var_ExSpRet         =   'ExSpRet_'+Type_Adj
#         Var_AbRet           =   Type_Date+'_AbRet_'+Type_Adj
        
#         Var_Obs             =   Type_Date+'_Obs_'+Type_Adj
#         Var_Alpha           =   Type_Date+'_Alpha_'+Type_Adj
#         Var_Beta            =   Type_Date+'_Beta_'+Type_Adj
        
#         SDC_AbRet_Long[Var_AbRet] \
#                             =   SDC_AbRet_Long[Var_ExRet]- \
#                                 SDC_AbRet_Long[Var_Alpha]- \
#                                 SDC_AbRet_Long[Var_Beta]*SDC_AbRet_Long[Var_ExSpRet]
#         TempInd_2           =   SDC_AbRet_Long[Var_Obs]>=MinObs
        
#         SDC_AbRet_Long.loc[~(TempInd_1 & TempInd_2),Var_AbRet]    =   np.nan
        
#         AbRetVarList.append(Var_AbRet)
#     # Based on the Unified Alpha/Beta    
#     for Type_Adj in ['NAdj','Adj']:
#         Var_ExRet           =   'ExRet_'+Type_Adj
#         Var_ExSpRet         =   'ExSpRet_'+Type_Adj
#         Var_AbRet           =   Type_Date+'_UniAbRet_'+Type_Adj
        
#         Var_Obs             =   'I'+'_Obs_'+Type_Adj
#         Var_Alpha           =   'I'+'_Alpha_'+Type_Adj
#         Var_Beta            =   'I'+'_Beta_'+Type_Adj
        
#         SDC_AbRet_Long[Var_AbRet] \
#                             =   SDC_AbRet_Long[Var_ExRet]- \
#                                 SDC_AbRet_Long[Var_Alpha]- \
#                                 SDC_AbRet_Long[Var_Beta]*SDC_AbRet_Long[Var_ExSpRet]
#         TempInd_2           =   SDC_AbRet_Long[Var_Obs]>=MinObs
        
#         SDC_AbRet_Long.loc[~(TempInd_1 & TempInd_2),Var_AbRet]    =   np.nan
        
#         AbRetVarList.append(Var_AbRet)

# IDVarList           =   ['IssueID','FDate_Adj','LDate_Adj','IDate_Adj']

# SDC_AbRet_Long      =   SDC_AbRet_Long[IDVarList+AbRetVarList].reset_index(drop=True)

# pickle.dump(SDC_AbRet_Long,open(DataFolder+"SDC_AbRet_Long.p",'wb'))


# ### Wide-Table: Abnormal History at each Relative Date and Accumulated Abnormal Return

# ## Setup
# # Window for Calculating Accumulated Abnormal Return
# WindowList      =   [[StartEndDate[0],x] for x in range(StartEndDate[0],StartEndDate[1]+1)]+ \
#                     [[0,x] for x in range(0,10+1)]+ \
#                     [[-x,x] for x in range(1,10+1)]

# ## Computation
# AbRetDict       =   {}
# for Suffix in ['F','L','I']:
#     # Setup
#     RelDateVar          =   Suffix+'Date_Adj'
    
#     # Eliminate Irrelevant Relative Periods
#     TempInd             =   ( SDC_AbRet_Long[RelDateVar]>=StartEndDate[0] ) & \
#                             ( SDC_AbRet_Long[RelDateVar]<=StartEndDate[1] )
    
#     InitiateFlag        =   True
#     for AbRet in ['AbRet','UniAbRet']:
#         AbRetVar            =   Suffix+'_'+AbRet+'_Adj'
#         TempDS              =   SDC_AbRet_Long.loc[TempInd,['IssueID',RelDateVar,AbRetVar]] \
#                                 .sort_values(['IssueID',RelDateVar]).reset_index(drop=True)
#         # Transform the Long Table to Wide Table
#         TempDS              =   TempDS.pivot(index='IssueID',columns=RelDateVar,values=AbRetVar)
#         TempDS.columns      =   [Suffix+'_'+AbRet+'_'+str(int(x)) for x in TempDS.columns]
#         TempDS.dropna(how='all',inplace=True)
#         # Generate the Accumulated Abnormal Return
#         for Window in WindowList:
#             WinStart            =   Window[0]
#             WinEnd              =   Window[1]
#             ColList             =   [Suffix+'_'+AbRet+'_'+str(int(x)) for x in range(WinStart,WinEnd+1)]
#             VarName             =   Suffix+'_Acc'+AbRet+'_'+str(WinStart)+'_'+str(WinEnd)
#             TempDS[VarName]     =   TempDS[ColList].sum(axis=1)/TempDS[ColList].count(axis=1)* \
#                                     ( WinEnd-WinStart+1 )
#         if InitiateFlag:
#             TempAbRetDS     =   TempDS.sort_index().copy()
#             InitiateFlag    =   False
#         else:
#             TempAbRetDS     =   TempAbRetDS.merge(right=TempDS,how='outer', \
#                                                   left_index=True,right_index=True)
        
    
#     AbRetDict[Suffix]   =   TempAbRetDS.copy()

# ## Merged Data Set
# # Extract the List of IssueID which has good Coverage of the Event and Factor Regression 
# for FLI in ['F','L','I']:
#     GoodIssueID[FLI]    =   list( set(AbRetDict[FLI].index.tolist()) & set(GoodIssueID[FLI]) )
# # Data Sets Merge
# SDC_AbRet_Wide  =   AbRetDict['F'].loc[GoodIssueID['F'],:] \
#                     .merge(right=AbRetDict['L'].loc[GoodIssueID['L'],:], \
#                            how='outer',left_index=True,right_index=True) \
#                     .merge(right=AbRetDict['I'].loc[GoodIssueID['I'],:], \
#                            how='outer',left_index=True,right_index=True) \
#                     .reset_index()

# ## Save the Data Set
# pickle.dump(SDC_AbRet_Wide,open(DataFolder+'SDC_AbRet_Wide.p','wb'))
# # End of Section:
# ###############################################################################


# #%% Summary Statistics of the Abnormal Return Around the Filing/Issuance Date


# ### Setup

# ## Construct the Sample
# DataFolder          =   "..\\temp\\"
# SDC_AbRet_Wide      =   pickle.load(open(DataFolder+"SDC_AbRet_Wide.p",'rb'))
# SDC_IssuanceInfo    =   pickle.load(open(DataFolder+"SDC_IssuanceInfo.p",'rb'))
# Sample              =   SDC_AbRet_Wide.merge(SDC_IssuanceInfo,how='left', \
#                                              left_on='IssueID',right_on='IssueID')

# ## Preliminaries 
# StartEndDate        =   [-100,160]
# WindowList          =   [[StartEndDate[0],x] for x in range(StartEndDate[0],StartEndDate[1]+1)]+ \
#                         [[0,x] for x in range(0,10+1)]+[[-x,x] for x in range(1,10+1)]

# AbRetVarList        =   ['AbRet_'+str(int(x)) for x in range(StartEndDate[0],StartEndDate[1]+1)]
# AccAbRetVarList     =   ['AccAbRet_'+str(int(x[0]))+'_'+str(int(x[1])) for x in WindowList]

# ## Temporary Functions
# # Weighted Average
# def TempFun_WM(DS,VarList,WeightVar):
#     Temp_Num        =   DS[VarList].multiply(DS[WeightVar],axis=0).sum(axis=0)
#     Temp_DeNum      =   ( ~pd.isna(DS[VarList]) ).multiply(DS[WeightVar],axis=0).sum(axis=0)
#     WM              =   Temp_Num.divide(Temp_DeNum,axis=0)
#     WM.name         =   'WMean'
    
#     return WM
# # Unit-level Summary Statistics
# def TempFun_UnitSumStat(DS,VarList):
#     Stat_1          =   DS[VarList].quantile(q=[0.01,0.1,0.25,0.5,0.75,0.9,0.99])
#     Stat_1.index    =   ['Q'+str(int(x*100)) for x in Stat_1.index]
    
#     Stat_2          =   DS[VarList].apply(['min','max','count','mean','std'])
#     Stat_2.rename(index={'min': 'Min','max': 'Max','count': 'Obs', \
#                          'mean': 'Mean', 'std': 'Std'},inplace=True)
    
#     Stat_3          =   ( DS[VarList]<0 ).sum().to_frame('NegPct').T
    
#     SumStat         =   pd.concat([Stat_1,Stat_2,Stat_3],axis=0,join='outer')
#     SumStat.loc['NegPct',:] \
#                     =   SumStat.loc['NegPct',:]/SumStat.loc['Obs',:]
#     return SumStat
# # Aggregated Summary Statistics
# def TempFun_AggStat(DS,VarList,CalDateVar,WeightVar):
#     Stat_1          =   DS[VarList+[CalDateVar]].groupby(CalDateVar).mean()
#     AggStat_1       =   TempFun_UnitSumStat(Stat_1,VarList)
#     IndexDict       =   {x: x+'_NQ' for x in AggStat_1.index}
#     AggStat_1.rename(index=IndexDict,inplace=True)
        
#     Stat_2          =   DS.groupby(CalDateVar).apply(TempFun_WM,VarList,WeightVar)
#     AggStat_2       =   TempFun_UnitSumStat(Stat_2,VarList)
#     IndexDict       =   {x: x+'_WQ' for x in AggStat_2.index}
#     AggStat_2.rename(index=IndexDict,inplace=True)
    
#     AggQ            =   pd.concat([Stat_1,Stat_2],axis=0,join='outer',keys=['N','W'])
    
#     AggStat_3       =   TempFun_UnitSumStat(DS,VarList)
#     AggStat_4       =   TempFun_WM(DS,VarList,WeightVar).to_frame().T
    
#     AggStat         =   pd.concat([AggStat_1,AggStat_2,AggStat_3,AggStat_4], \
#                                   axis=0,join='outer')
#     return AggStat, AggQ


# ### Calculate the Summary Statistics

# ## Setup
# EventDictList       =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
#                          {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
#                          {'Suffix': 'I', 'DateVar': 'IssueDate'}]

# ## Compute the Abnormal Return within the Window History
# WinHistDict         =   {}
# CalHistDict         =   {}
# WinHistSumStatDict  =   {}
# for EventDict in EventDictList:
#     Suffix              =   EventDict['Suffix']
#     WeightVar           =   'RealProceedsAmount'
#     CalDateVar          =   EventDict['DateVar']+'_Quarter'
    
#     Temp_AbRetVarList   =   [Suffix+'_'+x for x in AbRetVarList]
#     Temp_AccAbRetVarList=   [Suffix+'_'+x for x in AccAbRetVarList]
#     Temp_VarList        =   Temp_AbRetVarList+Temp_AccAbRetVarList
    
#     AggStat,AggStat_Q   =   TempFun_AggStat(Sample,Temp_VarList,CalDateVar,WeightVar)
    
#     # Sum-Stat Along the Window History
#     TempDF              =   AggStat[Temp_AbRetVarList].T
#     TempDF.index        =   [int(x.split('_')[2]) for x in TempDF.index]
#     TempDF.columns      =   [x+'_'+Suffix for x in TempDF.columns]
#     TempDF.reset_index(inplace=True)
#     TempDF.rename(columns={'index': 'EventDate'},inplace=True)
    
#     WinHistDict[Suffix] =   TempDF
    
#     # Sum-Stat Along the Calendar History
#     TempDF              =   AggStat_Q[Temp_AccAbRetVarList].reset_index()
#     TempDF.rename(columns={'level_0': 'Type',CalDateVar:'Date'},inplace=True)
#     TempDF              =   TempDF.pivot(index='Date',columns='Type',values=Temp_AccAbRetVarList)
#     TempDF.columns      =   [x[0]+'_'+x[1] for x in TempDF.columns]
#     TempDF.reset_index(inplace=True)
     
#     CalHistDict[Suffix] =   TempDF
    
#     # Cross-time Aggregated Sum-Stat
#     WinHistSumStatDict[Suffix] \
#                         =   AggStat[Temp_AccAbRetVarList].T

# ## Merge the Issuance Event Study and Filing Event Study
# # Window History
# WinHist             =   WinHistDict['F'] \
#                         .merge(right=WinHistDict['L'],how='outer',on='EventDate') \
#                         .merge(right=WinHistDict['I'],how='outer',on='EventDate')
# pickle.dump(WinHist,open(DataFolder+'SDC_AbRet_WinHist.p','wb'))
# # Summary of Window History
# WinHistSumStat      =   pd.concat([WinHistSumStatDict['F'], \
#                                    WinHistSumStatDict['L'], \
#                                    WinHistSumStatDict['I']], \
#                                   join='outer',axis=0)
# pickle.dump(WinHistSumStat,open(DataFolder+'SDC_AbRet_WinHist_SumStat.p','wb'))
# # Calendar History
# CalHist             =   CalHistDict['F'] \
#                         .merge(right=CalHistDict['L'],how='outer',on='Date') \
#                         .merge(right=CalHistDict['I'],how='outer',on='Date')

# pickle.dump(CalHist,open(DataFolder+'SDC_AbRet_CalHist.p','wb'))
# # End of Section:
# ###############################################################################