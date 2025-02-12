# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Sun Mar 31 09:07:14 2019
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
## NBER data plot
exec(open(CodeFolder+'Fun_NBER_date.py').read())
exec(open(CodeFolder+'Fun_RomerRomerReg.py').read())
exec(open(CodeFolder+'Fun_IRF_Plot.py').read())
exec(open(CodeFolder+'Toolbox_Graph.py').read())
# End of Section: Import Self-written Functions
###############################################################################


#%% Sample Observations


### Calculation

## Read in the Data Sets
# Main Sample
DataFolder      =   "..\\temp\\"
Sample          =   pickle.load(open(DataFolder+'SDC_IssuanceInfo.p','rb'))
# Aggregated SEO Number from Fed
IpoSeoNum_Fed   =   pickle.load(open('..\\..\\Macro_data\\temp\\'+'IpoSeo_Q.p','rb'))
IpoSeoNum_Fed.index     =   [x.date() for x in IpoSeoNum_Fed.index]
IpoSeoNum_Fed.rename(columns={'SEO': 'SeoNum_Fed'},inplace=True)

## Sample Statistics
# Sample Size and Information Completeness
SampleInfo      =   {'Obs': Sample.shape[0], \
                     'Pct_NoNan_FDate': (1-pd.isna(Sample['FilingDate']).sum()/Sample.shape[0])*100, \
                     'Pct_NoNan_IDate': (1-pd.isna(Sample['IssueDate']).sum()/Sample.shape[0])*100}
# SEO Numbers across Sample Periods
SeoNum_I        =   Sample.groupby('IssueDate_Quarter')['IssueID'].count() \
                    .to_frame().rename(columns={'IssueID': 'SeoNum_I'})
SeoNum_F        =   Sample.groupby('FilingDate_Quarter')['IssueID'].count() \
                    .to_frame().rename(columns={'IssueID': 'SeoNum_F'})
SeoNum          =   SeoNum_I.merge(right=SeoNum_F,how='outer', \
                                   left_index=True,right_index=True)
SeoNum          =   SeoNum.merge(right=IpoSeoNum_Fed[['SeoNum_Fed']],how='outer', \
                                 left_index=True,right_index=True)


### Graph
GraphFolder     =   "..\\results\\DescriptiveStudy\\"

H_pdf,H_fig     =   Graph_PDF(GraphFolder+'SeoNum_Quarterly.pdf', \
                              FigSize=(10,6))
## Level
ax              =   H_fig.add_subplot(2,1,1)
ax              =   MultiLine_SinglePlot(SeoNum, \
                                         ['SeoNum_I','SeoNum_F','SeoNum_Fed'], \
                                         ['solid','dashed','solid'], \
                                         ['red','blue','black'], \
                                         ax=ax,YLabel='Obs.',LineWidth=2, \
                                         LineLabelList=['by Issuance Date', \
                                                        'by Filing Date', \
                                                        'by Issuance Date, from Fed'])
NBER_date(ax)
## Change
ax              =   H_fig.add_subplot(2,1,2)
ax              =   MultiLine_SinglePlot(SeoNum.diff(), \
                                         ['SeoNum_I','SeoNum_F','SeoNum_Fed'], \
                                         ['solid','dashed','solid'], \
                                         ['red','blue','black'], 
                                         ax=ax,YLabel='Diff. Obs.',LineWidth=2, \
                                         SymmetricY=True,YMid=0)
