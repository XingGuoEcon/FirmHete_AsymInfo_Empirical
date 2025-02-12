# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Tue Apr 16 14:42:29 2019
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
'''
This section is designed to 
'''


### Compute the Aggregated Return/Accumulated Return History

## Load-in the Data
DataFolder      =   "..\\temp\\"
# Return History, Wide Panel
DS_Ret          =   pickle.load(open(DataFolder+"SDC_Ret_Wide.p",'rb'))
# Issuance Information
DS_IssueInfo    =   pickle.load(open(DataFolder+"SDC_IssuanceInfo.p",'rb'))

## Clean the Data
# Convert Return History to pct Unit
RetVarList      =   DS_Ret.columns.tolist()
RetVarList.remove('IssueID')
DS_Ret[RetVarList] \
                =   DS_Ret[RetVarList]*100
# Merge the Issuance Information into the Return History
InfoVarList     =   [x+y for x in ['FilingDate','LaunchDate','IssueDate'] \
                         for y in ['','_Quarter','_Year']]+ \
                    [x+y for x in ['GapBusDays','GapDays'] \
                         for y in ['_F2I','_L2I']]
DS_Ret          =   DS_Ret.merge(right=DS_IssueInfo[['IssueID']+InfoVarList], \
                                 how='left',on='IssueID')

## Setup
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]

## Temporary Function for Calculating the Summary Statistics
def TempFun_UnitSumStat(DS,EventDict,DateLimit,VarList):
    
    Suffix      =   EventDict['Suffix']
    EventDateVar=   EventDict['DateVar']
    TempInd     =   ( DS[EventDateVar]>=DateLimit[0] ) & \
                    ( DS[EventDateVar]<=DateLimit[1] )
    TempDS      =   DS.loc[TempInd,[Suffix+'_'+x for x in VarList]]
    TempSumStat =   TempDS.describe(percentiles=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]) \
                    .rename(index={'count': 'Obs','mean': 'Mean','std': 'Std', \
                                  'min': 'Min','max': 'Max'})
    TempSumStat =   TempSumStat.T
    
    TempDateTag =   (DateLimit[0].year,DateLimit[1].year)
    
    TempSumStat.columns     =   pd.MultiIndex.from_tuples([(Suffix,TempDateTag,x) \
                                                           for x in TempSumStat.columns])
    TempSumStat.rename(index={Suffix+'_'+x: x for x in VarList},inplace=True)
    return TempSumStat

## Setup
# Parameters in Construction
StartEndDate    =   [-100,160]
# Parameters in Computation
RetVarList      =   ['Ret_'+str(x) for x in range(StartEndDate[0],StartEndDate[1]+1)]
AccRetVarList   =   ['AccRet_'+str(StartEndDate[0])+'_'+str(x) \
                     for x in range(StartEndDate[0],StartEndDate[1]+1)]
VarList         =   RetVarList+AccRetVarList

SamplePeriodList=   [[datetime.date(1970,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1983,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1994,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1970,1,1),datetime.date(2007,12,31)], \
                     [datetime.date(1983,1,1),datetime.date(2007,6,1)], \
                     [datetime.date(1994,1,1),datetime.date(2007,6,1)], \
                     [datetime.date(1983,1,1),datetime.date(1993,12,31)], \
                     [datetime.date(1970,1,1),datetime.date(1993,12,31)], \
                     [datetime.date(2000,1,1),datetime.date(2007,6,1)]]

## Computation
InitiateFlag    =   True
for EventDict in EventDictList:
    for DateLimit in SamplePeriodList:
        TempSumStat     =   TempFun_UnitSumStat(DS_Ret,EventDict,DateLimit,VarList)
        if InitiateFlag:
            SumStat         =   TempSumStat
            InitiateFlag    =   False
        else:
            SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                              left_index=True,right_index=True)
SumStat_Ret     =   SumStat.loc[RetVarList,:] \
                    .rename(index={x:int(x.split('_')[1]) for x in RetVarList})
SumStat_AccRet  =   SumStat.loc[AccRetVarList,:] \
                    .rename(index={x:int(x.split('_')[2]) for x in AccRetVarList})


