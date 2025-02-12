# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Sun Apr 14 14:44:29 2019
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

#%% Temporary Function for Calculating the Summary Statistics

def TempFun_UnitSumStat(DS,EventDict,DateLimit,GroupVar,SuffixVarList, \
                        NoSuffixVarList=[],CutoffList=[0],SuffixGroupVarFlag=True):

    TempSuffix  =   EventDict['Suffix']
    TempDateVar =   EventDict['DateVar']
    
    TempInd     =   ( DS[TempDateVar]>=DateLimit[0] ) & (DS[TempDateVar]<=DateLimit[1])
    TempVarList =   [TempSuffix+'_'+x for x in SuffixVarList]+ \
                    NoSuffixVarList
    PctVarList  =   ['Pct(<='+str(x)+')' for x in CutoffList]
    QuantList   =   [0.05,0.25,0.5,0.75,0.95]
    if GroupVar=='':
        TempDS      =   DS.loc[TempInd,TempVarList]
        TempSumStat =   TempDS[TempVarList].describe(percentiles=QuantList) \
                        .rename(index={'count': 'Obs','mean': 'Mean','std': 'Std', \
                                       'min': 'Min','max': 'Max'})
        PctSumStat  =   pd.concat([TempDS[TempVarList] \
                                   .apply(lambda x: (x<=CutoffList[ii]).sum()) \
                                   for ii in range(len(CutoffList))],axis=1, \
                                  keys=['Pct(<='+str(x)+')' for x in CutoffList]) \
                        .T
        TempSumStat =   TempSumStat.append(PctSumStat)
        TempSumStat.loc[PctVarList,:] \
                    =   TempSumStat.loc[PctVarList,:]/TempSumStat.loc['Obs',:]*100
                    
        TempSumStat.columns \
                    =   pd.MultiIndex.from_tuples([(x,0) \
                                                   for x in TempSumStat.columns])
        TempGroupVar=   'FullSample'
    else:
        if SuffixGroupVarFlag:
            TempGroupVar    =   TempSuffix+'_'+GroupVar
        else:
            TempGroupVar    =   GroupVar
        TempDS      =   DS.loc[TempInd,TempVarList+[TempGroupVar]]
        TempSumStat =   TempDS.groupby(TempGroupVar)[TempVarList].describe(percentiles=QuantList) \
                        .T.unstack(level=0).swaplevel(i=0,j=1,axis=1) \
                        .rename(index={'count': 'Obs','mean': 'Mean','std': 'Std', \
                                       'min': 'Min','max': 'Max'})
    
        PctSumStat  =   pd.concat([TempDS.groupby(TempGroupVar)[TempVarList] \
                                   .apply(lambda x: (x<=CutoffList[ii]).sum()) \
                                   for ii in range(len(CutoffList))],axis=1, \
                                  keys=['Pct(<='+str(x)+')' for x in CutoffList]) \
                        .T.unstack(level=1).swaplevel(i=0,j=1,axis=1)
        
        
        TempSumStat =   TempSumStat.append(PctSumStat)
        TempSumStat.loc[PctVarList,:] \
                    =   TempSumStat.loc[PctVarList,:]/TempSumStat.loc['Obs',:]*100
    
        TempGroupVar=   GroupVar
 
    TempSumStat.loc['T-Stat',:] \
                =   TempSumStat.loc['Mean',:]/ \
                    (TempSumStat.loc['Std',:]/np.sqrt(TempSumStat.loc['Obs',:]))
    TempSumStat =   TempSumStat.T
     
    TempDateTag =   str(DateLimit[0].year)+'-'+str(DateLimit[1].year)
     
    TempSumStat.columns     =   pd.MultiIndex.from_tuples([(TempSuffix,TempDateTag,TempGroupVar,x) \
                                                           for x in TempSumStat.columns])
    TempSumStat =   TempSumStat.unstack(level=1).swaplevel(i=3,j=4,axis=1)
    TempSumStat.rename(index={TempSuffix+'_'+x: x for x in SuffixVarList},inplace=True)
     
    return TempSumStat

# End of Section:
###############################################################################
    
