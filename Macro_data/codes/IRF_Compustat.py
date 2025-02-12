# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Mon May 20 15:35:36 2019
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


#%% Regression Results based on Quarterly Data


### Construct the Sample
DataFolder          =   "..\\temp\\"

## Read-in Data
# Quarterly Flow of Funds and the Related Time-series
Sample_CS_Q         =   pickle.load(open(DataFolder+"Sample_CS_Q.p",'rb'))

# Romer and Romer Shocks
RRShock_Q           =   pd.read_stata("..\\datasets\\MonetaryShocks_FromWieland"+
                                      "\\RR_monetary_shock_quarterly.dta") \
                        .set_index('date')
# Merged Sample
Sample_CS_Q         =   Sample_CS_Q.merge(right=RRShock_Q,how='outer', \
                                          left_index=True,right_index=True)
Sample_CS_Q.sort_index(inplace=True)
## Sample Cleaning
# Season ID
Sample_CS_Q['Quarter']  =   Sample_CS_Q.index.map(lambda x: x.quarter)
Sample_CS_Q.index       =   Sample_CS_Q.index.map(lambda x: x.date)
# Set Monetary Shocks before March, 1969 to 0
Sample_CS_Q.loc[Sample_CS_Q.index<datetime.date(1969,3,1), \
                ['resid','resid_romer','resid_full']] \
                    =   0


### Regression Setup                    
LagMin_Shock        =   1
LagNum_Shock        =   3*4

LagNum_Res          =   2*4

StartEndDate        =   [datetime.date(1984,1,1),datetime.date(2007,6,30)]

## List of Response Variables with Level-Difference in Regression
# Normalized Varialbles
FlowVarList         =   ['StockIssuance', 'StockRepurchase', 'Dividend',
                         'Equity_NetIssuance', 'EquityFinancing', 'LongTermDebt_Issuance',
                         'LongTermDebt_Reduction', 'CurrentDebt_NetIssuance',
                         'LongTermDebt_NetIssuance', 'DebtFinancing', \
                         'EquityIssuance_Ipo', 'EquityIssuance_Seo', 'EquityIssuance_IpoSeo']

NormVarList         =   ['LagTotalAsset']

LevelResVarList     =   []
for NormVar in NormVarList:
    LevelResVarList     =   LevelResVarList+ \
                            [TempVar+'_'+NormVar for TempVar in FlowVarList]

LevelResVarList     =   LevelResVarList+['IpoNum','SeoNum']
TempInd             =   (Sample_CS_Q.index>=StartEndDate[0]) & (Sample_CS_Q.index<=StartEndDate[1])
for TempVar in ['IpoNum','SeoNum']:
    Sample_CS_Q[TempVar]   =   Sample_CS_Q[TempVar]/Sample_CS_Q.loc[TempInd,TempVar].mean()
    
## List of Response Variables with Log-Difference in Regression
LogResVarList       =   []


Sample_CS_Q[LogResVarList] \
                    =   np.log(Sample_CS_Q[LogResVarList])

## Merged Response Variable List
ResVarList          =   LevelResVarList+LogResVarList                    

## List of Variables which should have Extra (-) in IRF
SpecialNegVarList   =   ['StockRepurchase','Dividend','LongTermDebt_Reduction']
for ResVar in ResVarList:
    if ResVar.split('_')[0] in SpecialNegVarList:
        Sample_CS_Q[ResVar]     =   -Sample_CS_Q[ResVar]

### Run Regressions and Collect the IRF 

## Regression Fitting
InitiateFlag        =   1
for ii in range(len(ResVarList)):
    ResVar          =   ResVarList[ii]
    TempIRF,TempSTD,TempRegResult   \
                    =   RomerRomerReg(Sample_CS_Q, \
                                      ResVar,'resid_full','Quarter', \
                                      LagNum_Res,LagNum_Shock,LagMin_Shock, \
                                      StartEndIndex=StartEndDate, \
                                      ResType='Diff',IRFType='Accumulated')
    if InitiateFlag:
        IRF             =   TempIRF
        STD             =   TempSTD
        
        InitiateFlag    =   0
    else:
        IRF             =   IRF.join(TempIRF)
        STD             =   STD.join(TempSTD)
        
IRF_Q           =   IRF
STD_Q           =   STD

if LagMin_Shock>0:
    IRF_Q.loc[0,:]  =   0
    IRF_Q           =   IRF_Q.sort_index()
    
    STD_Q.loc[0,:]  =   0
    STD_Q           =   STD_Q.sort_index()

# End of Section:
###############################################################################


#%% IRF Plots


### Setup

## Target Folder
GraphFolder     =   '..\\results\\Compustat\\'

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
FlowVarList     =   ['StockIssuance', 'StockRepurchase', 'Dividend',
                     'Equity_NetIssuance', 'EquityFinancing', 'LongTermDebt_Issuance',
                     'LongTermDebt_Reduction', 'CurrentDebt_NetIssuance',
                     'LongTermDebt_NetIssuance', 'DebtFinancing', \
                     'EquityIssuance_Ipo', 'EquityIssuance_Seo', 'EquityIssuance_IpoSeo']


for FlowVar in FlowVarList:
    
    H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_'+FlowVar+'_CS_Quarterly.pdf', \
                                  FigSize=(3,4))
    
    ax              =   H_fig.add_subplot(1,1,1)
    IRF_SinglePlot(IRF_Q*100, \
                   [FlowVar+'_LagTotalAsset'], \
                   ['solid'],['red'], \
                   ax=ax,DS_STD=STD_Q*100, \
                   YLabel=' (\%)',XLabel='Quarter', \
                   LineLabelList=[],XTickStep=4,YMax=0.5,YMin=-0.5)
    TempFun_FormatAX(ax)
    
    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()


# End of Section:
###############################################################################