### Generate the Graphs

## Setup
GraphFolder     =   "..\\results\\TableGraph\\EventWinHistory\\"

# Temporary Function
def TempFun_Plot(ax,SumStatDS,IF,StatVar,Title, \
                 SubSampleList,LineStyleList,LineColorList,LineLabelList,YLabel,YLimit,XLabel):
#    SubSampleList   =   [(1994,1999),(1984,1993),(2000,2007)]
#    LineStyleList   =   ['solid','dashed','dashed']
#    LineColorList   =   ['black','red','blue']
#    LineLabelList   =   ['94-99','94-07','84-99']
    TempData        =   SumStatDS.loc[:,idx[IF,SubSampleList,StatVar]]
    TempData.columns=   [x[1] for x in TempData.columns]

    ax              =   MultiLine_SinglePlot(TempData,SubSampleList, \
                                             LineStyleList,LineColorList, \
                                             LineWidth=1.5,ax=ax,Title=Title, \
                                             YLabel=YLabel,LineLabelList=LineLabelList,  \
                                             XLabel=XLabel, \
                                             YLimit=YLimit)
#    ax.xaxis.set_ticks(range(-30,11,10))
    ax.fill_between(x=[-1,1], \
                    y1=[ax.get_ylim()[0],ax.get_ylim()[0]],\
                    y2=[ax.get_ylim()[1],ax.get_ylim()[1]], \
                    edgecolor='pink',facecolor='pink',alpha=0.5)
    ax.fill_between(x=[11,160], \
                    y1=[ax.get_ylim()[0],ax.get_ylim()[0]],\
                    y2=[ax.get_ylim()[1],ax.get_ylim()[1]], \
                    edgecolor='blue',facecolor='blue',alpha=0.1)
    return ax
# Benchmark Periods, Mean
TempSampleList      =   [(1983,1999),(1983,2007)]
TempSampleLabelList =   ['to99','to07']
TempStatVar         =   'Mean'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+TempStatVar
        # Accumulated Return
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'WinHist_AccRet_'+TempLabel+'.pdf', \
                                      FigSize=(5,3))
        
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStat_AccRet,TempSuffix,'Mean','', \
                     [TempSampleList[ii]],['solid'],['black'],[''],'\%',[0,30], \
                     'Trading Days from the Event Date')
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 
        # Daily Return
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'WinHist_Ret_'+TempLabel+'.pdf', \
                                      FigSize=(5,3))
        
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStat_Ret,TempSuffix,'Mean','', \
                     [TempSampleList[ii]],['solid'],['black'],[''],'\%',[-1.5,0.5], \
                     'Trading Days from the Event Date')
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 

# All SupSample Periods, All Statistics
for EventDict in EventDictList:
    Suffix          =   EventDict['Suffix']
    H_pdf,H_fig     =   Graph_PDF(GraphFolder+'WinHist_RetVsAccRet_'+Suffix+'_AllSubSample_AllStat.pdf', \
                                  FigSize=(5*2,3*2))
    
    ax              =   H_fig.add_subplot(2,2,1)
    TempFun_Plot(ax,SumStat_Ret,Suffix,'Mean','Mean', \
                 [(1983,1999),(1970,1999),(2000,2007)], \
                 ['solid','dashed','dashed'],['black','blue','red'], \
                 ['94-99','70-99','00-07'],'Daily Return (\%)',[-2,1],'')
    ax              =   H_fig.add_subplot(2,2,2)
    TempFun_Plot(ax,SumStat_Ret,Suffix,'50%','Median', \
                 [(1983,1999),(1970,1999),(2000,2007)], \
                 ['solid','dashed','dashed'],['black','blue','red'], \
                 [],'',[-2,1],'')
    ax              =   H_fig.add_subplot(2,2,3)
    TempFun_Plot(ax,SumStat_AccRet,Suffix,'Mean','', \
                 [(1983,1999),(1970,1999),(2000,2007)], \
                 ['solid','dashed','dashed'],['black','blue','red'], \
                 [],'Accumulated Return (\%)',[0,30],'Trading Days from the Event Date')
    ax              =   H_fig.add_subplot(2,2,4)
    TempFun_Plot(ax,SumStat_AccRet,Suffix,'50%','', \
                 [(1983,1999),(1970,1999),(2000,2007)], \
                 ['solid','dashed','dashed'],['black','blue','red'], \
                 [],'',[0,30],'Trading Days from the Event Date')
    
    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close() 