#%% Generate the Summary Statistics
'''
This section is designed to 
'''
DataFolder      =   "..\\temp\\"


### Construct the Sample

## Load-in the Data
RegSample       =   pickle.load(open(DataFolder+"RegSample.p",'rb'))
#RegSample       =   RegSample[~pd.isna(RegSample['F_AccAbRet_-1_1'])]

## Preliminary Setup
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]

## Generate the Group Classification Dummy
# Monetary Shock Periods
MsVarList       =   ['Pre_MsRR','30d_MsRR','90d_MsRR', \
                     'Pre_MsWideHF','30d_MsWideHF','90d_MsWideHF']
for EventDict in EventDictList:
    for MsVar in MsVarList:
        TempVar         =   EventDict['Suffix']+'_'+MsVar
        TempNegFlagVar  =   EventDict['Suffix']+'_'+MsVar+'_NegFlag'
        RegSample.loc[RegSample[TempVar]<=0,TempNegFlagVar] \
                        =   1
        RegSample.loc[RegSample[TempVar]>0,TempNegFlagVar] \
                        =   0
        RegSample.loc[pd.isna(RegSample[TempVar]),TempNegFlagVar] \
                        =   np.nan
# Business Cycle Periods (GDP Growth)
CycleVarList    =   ['GdpGrowth','UnemploymentRate','RecessionFlag']
CutoffList      =   [3.3,5.6,0.5]
for EventDict in EventDictList:
    for ii in range(len(CycleVarList)):
        CycleVar    =   CycleVarList[ii]
        Cutoff      =   CutoffList[ii]
        for MsLagVar in MsVarList+['Lag0','Lag1','Lag2']:
            TempVar         =   EventDict['Suffix']+'_'+MsLagVar+'_'+CycleVar
            TempNegFlagVar  =   TempVar+'_LowFlag'
            TempInd         =   RegSample[TempVar]<Cutoff
            RegSample.loc[TempInd,TempNegFlagVar] \
                            =   1
            RegSample.loc[~TempInd,TempNegFlagVar] \
                            =   0
            RegSample.loc[pd.isna(RegSample[TempVar]),TempNegFlagVar] \
                            =   np.nan


### Calculate the Cross-sectional Statistics


## Setup
AccRetVarList       =   ['AccRet_'+str(-x)+'_'+str(x) for x in range(1,11)]+ \
                        ['AccRet_'+str(0)+'_'+str(x) for x in range(1,11)]
AccRetCutoffList    =   [0]
AccAbRetVarList     =   ['Acc'+AbRet+'_'+str(-x)+'_'+str(x) \
                         for AbRet in ['AbRet','UniAbRet'] for x in range(1,11)]+ \
                        ['Acc'+AbRet+'_'+str(0)+'_'+str(x) \
                         for AbRet in ['AbRet','UniAbRet'] for x in range(1,11)]
AccAbRetCutoffList  =   [0]
GapDaysVarList      =   ['GapBusDays_F2I','GapBusDays_L2I','GapBusDays_F2L']
GapDaysCutoffList   =   [0,1,5,10,20,65,133,265]
SuffixGroupVarList  =   [MsVar+'_NegFlag' for MsVar in MsVarList]+ \
                        [LagVar+'_'+CycleVar+'_LowFlag' \
                         for LagVar in ['Lag0','Lag1'] for CycleVar in CycleVarList]
NoSuffixGroupVarList=   ['PrimaryFlag','ShelfIssueFlag']
SamplePeriodList    =   [[datetime.date(1970,1,1),datetime.date(1999,12,31)], \
                         [datetime.date(1983,1,1),datetime.date(1999,12,31)], \
                         [datetime.date(1994,1,1),datetime.date(1999,12,31)], \
                         [datetime.date(1970,1,1),datetime.date(2007,12,31)], \
                         [datetime.date(1983,1,1),datetime.date(2007,6,1)], \
                         [datetime.date(1994,1,1),datetime.date(2007,6,1)], \
                         [datetime.date(1983,1,1),datetime.date(1993,12,31)], \
                         [datetime.date(2000,1,1),datetime.date(2007,6,1)]]

