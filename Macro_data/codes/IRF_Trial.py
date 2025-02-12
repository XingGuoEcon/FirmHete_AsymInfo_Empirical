# -*- coding: utf-8 -*-
"""
Code Introduction:
    
Version History:
    Created: Fri May 10 10:58:31 2019
    Current: 

@author: Xing Guo (xingguo@umich.edu)

"""
# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code computes the accumulated response of gross equity and debt 
    issuance to Romer and Romer monetary shock.
    For robustness check, the same procedure is also implemented on the shock
    series recovered by Wieland based on the full sample information; and the 
    sample period also varies from the original Romer and Romer (2004, AER) 
    period (1970-1996) to a longer sample period (1970-2007).
    
Version History:
    Created: Mar 03, 2017
    Current: Mar 20, 2018

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
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
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

##Windows System Path
os.chdir("Research Projects\\EquityMarkets_MonetaryPolicy\\Data\\Macro_data\\codes")


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
Sample_Q            =   pickle.load(open(DataFolder+"Sample_Q.p",'rb'))

# Romer and Romer Shocks
RRShock_Q           =   pd.read_stata("..\\datasets\\MonetaryShocks_FromWieland"+
                                      "\\RR_monetary_shock_quarterly.dta") \
                        .set_index('date')
# Merged Sample
Sample_Q            =   Sample_Q.merge(right=RRShock_Q,how='outer', \
                                       left_index=True,right_index=True)

## Sample Cleaning
# Season ID
Sample_Q['Quarter'] =   Sample_Q.index.map(lambda x: x.quarter)
Sample_Q.index      =   Sample_Q.index.map(lambda x: x.date)
# Set Monetary Shocks before March, 1969 to 0
Sample_Q.loc[Sample_Q.index<datetime.date(1969,3,1), \
             ['resid','resid_romer','resid_full']] \
                    =   0


### Regression Setup                    
LagMin_Shock        =   1
LagNum_Shock        =   3*4

LagNum_Res          =   2*4

StartEndDate        =   [datetime.date(1970,1,1),datetime.date(2007,6,30)]

## List of Response Variables with Level-Difference in Regression
# Normalized Varialbles
FlowVarList_Cor     =   ['EquityFin','EquityNetIssue','EquityNetIssueExMA','DivPayment', \
                         'EquityIssue','EquityRepurchase','EquityMA', \
                         'EquityIssuePublic','EquityIssuePrivate', \
                         'EquityIssueIPO','EquityIssueSEO', \
                         'EquityGrossIssue','DebtGrossIssue','TotalGrossIssue', \
                         'DebtFin','DebtSecurity', \
                         'ExternalFin','Inv', \
                         'LiqAcc','DebtFinNetLiqAcc','ExternalFinNetLiqAcc', \
                         'Profit']
FlowVarList_NonCor  =   ['EquityFin','DebtFin','ExternalFin','Inv', \
                         'LiqAcc','DebtFinNetLiqAcc','ExternalFinNetLiqAcc']
FlowVarList_Agg     =   ['EquityFin','DebtFin','ExternalFin','Inv', \
                         'LiqAcc','DebtFinNetLiqAcc','ExternalFinNetLiqAcc']
NormVarList         =   ['Trend_TotalAsset','LagTotalAsset','GrossValAdd']

LevelResVarList     =   []
for NormVar in NormVarList:
    LevelResVarList     =   LevelResVarList+ \
                            [TempVar+'_'+NormVar+'_'+'Cor' for TempVar in FlowVarList_Cor]+ \
                            [TempVar+'_'+NormVar+'_'+'NonCor' for TempVar in FlowVarList_NonCor]+ \
                            [TempVar+'_'+NormVar+'_'+'Agg' for TempVar in FlowVarList_Agg]

LevelResVarList     =   LevelResVarList+['IpoNum_Cor','SeoNum_Cor']
TempInd             =   (Sample_Q.index>=StartEndDate[0]) & (Sample_Q.index<=StartEndDate[1])
for TempVar in ['IpoNum_Cor','SeoNum_Cor']:
    Sample_Q[TempVar]   =   Sample_Q[TempVar]/Sample_Q.loc[TempInd,TempVar].mean()

## List of Response Variables with Log-Difference in Regression
LogResVarList       =   [x+'_'+y \
                         for x in ['Inv','GrossValAdd','TotalAsset'] \
                         for y in ['Cor','NonCor','Agg']]

    
LogResVarList       =   LogResVarList+ \
                        ['EquityGrossIssue_Cor','DebtGrossIssue_Cor', \
                         'EquityIssuePublic_Cor','EquityIssuePrivate_Cor', \
                         'IndProd','GDP','INV']

Sample_Q[LogResVarList] \
                    =   np.log(Sample_Q[LogResVarList])

## Merged Response Variable List
ResVarList          =   LevelResVarList+LogResVarList                    

## List of Variables which should have Extra (-) in IRF
SpecialNegVarList   =   ['EquityRepurchase','EquityMA','DivPayment']
for ResVar in ResVarList:
    if ResVar.split('_')[0] in SpecialNegVarList:
        Sample_Q[ResVar]    =   -Sample_Q[ResVar]

### Run Regressions and Collect the IRF 

## Regression Fitting
InitiateFlag        =   1
for ii in range(len(ResVarList)):
    ResVar          =   ResVarList[ii]
    TempIRF,TempSTD,TempRegResult   \
                    =   RomerRomerReg(Sample_Q, \
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
        
IRF_Q    =   IRF
STD_Q    =   STD




# End of Section:
###############################################################################


#%% Plots in the Paper
GraphFolder     =   '..\\results\\Paper\\'

## Equity vs. Debt, Net Flows
# Equity
#H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFin_Agg_Quarterly.pdf', \
#                              FigSize=(3,4))
#
#ax              =   H_fig.add_subplot(1,1,1)


#H_pdf.savefig(H_fig,bbox_inches='tight')
#H_pdf.close()
# End of Section:
###############################################################################