# End of Section:
###############################################################################
    
    

#%% Abnormal Return/Accumulated Return History within Event Window
'''
This section is designed to help audience to understand the event study we use.
The benchmark result is the event window history of the abnormal return around 
the filing event dates. The robustness check includes following dimensions:
    1. Different statistics for the abnormal return: mean, median, pct of neg., T-values
    2. Both Issuance and Filing events.
    3. Different Sub-sample periods.
'''

### Calculation

## Load-in the Data
DataFolder      =   "..\\temp\\"
# Panel of Abnormal Return
DS_AbRet        =   pickle.load(open(DataFolder+"SDC_AbRet_Wide.p",'rb'))
# Convert to pct return
RetVarList      =   DS_AbRet.columns.tolist()
RetVarList.remove('IssueID')
DS_AbRet[RetVarList] \
                =   DS_AbRet[RetVarList]*100
# Issuance Information
DS_IssueInfo    =   pickle.load(open(DataFolder+"SDC_IssuanceInfo.p",'rb'))
InfoVarList     =   [x+y for x in ['FilingDate','LaunchDate','IssueDate'] \
                         for y in ['','_Quarter','_Year']]+ \
                    [x+y for x in ['GapBusDays','GapDays'] \
                         for y in ['_F2I','_L2I']]
# Merge the Data Sets
DS              =   DS_AbRet.merge(right=DS_IssueInfo[['IssueID']+InfoVarList], \
                                   how='left',on='IssueID')

## Setup
EventDictList   =   [{'Suffix': 'F', 'DateVar': 'FilingDate'}, \
                     {'Suffix': 'L', 'DateVar': 'LaunchDate'}, \
                     {'Suffix': 'I', 'DateVar': 'IssueDate'}]


## Temporary Function for Calculating the Summary Statistics
def TempFun_UnitSumStat(DS,EventDict,DateLimit,VarList):
    TempSuffix  =   EventDict['Suffix']
    TempDateVar =   EventDict['DateVar']
    
    TempInd     =   ( DS[TempDateVar]>=DateLimit[0] ) & \
                    ( DS[TempDateVar]<=DateLimit[1] )
    TempDS      =   DS.loc[TempInd,[TempSuffix+'_'+x for x in VarList]]
    TempSumStat =   TempDS.describe(percentiles=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]) \
                    .rename(index={'count': 'Obs','mean': 'Mean','std': 'Std', \
                                  'min': 'Min','max': 'Max'})
    TempSumStat.loc['MeanStd',:] \
                =   TempSumStat.loc['Std',:]/np.sqrt(TempSumStat.loc['Obs',:])
    TempSumStat.loc['Tstat',:] \
                =   TempSumStat.loc['Mean',:]/TempSumStat.loc['MeanStd',:]
                
    TempNegFlag =   TempDS.copy()
    TempNegFlag[TempDS<0]   =   1
    TempNegFlag[TempDS>=0]  =   0
    TempSumStat.loc['NegMean',:] \
                =   TempNegFlag.mean()*100
    TempSumStat.loc['NegStd',:] \
                =   TempNegFlag.std()*100
    TempSumStat.loc['NegMeanStd',:] \
                =   TempSumStat.loc['NegStd',:]/np.sqrt(TempSumStat.loc['Obs',:])
    TempSumStat.loc['NegTstat',:] \
                =   (TempSumStat.loc['NegMean',:]-50)/(TempSumStat.loc['NegMeanStd',:])
    
    TempSumStat =   TempSumStat.T
    
    TempDateTag =   (DateLimit[0].year,DateLimit[1].year)
    
    TempSumStat.columns     =   pd.MultiIndex.from_tuples([(TempSuffix,TempDateTag,x) \
                                                           for x in TempSumStat.columns])
    TempSumStat.rename(index={TempSuffix+'_'+x: x for x in VarList},inplace=True)
    
    return TempSumStat