## Computation
CroSecSumStatDict   =   {}
# Returns
InitiateFlag    =   True
for EventDict in EventDictList:
    for DateLimit in SamplePeriodList:
        for GroupVar in ['']+SuffixGroupVarList+NoSuffixGroupVarList:
            if GroupVar in NoSuffixGroupVarList:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,AccRetVarList, \
                                                        CutoffList=AccRetCutoffList, \
                                                        SuffixGroupVarFlag=False)
            else:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,AccRetVarList, \
                                                        CutoffList=AccRetCutoffList, \
                                                        SuffixGroupVarFlag=True)
            
            if InitiateFlag:
                SumStat         =   TempSumStat
                InitiateFlag    =   False
            else:
                SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                                  left_index=True,right_index=True)
CroSecSumStatDict['AccRet']  =   SumStat.T
# Abnormal Returns
InitiateFlag    =   True
for EventDict in EventDictList:
    for DateLimit in SamplePeriodList:
        for GroupVar in ['']+SuffixGroupVarList+NoSuffixGroupVarList:
            if GroupVar in NoSuffixGroupVarList:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,AccAbRetVarList, \
                                                        CutoffList=AccAbRetCutoffList, \
                                                        SuffixGroupVarFlag=False)
            else:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,AccAbRetVarList, \
                                                        CutoffList=AccAbRetCutoffList, \
                                                        SuffixGroupVarFlag=True)
            
            if InitiateFlag:
                SumStat         =   TempSumStat
                InitiateFlag    =   False
            else:
                SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                                  left_index=True,right_index=True)
CroSecSumStatDict['AccAbRet']  =   SumStat.T
# Gap Days
InitiateFlag    =   True
for EventDict in EventDictList:
    for DateLimit in SamplePeriodList:
        for GroupVar in ['']+SuffixGroupVarList+NoSuffixGroupVarList:
            if GroupVar in NoSuffixGroupVarList:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,[], \
                                                        NoSuffixVarList=GapDaysVarList, \
                                                        CutoffList=GapDaysCutoffList, \
                                                        SuffixGroupVarFlag=False)
            else:
                TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit,GroupVar,[], \
                                                        NoSuffixVarList=GapDaysVarList, \
                                                        CutoffList=GapDaysCutoffList, \
                                                        SuffixGroupVarFlag=True)
            
            if InitiateFlag:
                SumStat         =   TempSumStat
                InitiateFlag    =   False
            else:
                SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                                  left_index=True,right_index=True)
CroSecSumStatDict['GapBusDays']   =   SumStat.T



### Calculate the Cross-Time Statistics

## Setup
AccAbRetVarList     =   ['AccAbRet_-1_1','AccAbRet_-2_2']
GapDaysVarList      =   ['GapBusDays_F2I','GapBusDays_L2I','GapBusDays_F2L']
OtherNoSuffixVarList=   ['ShelfIssueFlag','PrimarySecondaryFlag','OnlySecondaryFlag']
DateLimit           =   [datetime.date(1960,1,1),datetime.date(2016,6,1)]

## Computation
InitiateFlag        =   True
for EventDict in EventDictList:
    TempSumStat     =   TempFun_UnitSumStat(RegSample,EventDict,DateLimit, \
                                            EventDict['DateVar']+'_Year', \
                                            AccAbRetVarList, \
                                            NoSuffixVarList=GapDaysVarList+OtherNoSuffixVarList, \
                                            CutoffList=GapDaysCutoffList, \
                                            SuffixGroupVarFlag=False)
    if InitiateFlag:
        SumStat         =   TempSumStat
        InitiateFlag    =   False
    else:
        SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                          left_index=True,right_index=True)

CroTimeSumStat      =   SumStat.T.reset_index(level=[1,2],drop=True) \
                        .unstack(level=[0,2]).swaplevel(i=0,j=1,axis=1)

# End of Section:
###############################################################################

#%% Produce the Tables and Graphs
                        
TableFolder     =   "..\\results\\TableGraph\\SumStat\\"


### Cross-Sectional Results: AccRet