NBER_date(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

# End of Section:
###############################################################################


#%% Gap Days


### Calculation

## Read in the Data Sets
# Main Sample
DataFolder      =   "..\\temp\\"
Sample          =   pickle.load(open(DataFolder+'SDC_IssuanceInfo.p','rb'))

## Temporary Function
def TempFun_UnitStat(DS,GapDaysList):
    NumList         =   len(GapDaysList)
    NumDS           =   ( ~pd.isna(DS) ).sum()
    Stat            =   []
    Stat_Label      =   ['%: <='+str(x) for x in GapDaysList]
    
    for ii in range(NumList):
        TempInd         =   ( DS<=GapDaysList[ii] ) 
        Stat.append(TempInd.sum()/NumDS*100)
        
    Stat.extend([DS.mean(),DS.median()])
    Stat            =   pd.Series(Stat,index=Stat_Label+['Mean','Median'])
    
    return Stat

## Sample Statistics
GapDaysVar      =   'GapDays_Adj'
GapDaysList     =   [0,1,5,10,20,30,70,100,260]

# For the Whole Sample
GapDaysInfo_Agg =   TempFun_UnitStat(Sample[GapDaysVar],GapDaysList) \
                    .to_frame(name='Gap Days').T
#display(GapDaysInfo_Agg.T)
# Time-Series of Aggregation: Issuance Date
GapDaysInfo_I   =   Sample.groupby('IssueDate_Quarter')[GapDaysVar] \
                    .apply(TempFun_UnitStat,GapDaysList) \
                    .to_frame().reset_index() \
                    .pivot(index='IssueDate_Quarter',columns='level_1',values=GapDaysVar)
GapDaysInfo_I   =   GapDaysInfo_I[( GapDaysInfo_I.index>=datetime.date(1983,1,1) ) & \
                                  ( GapDaysInfo_I.index<=datetime.date(2015,12,31) ) ]
# Time-Series of Aggregation: Filing Date
GapDaysInfo_F   =   Sample.groupby('FilingDate_Quarter')[GapDaysVar] \
                    .apply(TempFun_UnitStat,GapDaysList) \
                    .to_frame().reset_index() \
                    .pivot(index='FilingDate_Quarter',columns='level_1',values=GapDaysVar)
GapDaysInfo_F   =   GapDaysInfo_F[( GapDaysInfo_F.index>=datetime.date(1983,1,1) ) & \
                                  ( GapDaysInfo_F.index<=datetime.date(2015,12,31) )]                    


### Graph

## Setup
GraphFolder     =   "..\\results\\DescriptiveStudy\\"

H_pdf,H_fig     =   Graph_PDF(GraphFolder+'GapDays_Quarterly.pdf', \
                              FigSize=(10,6))
## Issuance Date
# Average Days
ax              =   H_fig.add_subplot(2,2,1)
ax              =   MultiLine_SinglePlot(GapDaysInfo_I, \
                                         ['Mean','Median'],['solid','dashed'],['red','blue'], \
                                         LineLabelList=['Mean','Median'],LineWidth=2, \
                                         ax=ax,YLabel='Days',Title='By Issuance Date')
NBER_date(ax)
# Quantiles
ax              =   H_fig.add_subplot(2,2,3)
ax              =   MultiLine_SinglePlot(GapDaysInfo_I, \
                                         ['%: <=0','%: <=1','%: <=10'], \
                                         ['dotted','dashed','solid'], \
                                         ['red','blue','green'],LineWidth=2, \
                                         LineLabelList=['$=0$','$\leq 1$','$\leq 10$'], \
                                         ax=ax,YLabel='\%')
NBER_date(ax)

## Filing Date
# Average Days
ax              =   H_fig.add_subplot(2,2,2)
ax              =   MultiLine_SinglePlot(GapDaysInfo_F, \
                                         ['Mean','Median'],['solid','dashed'],['red','blue'], \
                                         LineWidth=2,ax=ax,Title='By Filing Date')
NBER_date(ax)
# Quantiles
ax              =   H_fig.add_subplot(2,2,4)
ax              =   MultiLine_SinglePlot(GapDaysInfo_F, \
                                         ['%: <=0','%: <=1','%: <=10'], \
                                         ['dotted','dashed','solid'], \
                                         ['red','blue','green'], \
                                         LineWidth=2,ax=ax)
NBER_date(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

# End of Section:
###############################################################################

#%% Abnormal Returns


### Calculation

## Read in the Data Sets
# Main Sample
DataFolder      =   "..\\temp\\"
WinHist         =   pickle.load(open(DataFolder+'SDC_AbRet_WinHist.p','rb'))

### Graphs
GraphFolder     =   "..\\results\\DescriptiveStudy\\"
StartEndDate    =   [-30,10]

WH_Sample       =   WinHist[ ( WinHist['EventDate']>=StartEndDate[0] ) & \
                             ( WinHist['EventDate']<=StartEndDate[1] )]

WH_Sample.set_index('EventDate',inplace=True)

WH_Sample       =   WH_Sample*100
for Type in ['NQ_I','WQ_I','NQ_F','WQ_F','I','F']:
    WH_Sample['Obs_'+Type]  =   WH_Sample['Obs_'+Type]/100

for Type in ['NQ_I','WQ_I','NQ_F','WQ_F','I','F']:
    WH_Sample['T_'+Type]    =   WH_Sample['Mean_'+Type]/WH_Sample['Std_'+Type] \
                                *np.sqrt(WH_Sample['Obs_'+Type])

## Window History
# Mean
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'EventStudy_AbRet_Mean.pdf', \
                              FigSize=(10,6))

VarList         =   ['Mean_WQ','Mean_NQ','WMean','Mean']
StyleList       =   ['solid','dashed','solid','dashed']
ColorList       =   ['red','red','blue','blue']
LabelList       =   ['Weighted, 2','Non-Weighted, 2','Weighted, 1','Non-Weighted, 1']

ax              =   H_fig.add_subplot(1,2,1)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_I' for x in VarList],StyleList,ColorList, \
                    LineLabelList=LabelList, \
                    LineWidth=2,ax=ax,Title='By Issuance Date',YLabel='Mean \%', \
                    YLimit=[-2,0.5])

ax              =   H_fig.add_subplot(1,2,2)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_F' for x in VarList],StyleList,ColorList,  \
                    LineWidth=2,ax=ax,Title='By Filing Date', \
                    YLimit=[-2,0.5])

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Quantile
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'EventStudy_AbRet_Quantile.pdf', \
                              FigSize=(10,6))