## Compute the Statistics
# Setup
StartEndDate    =   [-100,10]
AbRetVarList    =   ['AbRet_'+str(x) for x in range(StartEndDate[0],StartEndDate[1]+1)]
AccAbRetVarList_Long \
                =   ['AccAbRet_'+str(StartEndDate[0])+'_'+str(x) \
                     for x in range(StartEndDate[0],StartEndDate[1]+1)]
AccAbRetVarList_Short \
                =   ['AccAbRet_'+str(-x)+'_'+str(x) for x in range(1,10)]+ \
                    ['AccAbRet_0_'+str(x) for x in range(1,10)]
AccAbRetVarList =   AccAbRetVarList_Long+AccAbRetVarList_Short
VarList         =   AbRetVarList+AccAbRetVarList

SamplePeriodList=   [[datetime.date(1970,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1983,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1994,1,1),datetime.date(1999,12,31)], \
                     [datetime.date(1970,1,1),datetime.date(2007,12,31)], \
                     [datetime.date(1983,1,1),datetime.date(2007,6,1)], \
                     [datetime.date(1994,1,1),datetime.date(2007,6,1)], \
                     [datetime.date(1983,1,1),datetime.date(1993,12,31)], \
                     [datetime.date(2000,1,1),datetime.date(2007,6,1)]]
InitiateFlag    =   True
for EventDict in EventDictList:
    for DateLimit in SamplePeriodList:
        TempSumStat     =   TempFun_UnitSumStat(DS,EventDict,DateLimit,VarList)
        if InitiateFlag:
            SumStat         =   TempSumStat
            InitiateFlag    =   False
        else:
            SumStat         =   SumStat.merge(right=TempSumStat,how='outer', \
                                              left_index=True,right_index=True)

# Clean the Data
SumStatDict     =   {}
SumStatDict['AccAbRet_Long'] \
                =   SumStat.loc[AccAbRetVarList_Long,:]
SumStatDict['AccAbRet_Long'].index \
                =   [int(x.split('_')[2]) for x in SumStatDict['AccAbRet_Long'].index]
                

SumStatDict['AbRet'] \
                =   SumStat.loc[AbRetVarList,:]
SumStatDict['AbRet'].index \
                =   [int(x.split('_')[1]) for x in SumStatDict['AbRet'].index]
                
SumStatDict['AccAbRet_Short'] \
                =   SumStat.loc[AccAbRetVarList_Short,:]

### Generate the Graphs

## Setup
GraphFolder     =   "..\\results\\TableGraph\\EventWinHistory\\"
DateLimit_0     =   (1983,1999)
ColorBarXLimit  =   [-1,1]

## Temporary Function for Graph Format
def TempFun_FormatAX(ax):
    ax.tick_params(axis='both',labelsize=8)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_fontsize(8)
    ax.title.set_fontsize(8)
    if plt.gca().get_legend()!=None:
        plt.setp(plt.gca().get_legend().get_texts(), fontsize=8) 
    return 

## Paper Main: Narrow Event Window History of Average Abnormal Return
# Temporary Function
def TempFun_Plot(ax,SumStat,IF,DateLimit,StatVarList,LineStyleList,LineColorList,LineLabelList, \
                           Title,XLabel,YLabel,YLimit,StdFlag=False):
    TempSumStat     =   SumStat.loc[:,idx[IF,[DateLimit],:]]
    TempSumStat.columns \
                    =   [x[2] for x in TempSumStat.columns]
 
    if StdFlag==False:
        TempStd     =   pd.DataFrame()
    else:
        TempStd     =   TempSumStat[[x+'Std' for x in StatVarList]] \
                        .rename(columns={x+'Std':x for x in StatVarList})
    
    ax              =   IRF_SinglePlot(TempSumStat[StatVarList],StatVarList,LineStyleList,LineColorList, \
                                       ax=ax, \
                                       LineLabelList=LineLabelList,XLabel=XLabel,YLabel=YLabel, \
                                       Title=Title, \
                                       DS_STD=TempStd, \
                                       ErrorBandWidth=2, \
                                       YMax=YLimit[1],YMin=YLimit[0],XTickStep=5, \
                                       SymmetricY=False)
    ax.fill_between(x=ColorBarXLimit, \
                    y1=[ax.get_ylim()[0],ax.get_ylim()[0]],\
                    y2=[ax.get_ylim()[1],ax.get_ylim()[1]], \
                    edgecolor='pink',facecolor='pink',alpha=0.5)
    
    TempFun_FormatAX(ax)
    
    return ax