## Setup
ExcelWriter     =   pd.ExcelWriter(TableFolder+'SumStat_AccRet.xlsx')                        
TempVarList     =   ['AccRet_'+str(-x)+'_'+str(x) for x in range(1,5)]+ \
                    ['AccRet_'+str(0)+'_'+str(x) for x in range(1,5)]
TempStatList    =   ['Min','5%','25%','50%','75%','95%','Max','Mean','Std','Pct(<=0)','Obs','T-Stat']
TempMultiIndex  =   pd.MultiIndex.from_tuples([(x,y) for x in TempVarList for y in TempStatList])

TempSampleListDict \
                =   {'F': ['1994-1999','1983-1999','2000-2007', \
                           '1970-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'L': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'I': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'] \
                    }
## Output Different Tables
# Unconditional Moments
TempTable       =   CroSecSumStatDict['AccRet'].loc[idx[:,:,'FullSample',:,:],:] \
                    .reset_index(level=[2,3],drop=True) \
                    .unstack(level=[0,1]) \
                    .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                    .reindex(TempMultiIndex)
for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    TempTable[Suffix][TempSampleListDict[Suffix]] \
    .to_excel(ExcelWriter,sheet_name=Suffix+'_Unconditional',float_format='%.2f')
    
# Conditional Moments
for TempGroupVar in NoSuffixGroupVarList+SuffixGroupVarList:
    TempTable       =   CroSecSumStatDict['AccRet'].loc[idx[:,:,TempGroupVar,:,:],:] \
                        .reset_index(level=[2],drop=True) \
                        .unstack(level=[0,1,2]) \
                        .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                        .reindex(TempMultiIndex)
    for EventDict in EventDictList:
        Suffix          =   EventDict['Suffix']
        TempColList     =   pd.MultiIndex.from_tuples( \
                            [(x,y) \
                             for x in TempSampleListDict[Suffix] \
                             for y in TempTable.columns.get_level_values(2).unique().tolist()])
        TempTable[Suffix].reindex(columns=TempColList) \
        .to_excel(ExcelWriter,sheet_name=Suffix+'_'+TempGroupVar,float_format='%.2f')
# Save the File
ExcelWriter.save()  


### Cross-Sectional Results: AccAbRet

## Setup
ExcelWriter     =   pd.ExcelWriter(TableFolder+'SumStat_AccAbRet.xlsx')                        
TempVarList     =   ['Acc'+AbRet+'_'+str(-x)+'_'+str(x) \
                     for AbRet in ['AbRet','UniAbRet'] for x in range(1,5)]+ \
                    ['Acc'+AbRet+'_'+str(0)+'_'+str(x) \
                     for AbRet in ['AbRet','UniAbRet'] for x in range(1,5)]
TempStatList    =   ['Min','5%','25%','50%','75%','95%','Max','Mean','Std','Pct(<=0)','Obs','T-Stat']
TempMultiIndex  =   pd.MultiIndex.from_tuples([(x,y) for x in TempVarList for y in TempStatList])

TempSampleListDict \
                =   {'F': ['1994-1999','1983-1999','2000-2007', \
                           '1970-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'L': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'I': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'] \
                    }
## Output Different Tables
# Unconditional Moments
TempTable       =   CroSecSumStatDict['AccAbRet'].loc[idx[:,:,'FullSample',:,:],:] \
                    .reset_index(level=[2,3],drop=True) \
                    .unstack(level=[0,1]) \
                    .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                    .reindex(TempMultiIndex)
for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    TempTable[Suffix][TempSampleListDict[Suffix]] \
    .to_excel(ExcelWriter,sheet_name=Suffix+'_Unconditional',float_format='%.2f')
    