VarList         =   ['Q25_WQ','Q50_WQ','Q75_WQ','Q25','Q50','Q75']
StyleList       =   ['solid','solid','solid','dashed','dashed','dashed']
ColorList       =   ['black','red','blue','black','red','blue']
LabelList       =   ['Q25: 2(W)','Q50: 2(W)','Q75: 2(W)','Q25: 1','Q50: 1','Q75: 1']

ax              =   H_fig.add_subplot(1,2,1)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_I' for x in VarList],StyleList,ColorList, \
                    LineLabelList=LabelList,YLabel='Quantile \%', \
                    LineWidth=2,ax=ax,Title='By Issuance Date', \
                    YLimit=[-4,2])

ax              =   H_fig.add_subplot(1,2,2)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_F' for x in VarList],StyleList,ColorList,  \
                    LineWidth=2,ax=ax,Title='By Filing Date', \
                    YLimit=[-4,2])

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Pct Negative
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'EventStudy_AbRet_NegPct.pdf', \
                              FigSize=(10,6))

VarList         =   ['NegPct_WQ','NegPct_NQ','NegPct']
StyleList       =   ['solid','dashed','solid']
ColorList       =   ['red','blue','black']
LabelList       =   ['2(W)','2(NW)','1']

ax              =   H_fig.add_subplot(1,2,1)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_I' for x in VarList],StyleList,ColorList, \
                    LineLabelList=LabelList,YLabel='Percent of Negative AR', \
                    LineWidth=2,ax=ax,Title='By Issuance Date', \
                    YLimit=[30,90])

ax              =   H_fig.add_subplot(1,2,2)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_F' for x in VarList],StyleList,ColorList,  \
                    LineWidth=2,ax=ax,Title='By Filing Date', \
                    YLimit=[30,90])

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Std
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'EventStudy_AbRet_T.pdf', \
                              FigSize=(10,6))

VarList         =   ['T_WQ','T_NQ','T']
StyleList       =   ['solid','dashed','solid']
ColorList       =   ['red','blue','black']
LabelList       =   ['2(W)','2(NW)','1']

ax              =   H_fig.add_subplot(1,2,1)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_I' for x in VarList],StyleList,ColorList, \
                    LineLabelList=LabelList,YLabel='T', \
                    LineWidth=2,ax=ax,Title='By Issuance Date', \
                    YLimit=[-30,5])

ax              =   H_fig.add_subplot(1,2,2)
ax              =   MultiLine_SinglePlot(WH_Sample, \
                    [x+'_F' for x in VarList],StyleList,ColorList,  \
                    LineWidth=2,ax=ax,Title='By Filing Date', \
                    YLimit=[-30,5])

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# End of Section:
###############################################################################

#%% Accumulated Abnormal Returns


### Calculation