# Sample Periods
TempSampleList      =   [(1970,1999),(1983,1999),(1970,2007),(1983,2007)]
TempSampleLabelList =   ['70to99','83to99','70to07','83to07']
# Mean
TempStatVar         =   'Mean'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+TempStatVar
        
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'NarrowWinHist_AbRet_'+TempLabel+'.pdf', \
                                      FigSize=(5,3))
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStatDict['AbRet'].loc[range(-10,11),:], \
                     TempSuffix,TempSampleList[ii],[TempStatVar],['solid'],['blue'],[], \
                     '','Trading Days from Event Date','\%',[-1.5,0.5],StdFlag=True)
        ax.yaxis.set_ticks(np.arange(-1.5,1,0.5))
        plt.axhline(y=0, linewidth=1,color='k',alpha=0.5)
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 
# NegPct
TempStatVar         =   'NegMean'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+TempStatVar
        
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'NarrowWinHist_AbRet_'+TempLabel+'.pdf', \
                                      FigSize=(5,3))
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStatDict['AbRet'].loc[range(-10,11),:], \
                     TempSuffix,TempSampleList[ii],[TempStatVar],['solid'],['blue'],[], \
                     '','Trading Days from Event Date','\%',[45,65],StdFlag=True)
        ax.yaxis.set_ticks(np.arange(45,70,5))
        plt.axhline(y=50, linewidth=1,color='k',alpha=0.5)
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 

## Paper Main: Narrow Event Window History of Average Accumulated Abnormal Return
# Temporary Function
def TempFun_Plot(ax,SumStatDS,IF,StatVar,Title, \
                 SubSampleList,LineStyleList,LineColorList,LineLabelList,YLabel,YLimit,XLabel):
    TempData        =   SumStatDS.loc[:,idx[IF,SubSampleList,StatVar]]
    TempData.columns=   [x[1] for x in TempData.columns]
    TempData        =   TempData.loc[range(-10,11),:]
    TempData        =   TempData-TempData.loc[-10,:]
    
    ax              =   MultiLine_SinglePlot(TempData,SubSampleList, \
                                             LineStyleList,LineColorList, \
                                             LineWidth=3,ax=ax,Title=Title, \
                                             XLabel=XLabel,YLabel=YLabel,LineLabelList=LineLabelList,  \
                                             YLimit=YLimit,XTickStep=5)
    ax.fill_between(x=ColorBarXLimit, \
                    y1=[ax.get_ylim()[0],ax.get_ylim()[0]],\
                    y2=[ax.get_ylim()[1],ax.get_ylim()[1]], \
                    edgecolor='pink',facecolor='pink',alpha=0.5)
    
    TempFun_FormatAX(ax)
    return ax
# Sample Periods
TempSampleList      =   [(1970,1999),(1983,1999),(1970,2007),(1983,2007)]
TempSampleLabelList =   ['70to99','83to99','70to07','83to07']
# Mean
TempStatVar         =   'Mean'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+TempStatVar
        
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'NarrowWinHist_AccAbRet_'+TempLabel+'.pdf', \
                                  FigSize=(5,3))
    
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStatDict['AccAbRet_Long'],TempSuffix,TempStatVar,'', \
                     [TempSampleList[ii]],['solid'],['black'], \
                     [''],'\%',[-1,1],'Trading Days from Event Date')
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 
# Median
TempStatVar         =   '50%'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+'Median'
        
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'NarrowWinHist_AccAbRet_'+TempLabel+'.pdf', \
                                  FigSize=(5,3))
    
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStatDict['AccAbRet_Long'],TempSuffix,TempStatVar,'', \
                     [TempSampleList[ii]],['solid'],['black'], \
                     [''],'\%',[-1,1],'Trading Days from Event Date')
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 

        
        