# Conditional Moments
for TempGroupVar in NoSuffixGroupVarList+SuffixGroupVarList:
    TempTable       =   CroSecSumStatDict['AccAbRet'].loc[idx[:,:,TempGroupVar,:,:],:] \
                        .reset_index(level=[2],drop=True) \
                        .unstack(level=[0,1,2]) \
                        .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                        .reindex(TempMultiIndex)
    for EventDict in EventDictList:
        Suffix          =   EventDict['Suffix']
        TempColList     =   pd.MultiIndex.from_tuples( \
                            [(x,y) \
                             for x in TempSampleListDict[Suffix] \
                             for y in TempTable.columns.get_level_values(2).unique().tolist()])
        TempTable[Suffix].reindex(columns=TempColList) \
        .to_excel(ExcelWriter,sheet_name=Suffix+'_'+TempGroupVar,float_format='%.2f')
# Save the File
ExcelWriter.save()  


### Cross-Sectional Results: Gap Business Days

## Setup
ExcelWriter     =   pd.ExcelWriter(TableFolder+'SumStat_GapBusDays.xlsx')                        
TempVarList     =   ['GapBusDays_F2I','GapBusDays_L2I','GapBusDays_F2L']
TempStatList    =   ['Min','5%','25%','50%','75%','95%','Max','Mean','Std', \
                     'Pct(<=0)','Pct(<=1)','Pct(<=5)','Pct(<=10)','Pct(<=20)', \
                     'Pct(<=65)','Pct(<=133)','Pct(<=265)','Obs','T-Stat']
TempMultiIndex  =   pd.MultiIndex.from_tuples([(x,y) for x in TempVarList for y in TempStatList])

TempSampleListDict \
                =   {'F': ['1994-1999','1983-1999','2000-2007', \
                           '1970-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'L': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'], \
                     'I': ['1994-1999','1970-1999','2000-2007', \
                           '1983-1999','1983-1993','1970-2007','1983-2007','1994-2007'] \
                    }
## Output Different Tables
# Unconditional Moments
TempTable       =   CroSecSumStatDict['GapBusDays'].loc[idx[:,:,'FullSample',:,:],:] \
                    .reset_index(level=[2,3],drop=True) \
                    .unstack(level=[0,1]) \
                    .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                    .reindex(TempMultiIndex)
for EventDict in EventDictList:
    Suffix      =   EventDict['Suffix']
    TempTable[Suffix][TempSampleListDict[Suffix]] \
    .to_excel(ExcelWriter,sheet_name=Suffix+'_Unconditional',float_format='%.2f')
    
# Conditional Moments
for TempGroupVar in NoSuffixGroupVarList+SuffixGroupVarList:
    TempTable       =   CroSecSumStatDict['GapBusDays'].loc[idx[:,:,TempGroupVar,:,:],:] \
                        .reset_index(level=[2],drop=True) \
                        .unstack(level=[0,1,2]) \
                        .stack(level=0).swaplevel(i=0,j=1,axis=0) \
                        .reindex(TempMultiIndex)
    for EventDict in EventDictList:
        Suffix          =   EventDict['Suffix']
        TempColList     =   pd.MultiIndex.from_tuples( \
                            [(x,y) \
                             for x in TempSampleListDict[Suffix] \
                             for y in TempTable.columns.get_level_values(2).unique().tolist()])
        TempTable[Suffix].reindex(columns=TempColList) \
        .to_excel(ExcelWriter,sheet_name=Suffix+'_'+TempGroupVar,float_format='%.2f')
# Save the File
ExcelWriter.save()  


### Cross-Time Summary Statistics

## Setup
GraphFolder     =   "..\\results\\TableGraph\\SumStat\\"

## Temporary Function for Graph Format
def TempFun_FormatAX(ax):
    ax.tick_params(axis='both',labelsize=8)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_fontsize(8)
    ax.title.set_fontsize(8)
    if plt.gca().get_legend()!=None:
        plt.setp(plt.gca().get_legend().get_texts(), fontsize=8) 
    return 

## Output the Graphs 
# GapDays-Median
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'CalHist_GapBusDays_Median.pdf', \
                              FigSize=(5,3))

ax              =   H_fig.add_subplot(1,1,1)

TempVarList     =   ['GapBusDays_F2I']
TempDS          =   CroTimeSumStat.loc[:,idx['I',TempVarList,'50%']] \
                    .T.reset_index(level=[0,2],drop=True).T
