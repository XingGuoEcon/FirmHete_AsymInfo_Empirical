# -*- coding: utf-8 -*-
"""
Code Introduction: 
    This code investigate the response of TFP growth following the Romer & Romer
    monetary shock at the quarterly frequency.
Version History:
    Created: Thu Mar 14 16:32:37 2019
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
## Statistical Tools
import statsmodels.api as sm
## Database API
from fredapi import Fred


# End of Section: Import Moduels
###############################################################################


#%% Setup Work Directory

## Office Desktop Directory
os.chdir("E:\\Dropbox")
## Home Desktop Directory
#os.chdir("L:\Dropbox")
## Laptop Directory
#os.chdir("/Users/xingguo/Dropbox/")

##Windows System Path
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Macro_data\\codes")
##Mac System Path
#os.chdir("Research Projects/OttonelloGuo/Response2MonetaryShock/Monthly")

# End of Section: Setup Work Directory
###############################################################################

#%% Import Self-written Functions
exec(open('Fun_RomerRomerReg.py').read())
exec(open('Toolkit\\Toolbox_Graph.py').read())
# End of Section: Import Self-written Functions
###############################################################################


#%% Quarterly TFP Growth to Monetary Shock

### Construct the Data Set for Regression
try:
    ## Load in the Saved Data Set
    Sample          =   pickle.load(open("..\\temp\\TFP_Quarterly.p",'rb'))
except:
    ## Re-Construct the Data Set
    # Read-in TFP data
    TFP             =   pd.read_excel("..\\datasets\\TFP\\TFP_Quarterly.xlsx")
    TFP             =   TFP[['date','dtfp','dtfp_util', \
                                    'dtfp_I','dtfp_I_util', \
                                    'dtfp_C','dtfp_C_util']]
    
    TFP['Year']     =   TFP['date'].apply(lambda x: int(x.split(':Q')[0]))
    TFP['Quarter']  =   TFP['date'].apply(lambda x: int(x.split(':Q')[1]))
    TFP['QDate']    =   TFP['date'].apply(lambda x: datetime.datetime( \
                                                       int(x.split(':Q')[0]), \
                                                       3*(int(x.split(':Q')[1])-1)+1, \
                                                       1))
    TFP.set_index('QDate',inplace=True)
    # Quarterly Monetary Shock Data from Wieland
    RRShock     =   pd.read_stata("..\\datasets\\MonetaryShocks_FromWieland"+
                                  "\\RR_monetary_shock_quarterly.dta")
    RRShock.set_index('date',inplace=True)
    # Sample for Regression 
    Sample      =   RRShock.merge(right=TFP,how='outer', \
                                  left_index=True,right_index=True)
    Sample.sort_index(inplace=True)
    
    # Set Monetary Shocks before March, 1969 to 0
    Sample.loc[Sample.index<datetime.datetime(1969,3,1), \
               ['resid','resid_romer','resid_full']]    =   0
    # Save the Data
    pickle.dump(Sample,open("..\\temp\\TFP_Quarterly.p",'wb'))


### Generate the Result
## Setup
LagMin_Shock    =   1
LagNum_Shock    =   3*4

LagNum_Res      =   2*4

StartEndDate    =   [datetime.datetime(1970,1,1),datetime.datetime(2007,6,1)]
## Regression
ResVarList      =   ['dtfp','dtfp_util','dtfp_I','dtfp_I_util','dtfp_C','dtfp_C_util']

# Convert the Annual Growth Rate to Quarterly Growth Rate
Sample[ResVarList] \
                =   Sample[ResVarList]/4
for ii in range(len(ResVarList)):
    ResVar          =   ResVarList[ii]
    TempIRF,TempSTD,TempRegResult   \
                    =   RomerRomerReg(Sample, \
                                      ResVar,'resid_full','Quarter', \
                                      LagNum_Res,LagNum_Shock,LagMin_Shock, \
                                      StartEndIndex=StartEndDate, \
                                      ResType='Original',IRFType='Accumulated')
    if ii==0:
        IRF             =   TempIRF
        STD             =   TempSTD
    else:
        IRF             =   IRF.join(TempIRF)
        STD             =   STD.join(TempSTD)

IRF             =   IRF
STD             =   STD

if LagMin_Shock>0:
    IRF.loc[0,:]    =   0
    IRF             =   IRF.sort_index()
    STD.loc[0,:]    =   0
    STD             =   STD.sort_index()


# End of Section: Data Collection and Cleaning
###############################################################################


#%% IRF Plots


### Setup

## Target Folder
GraphFolder     =   '..\\results\\TFP\\'

## Format Setup
def TempFun_FormatAX(ax):
    ax.tick_params(axis='both',labelsize=8)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_fontsize(8)
    ax.title.set_fontsize(8)
    if plt.gca().get_legend()!=None:
        plt.setp(plt.gca().get_legend().get_texts(), fontsize=8) 
    return 


### Plots


## Main: Adjusted TFP: Aggregate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_AdjTFP_Agg_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF, \
               ['dtfp_util'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD, \
               YLabel='Accumulated Growth Rate (\%)',XLabel='Quarter', \
               LineLabelList=[],XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

## Appendix 1: Adjusted TFP: Different Sectors
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_AdjTFP_IvsC_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF, \
               ['dtfp_I_util','dtfp_C_util'], \
               ['dashed','solid'],['blue','red'], \
               ax=ax,DS_STD=STD, \
               YLabel='Accumulated Growth Rate (\%)',XLabel='Quarter', \
               LineLabelList=['Equipment and Durables','Non-Durables'], \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

## Appendix 2: Full Details of Adj vs. NonAdj 
# Aggregate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_TFP_Agg_AdjVsNonAdj_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF, \
               ['dtfp','dtfp_util'], \
               ['dashed','solid'],['blue','red'], \
               ax=ax,DS_STD=STD, \
               YLabel='Accumulated Growth Rate (\%)',XLabel='Quarter', \
               LineLabelList=['Not Adjusted','Adjusted'],XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()


# Equipment and Consumer Durables
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_TFP_EquipDurCon_AdjVsNonAdj_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF, \
               ['dtfp_I','dtfp_I_util'], \
               ['dashed','solid'],['blue','red'], \
               ax=ax,DS_STD=STD, \
               YLabel='Accumulated Growth Rate (\%)',XLabel='Quarter', \
               LineLabelList=['Not Adjusted','Adjusted'],XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

# Equipment and Consumer Durables
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_TFP_NonDur_AdjVsNonAdj_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF, \
               ['dtfp_C','dtfp_C_util'], \
               ['dashed','solid'],['blue','red'], \
               ax=ax,DS_STD=STD, \
               YLabel='Accumulated Growth Rate (\%)',XLabel='Quarter', \
               LineLabelList=['Not Adjusted','Adjusted'],XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

# End of Section:
###############################################################################