## Appendix: Wide Event Window
# Temporary Function
def TempFun_Plot(ax,SumStatDS,IF,StatVar,Title, \
                 SubSampleList,LineStyleList,LineColorList,LineLabelList,YLabel,YLimit,XLabel):
    TempData        =   SumStatDS.loc[:,idx[IF,SubSampleList,StatVar]]
    TempData.columns=   [x[1] for x in TempData.columns]

    ax              =   MultiLine_SinglePlot(TempData,SubSampleList, \
                                             LineStyleList,LineColorList, \
                                             LineWidth=1.5,ax=ax,Title=Title, \
                                             YLabel=YLabel,LineLabelList=LineLabelList,  \
                                             YLimit=YLimit)
    ax.fill_between(x=ColorBarXLimit, \
                    y1=[ax.get_ylim()[0],ax.get_ylim()[0]],\
                    y2=[ax.get_ylim()[1],ax.get_ylim()[1]], \
                    edgecolor='pink',facecolor='pink',alpha=0.5)
    return ax
# Sample Periods
TempSampleList      =   [(1970,1999),(1983,1999),(1970,2007),(1983,2007)]
TempSampleLabelList =   ['70to99','83to99','70to07','83to07']
# Benchmark Periods, Mean
TempStatVar         =   'Mean'
for ii in range(len(TempSampleList)):
    for EventDict in EventDictList:
        TempSuffix      =   EventDict['Suffix']
        TempLabel       =   TempSuffix+'_'+TempSampleLabelList[ii]+'_'+TempStatVar
        
        H_pdf,H_fig     =   Graph_PDF(GraphFolder+'WinHist_AccAbRet_'+TempLabel+'.pdf', \
                                  FigSize=(5,3))
    
        ax              =   H_fig.add_subplot(1,1,1)
        TempFun_Plot(ax,SumStatDict['AccAbRet_Long'],TempSuffix,TempStatVar,'', \
                     [TempSampleList[ii]],['solid'],['black'],[''],'\%',[0,30],'')
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close() 
        
# All Subsample Periods， All Statistics
TempSampleList      =   [(1983,1999),(2000,2007)]
TempSampleLabelList =   ['83to99','00to07']
TempLineStyleList   =   ['solid','dashed']
TempLineColorList   =   ['red','blue']
for EventDict in EventDictList:
    TempSuffix      =   EventDict['Suffix']
    H_pdf,H_fig     =   Graph_PDF(GraphFolder+'WinHist_AbRetVsAccAbRet_'+ \
                                  TempSuffix+'_AllSubSample_AllStat.pdf', \
                                  FigSize=(5*2,3*2))
    
    ax              =   H_fig.add_subplot(2,2,1)
    TempFun_Plot(ax,SumStatDict['AbRet'],TempSuffix,'Mean','Mean', \
                 TempSampleList, \
                 TempLineStyleList,TempLineColorList, \
                 TempSampleLabelList,'Daily Return (\%)',[-2,1],'')
    ax              =   H_fig.add_subplot(2,2,2)
    TempFun_Plot(ax,SumStatDict['AbRet'],TempSuffix,'50%','Median', \
                 TempSampleList, \
                 TempLineStyleList,TempLineColorList, \
                 [],'',[-2,1],'')
    ax              =   H_fig.add_subplot(2,2,3)
    TempFun_Plot(ax,SumStatDict['AccAbRet_Long'],TempSuffix,'Mean','', \
                 TempSampleList, \
                 TempLineStyleList,TempLineColorList, \
                 [],'Accumulated Return (\%)',[0,30],'')
    ax              =   H_fig.add_subplot(2,2,4)
    TempFun_Plot(ax,SumStatDict['AccAbRet_Long'],TempSuffix,'50%','', \
                 TempSampleList, \
                 TempLineStyleList,TempLineColorList, \
                 [],'',[0,30],'')
    
    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close() 

# End of Section:
###############################################################################