## Read in the Data Sets
# Main Sample
DataFolder      =   "..\\temp\\"

WinHist_SumStat =   pickle.load(open(DataFolder+'SDC_AbRet_WinHist_SumStat.p','rb'))

## Display the Results
AccAbRetStat    =   WinHist_SumStat.copy()
AccAbRetStat    =   AccAbRetStat*100
for Type in ['_NQ','_WQ']:
    AccAbRetStat['Obs'+Type]    =   AccAbRetStat['Obs'+Type]/100
for Type in ['_NQ','_WQ']:
    AccAbRetStat['T'+Type]      =   AccAbRetStat['Mean'+Type]/AccAbRetStat['Std'+Type] \
                                    *np.sqrt(AccAbRetStat['Obs'+Type])
AccAbRetStat['EventType']       =   AccAbRetStat.index.map(lambda x: x.split('_')[0])
AccAbRetStat['EventDateStart']  =   AccAbRetStat.index.map(lambda x: int(x.split('_')[-2]))
AccAbRetStat['EventDateEnd']    =   AccAbRetStat.index.map(lambda x: int(x.split('_')[-1]))
AccAbRetStat    =   AccAbRetStat[(AccAbRetStat['EventDateStart']>=-5) & \
                                 (AccAbRetStat['EventDateEnd']==1)]
AccAbRetStat    =   AccAbRetStat.reset_index(drop=True) \
                    .set_index(['EventType','EventDateStart','EventDateEnd']) \
                    .T

AccAbRetStat[('Stat','','')]            =   AccAbRetStat.index.map(lambda x: x.split('_')[0])
AccAbRetStat[('AggType','','')]         =   AccAbRetStat.index.map(lambda x: x.split('_')[-1])
AccAbRetStat.loc[AccAbRetStat[('AggType','','')]==AccAbRetStat[('Stat','','')],('AggType','','')]  \
                                = 'Pooled'
AccAbRetStat.set_index([('AggType',''),('Stat','')],inplace=True)
AccAbRetStat.sort_index(inplace=True)
Temp            =   AccAbRetStat.loc[(('WQ','NQ','Pooled'), \
                                      ('Min','Q25','Q50','Q75','Max','Mean','T','WMean','NegPct')),:]
display(np.round(Temp,2))
# End of Section:
###############################################################################

#%% Accumulated Abnormal Returns across Business Cycle


### Calculation

## Read in the Data Sets
DataFolder      =   "..\\temp\\"
CalHist         =   pickle.load(open(DataFolder+'SDC_AbRet_CalHist.p','rb'))

## Construct the Sample
Sample          =   CalHist.copy().set_index('Date')

VarList         =   []
for IF in ['I','F']:
    for NW in ['N','W']:
        for t in [-5,-1]:
            VarList.append(IF+'_AccAbRet_'+str(t)+'_1_'+NW)

Sample          =   Sample[VarList]*100


### Graph

## Setup
GraphFolder     =   "..\\results\\DescriptiveStudy\\"

H_pdf,H_fig     =   Graph_PDF(GraphFolder+'AccAbRet_Quarterly.pdf',FigSize=(10,6))
## Issuance Date
# Average Days
VarList         =   ['I_AccAbRet_'+x for x in ['-5_1_N','-1_1_N']]
StyleList       =   ['solid','dashed']
ColorList       =   ['red','blue']
LabelList       =   ['(-5,1), N','(-1,1), N']
ax              =   H_fig.add_subplot(2,1,1)
ax              =   MultiLine_SinglePlot(Sample, \
                                         VarList,StyleList,ColorList, \
                                         LineLabelList=LabelList,LineWidth=2, \
                                         ax=ax,YLabel='\%',Title='By Issuance Date', \
                                         YLimit=[-16,10])
NBER_date(ax)
## Filing Date
VarList         =   ['F_AccAbRet_'+x for x in ['-5_1_N','-1_1_N']]
ax              =   H_fig.add_subplot(2,1,2)
ax              =   MultiLine_SinglePlot(Sample, \
                                         VarList,StyleList,ColorList, \
                                         LineWidth=2, \
                                         ax=ax,YLabel='\%',Title='By Filing Date', \
                                         YLimit=[-16,10])
NBER_date(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# End of Section:
###############################################################################