TempDS          =   TempDS[(TempDS.index>=datetime.date(1983,1,1)) & \
                           (TempDS.index<=datetime.date(2014,1,1))]
MultiLine_SinglePlot(TempDS,TempVarList, \
                     ['solid'],['red'], 
                     ax=ax, \
                     LineLabelList=[],LineWidth=3,XTickStep=1, \
                     YLabel='Number of Trading Days')

NBER_RecessionBar(ax)
ax.vlines(datetime.date(1999,12,31),ax.get_ylim()[0],ax.get_ylim()[1])
ax.yaxis.set_major_locator(MaxNLocator(steps=[2]))
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# GapDays-Distribution
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'CalHist_GapBusDays_Distribution.pdf', \
                              FigSize=(4,6))
TempVarList     =   ['GapBusDays_F2I','GapBusDays_L2I','GapBusDays_F2L']
TempStatList    =   ['Pct(<=0)','Pct(<=5)','Pct(<=20)','Pct(<=65)']
TempYLabelList  =   ['F2I','L2I','F2L']
for ii in range(len(TempVarList)):
    ax              =   H_fig.add_subplot(len(TempVarList),1,ii+1)
    TempDS          =   CroTimeSumStat.loc[:,idx['I',TempVarList[ii],TempStatList]] \
                        .T.reset_index(level=[0,1],drop=True).T
    TempDS          =   TempDS[(TempDS.index>=datetime.date(1983,1,1)) & \
                               (TempDS.index<=datetime.date(2014,6,1))]
    if ii==2:
        TempLabelList   =   ['$ \leq '+str(x)+'$' for x in [0,5,20,65]]
    else:
        TempLabelList   =   []
        
    MultiLine_SinglePlot(TempDS,TempStatList, \
                         ['solid','dashed','dashed','solid'], \
                         ['red','blue','green','black'], 
                         ax=ax, \
                         LineLabelList=TempLabelList,LineWidth=1, \
                         YLabel=TempYLabelList[ii]+'\%')
    NBER_RecessionBar(ax)
    TempFun_FormatAX(ax)

    
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

# Pct of Different Types of Issuances: Primary vs. Secondary
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'CalHist_PrimaryVsSecondary_Mean.pdf', \
                              FigSize=(5,3))

ax              =   H_fig.add_subplot(1,1,1)

TempVarList     =   ['PrimarySecondaryFlag', 'OnlySecondaryFlag']
TempDS          =   CroTimeSumStat.loc[:,idx['I',TempVarList,'Mean']] \
                    .T.reset_index(level=[0,2],drop=True).T
TempDS          =   TempDS[(TempDS.index>=datetime.date(1970,1,1)) & \
                           (TempDS.index<=datetime.date(2007,6,1))]
MultiLine_SinglePlot(TempDS*100,TempVarList,['solid','dashed'],['red','blue'], 
                     ax=ax, \
                     LineLabelList=['Combined','Only Secondary'],LineWidth=1, \
                     YLabel='\%')

NBER_RecessionBar(ax)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Pct of Different Types of Issuances: Shelf Registration
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'CalHist_ShelfIssueFlag_Mean.pdf', \
                              FigSize=(5,3))

ax              =   H_fig.add_subplot(1,1,1)

TempVarList     =   ['ShelfIssueFlag']
TempDS          =   CroTimeSumStat.loc[:,idx['L',TempVarList,'Mean']] \
                    .T.reset_index(level=[0,2],drop=True).T
TempDS          =   TempDS[(TempDS.index>=datetime.date(1983,1,1)) & \
                           (TempDS.index<=datetime.date(2014,1,1))]
MultiLine_SinglePlot(TempDS*100,TempVarList,['solid','dashed'],['red','blue'], 
                     ax=ax, \
                     LineLabelList=[],LineWidth=3, \
                     YLabel='\%',XTickStep=1)

NBER_RecessionBar(ax)
ax.vlines(datetime.date(1999,12,31),ax.get_ylim()[0],ax.get_ylim()[1])
ax.yaxis.set_major_locator(MaxNLocator(steps=[2]))
TempFun_FormatAX(ax)


H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# End of Section:
###############################################################################