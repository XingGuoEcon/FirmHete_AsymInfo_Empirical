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


#%% Regression Results based on Monthly Data


### Construct the Sample 

## Read-in Data
DataFolder      =   "..\\temp\\"
# Real Gross Issuance Flows
Sample_M        =   pickle.load(open(DataFolder+"Sample_M.p",'rb'))
# Monthly Monetary Shock Data from Wieland
RRShock_M       =   pd.read_stata("..\\datasets\\MonetaryShocks_FromWieland"+
                                  "\\RR_monetary_shock_monthly.dta") \
                    .set_index('date')

## Sample for Regression 
Sample_M        =   RRShock_M.merge(right=Sample_M,how='outer', \
                                    left_index=True,right_index=True) \
                    .sort_index()
Sample_M.index  =   Sample_M.index.map(lambda x: x.date)

## Sample Cleaning
# Set Monetary Shocks before March, 1969 to 0
Sample_M.loc[Sample_M.index<datetime.date(1969,3,1),['resid','resid_romer','resid_full']] \
                =   0
# Generate Season Variables
Sample_M['Month'] \
                =   Sample_M.index.map(lambda x: x.month)


### Run Regression and Collect the IRF

## Setup
StartEndDate    =   [datetime.date(1970,1,1),datetime.date(2007,6,30)]
LagMin_Shock    =   1
LagNum_Shock    =   3*12

LagNum_Res      =   2*12

## Transformation of the Variables
# Level to Log-Level
Sample_M[['Equity','Debt']] \
                =   np.log(Sample_M[['Equity','Debt']])
# Extra Normalization by the Mean
#TempInd         =   (Sample.index>=StartEndDate[0]) & (Sample.index<=StartEndDate[1])
#for TempVar in ['Equity_LagTotalAsset_Cor','Debt_LagTotalAsset_Cor']:
#    Sample[TempVar] =   Sample[TempVar]/Sample.loc[TempInd,TempVar].mean()
                
## Regressiong Fit
ResVarList      =   ['Equity','Debt', \
                     'LogDev_Equity','LogDev_Debt', \
                     'Equity_LagTotalAsset_Cor','Debt_LagTotalAsset_Cor']

for ii in range(len(ResVarList)):
    ResVar          =   ResVarList[ii]
    TempIRF,TempSTD,TempRegResult   \
                    =   RomerRomerReg(Sample_M, \
                                      ResVar,'resid_full','Month', \
                                      LagNum_Res,LagNum_Shock,LagMin_Shock, \
                                      StartEndIndex=StartEndDate, \
                                      ResType='Diff',IRFType='Accumulated')
    if ii==0:
        IRF             =   TempIRF
        STD             =   TempSTD
        RegResultList   =   {}
        RegResultList[ResVar] \
                        =   TempRegResult
    else:
        IRF             =   IRF.join(TempIRF)
        STD             =   STD.join(TempSTD)
        RegResultList[ResVar] \
                        =   TempRegResult

IRF_M           =   IRF
IRF_M.loc[0,:]  =   0
IRF_M           =   IRF_M.sort_index()
STD_M           =   STD
STD_M.loc[0,:]  =   0
STD_M           =   STD_M.sort_index()

# End of Section: 
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
             ['resid','resid_romer','resid_full','resid_post84']] \
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
                         'Profit', \
                         'AggIpoSum','AggSeoSum','AggRepurchaseSum','AggDivPaymentSum']
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

LevelResVarList     =   LevelResVarList+['IpoNum_Cor','SeoNum_Cor','AggIpoNum_Cor','AggSeoNum_Cor']
TempInd             =   (Sample_Q.index>=StartEndDate[0]) & (Sample_Q.index<=StartEndDate[1])
for TempVar in ['IpoNum_Cor','SeoNum_Cor','AggIpoNum_Cor','AggSeoNum_Cor']:
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
SpecialNegVarList   =   ['EquityRepurchase','EquityMA','DivPayment', \
                         'AggRepurchaseSum','AggDivPaymentSum']
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
        
IRF_Q           =   IRF
STD_Q           =   STD

if LagMin_Shock>0:
    IRF_Q.loc[0,:]  =   0
    IRF_Q           =   IRF_Q.sort_index()
    STD_Q.loc[0,:]  =   0
    STD_Q           =   STD_Q.sort_index()

# End of Section:
###############################################################################


#%% Plots in the Paper


### Setup

## Target Folder
GraphFolder     =   '..\\results\\Paper\\'

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

## Equity vs. Debt, Net Flows
# Equity
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFin_Agg_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Agg'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# Debt
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_DebtFin_Agg_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtFin_LagTotalAsset_Agg'], \
               ['dashed'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

# Equity vs. Debt
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFinVsDebtFin_Agg_Quarterly.pdf', \
                              FigSize=(5,3))

ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Agg'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='Equity',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtFin_LagTotalAsset_Agg'], \
               ['dashed'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='',Title='Debt',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Net Equity Financing: Corporate vs. Non-Corporate
# Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFin_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Corporate','Non-Corporate'], \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Non-Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFin_NonCor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_NonCor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Corporate','Non-Corporate'], \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Corporate vs. Non-Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFin_CorVsNonCor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Cor','EquityFin_LagTotalAsset_NonCor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Corporate','Non-Corporate'], \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Equity Financing: Net Issuance vs. Dividend
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_NetIssuanceVsDiv_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityNetIssue_LagTotalAsset_Cor','DivPayment_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Net Issuance','Dividend (-)'], \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Equity vs. Debt Financing: Gross Issuance
# Equity
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityGrossIssuance_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityGrossIssue_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.2,YMin=-0.2)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Debt
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_DebtGrossIssuance_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtGrossIssue_LagTotalAsset_Cor'], \
               ['dashed'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Equity Vs. Debt
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityVsDebtGrossIssuance_Cor_Quarterly.pdf', \
                              FigSize=(5,3))

ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityGrossIssue_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='Equity',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtGrossIssue_LagTotalAsset_Cor'], \
               ['dashed'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='',Title='Debt',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Investment
# Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_Inv_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['Inv_LagTotalAsset_Cor'], \
               ['solid'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 
# Non-Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_Inv_NonCor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['Inv_LagTotalAsset_NonCor'], \
               ['dashed'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Profit
# Corporate
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_Profit_Cor_Quarterly.pdf', \
                              FigSize=(3,4))

ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['Profit_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='Fraction of Lagged Asset (\%)',Title='',XLabel='Quarter', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## IPO/SEO Numbers
# IPO
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_IpoNum_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['IpoNum_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# SEO
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SeoNum_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['SeoNum_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

# IPO vs. SEO
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_IpoVsSeoNum_Quarterly.pdf', \
                              FigSize=(5,3))
ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['IpoNum_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)',Title='IPO', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)
ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['SeoNum_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',Title='SEO', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

## IPO/SEO Aggregated from SDC: Frequency and Flows
# IPO Frequency
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcIpoNum_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggIpoNum_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# IPO Flow
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcIpo_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggIpoSum_LagTotalAsset_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Fraction of Lagged Asset (\%)', \
               YMin=-0.1,YMax=0.1,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# SEO Frequency
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcSeoNum_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggSeoNum_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# SEO Flow
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcSeo_Quarterly.pdf', \
                              FigSize=(3,4))
ax              =   H_fig.add_subplot(1,1,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggSeoSum_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Fraction of Lagged Asset (\%)', \
               YMin=-0.1,YMax=0.1,XTickStep=4)
TempFun_FormatAX(ax)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# IPO vs. SEO Frequency
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcIpoVsSeoNum_Quarterly.pdf', \
                              FigSize=(5,3))
ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggIpoNum_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)',Title='IPO', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)
ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['AggSeoNum_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',Title='SEO', \
               YMin=-50,YMax=50,XTickStep=4)
TempFun_FormatAX(ax)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# IPO vs. SEO Flow
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_SdcIpoVsSeo_Quarterly.pdf', \
                              FigSize=(5,3))
ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['AggIpoSum_LagTotalAsset_Cor'], \
               ['solid'],['blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',YLabel='Deviation from Historical Average (\%)',Title='IPO', \
               YMin=-0.15,YMax=0.15,XTickStep=4)
TempFun_FormatAX(ax)
ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['AggSeoSum_LagTotalAsset_Cor'], \
               ['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',Title='SEO', \
               YMin=-0.15,YMax=0.15,XTickStep=4)
TempFun_FormatAX(ax)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

# End of Section:
###############################################################################

#%% Main Plots

### Setup
GraphFolder     =   '..\\results\\Main\\'

## Main 1: Equity
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFinVsExternalFin_AggVsCor_Quarterly.pdf', \
                              FigSize=(10,6))
# Agg: Equity Financing
ax              =   H_fig.add_subplot(2,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Agg'], \
               ['solid'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='\%',Title='Net Equity Financing Flow, Aggregate', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
# Agg: Total External Financing
ax              =   H_fig.add_subplot(2,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['ExternalFin_LagTotalAsset_Agg'], \
               ['solid'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='Total External Financing, Aggregate', \
               XTickStep=4,YMax=0.5,YMin=-0.5)
# Cor.: Equity Financing: Gross Issuance vs. Net
ax              =   H_fig.add_subplot(2,2,3)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityGrossIssue_LagTotalAsset_Cor','EquityFin_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Gross Issuance','Net Flow'], \
               XLabel='Quarter',YLabel='\%',Title='Equity Financing, Corporate', \
               XTickStep=4)
# Cor.: Total External Financing: Gross Issuance vs. Net Flow
ax              =   H_fig.add_subplot(2,2,4)
IRF_SinglePlot(IRF_Q*100, \
               ['TotalGrossIssue_LagTotalAsset_Cor','ExternalFin_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',Title='Total External Financing, Corporate', \
               XTickStep=4)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Appendix: Debt
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_DebtFinVsExternalFin_AggVsCor_Quarterly.pdf', \
                              FigSize=(10,6))
# Agg: Net Financing Flow
ax              =   H_fig.add_subplot(2,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtFin_LagTotalAsset_Agg'], \
               ['solid'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               YLabel='\%',Title='Net Debt Financing Flow, Aggregate', \
               XTickStep=4)
# Agg: Total External Financing
ax              =   H_fig.add_subplot(2,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['ExternalFin_LagTotalAsset_Agg'], \
               ['solid'],['black'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='Total External Financing, Aggregate', \
               XTickStep=4)
# Cor.: Gross Issuance vs. Net
ax              =   H_fig.add_subplot(2,2,3)
IRF_SinglePlot(IRF_Q*100, \
               ['DebtGrossIssue_LagTotalAsset_Cor','DebtFin_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Gross Issuance','Net Flow'], \
               XLabel='Quarter',YLabel='\%',Title='Debt Financing, Corporate', \
               XTickStep=4)
# Cor.: Total External Financing: Gross Issuance vs. Net Flow
ax              =   H_fig.add_subplot(2,2,4)
IRF_SinglePlot(IRF_Q*100, \
               ['TotalGrossIssue_LagTotalAsset_Cor','ExternalFin_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               XLabel='Quarter',Title='Total External Financing, Corporate', \
               XTickStep=4)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close() 

## Appendix: Equity Financing: Cor., Non-Cor., Net Issuance vs. Dividend, Gross Issuance
H_pdf,H_fig     =   Graph_PDF(GraphFolder+'IRF2MS_EquityFinDecomposition_Normalized_Quarterly.pdf', \
                              FigSize=(10,6))
# Equity Financing: Cor. vs. Non-Corporate
ax              =   H_fig.add_subplot(1,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityFin_LagTotalAsset_Cor','EquityFin_LagTotalAsset_NonCor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Corporate','Non-Corporate'], \
               XLabel='Quarter',YLabel='\%',Title='Total Net Equity Financing Flows', \
               XTickStep=4)
# Equity Financing of Corporate: Net Issuance vs. Dividend Payment
ax              =   H_fig.add_subplot(1,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['EquityNetIssue_LagTotalAsset_Cor','DivPayment_LagTotalAsset_Cor'], \
               ['solid','dashed'],['red','blue'], \
               ax=ax,DS_STD=STD_Q*100, \
               LineLabelList=['Net Issuance','Dividend Payment (-)'], \
               XLabel='Quarter',Title='Equity Financing Flows, Corporate', \
               XTickStep=4)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()


# End of Section:
###############################################################################



#%% Generate the IRF Plots of the Quarterly Results

## Folder
GraphFolder             =   '..\\results\\RobustnessCheck\\'

## Difference Response Variables
# Normalized Gross Issuance Flows
for NormVar in NormVarList:
    for SecVar in ['Cor']:
        TempFileName    =   GraphFolder+'IRF2MS_GrossIssFlow_'+NormVar+'_'+SecVar+'_Quarterly.pdf'
        H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
        ax              =   H_fig.add_subplot(1,1,1)
        
        IRF_SinglePlot(IRF_Q*100, \
                       ['EquityGrossIssue'+'_'+NormVar+'_'+SecVar, \
                        'DebtGrossIssue'+'_'+NormVar+'_'+SecVar], \
                        ['solid','dashed'],['red','blue'], \
                        ax=ax,DS_STD=STD_Q*100, \
                        LineLabelList=['Equity','Debt'], \
                        XLabel='Quarter',YLabel='\%',XTickStep=4)
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close()
# Net Financial Flows
for NormVar in NormVarList:
    for SecVar in ['Cor','NonCor']:
        TempFileName    =   GraphFolder+'IRF2MS_NetFinFlow_'+NormVar+'_'+SecVar+'_Quarterly.pdf'
        H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
        ax              =   H_fig.add_subplot(1,1,1)
        IRF_SinglePlot(IRF_Q*100, \
                       ['EquityFin'+'_'+NormVar+'_'+SecVar, \
                        'DebtFin'+'_'+NormVar+'_'+SecVar], \
                        ['solid','dashed'],['red','blue'], \
                        ax=ax,DS_STD=STD_Q*100, \
                        LineLabelList=['Equity','Debt'], \
                        XLabel='Quarter',YLabel='\%',XTickStep=4)
        
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close()
# Details of Equity Financing
for NormVar in NormVarList:
    TempFileName    =   GraphFolder+'IRF2MS_EquityFinDetails_'+NormVar+'_Cor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   ['EquityNetIssue'+'_'+NormVar+'_Cor', \
                    'DivPayment'+'_'+NormVar+'_Cor'], \
                    ['solid','dashed'],['red','blue'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    LineLabelList=['Net Issuance','Dividend (-)'], \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()
# Details of Equity Issuance
for NormVar in NormVarList:
    TempFileName    =   GraphFolder+'IRF2MS_EquityIssPubicVsPrivate_'+NormVar+'_Cor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   ['EquityIssuePublic'+'_'+NormVar+'_Cor', \
                    'EquityIssuePrivate'+'_'+NormVar+'_Cor'], \
                    ['solid','dashed'],['red','blue'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    LineLabelList=['Public','Private'], \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()
    

# Details of Equity Net Issuance
for NormVar in NormVarList:
    TempFileName    =   GraphFolder+'IRF2MS_EquityIssDetails_'+NormVar+'_Cor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   ['EquityIssue'+'_'+NormVar+'_Cor', \
                    'EquityRepurchase'+'_'+NormVar+'_Cor', \
                    'EquityMA'+'_'+NormVar+'_Cor'], \
                    ['solid','dotted','dashed'],['black','red','blue'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    LineLabelList=['Issuance','Repurchase (-)','M\&A (-)'], \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()

# Details of Net Equity Issuance Excluding M&A
for NormVar in NormVarList:
    TempFileName    =   GraphFolder+'IRF2MS_EquityNetIssExMA_'+NormVar+'_Cor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   ['EquityNetIssueExMA'+'_'+NormVar+'_Cor'], \
                    ['solid'],['black'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()
    

# Details of Equity Gross Issuance: Private vs. Public
for NormVar in NormVarList:
    TempFileName    =   GraphFolder+'IRF2MS_EquityPublicIssIpoVsSeo_'+NormVar+'_Cor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   ['EquityIssueSEO'+'_'+NormVar+'_Cor', \
                    'EquityIssueIPO'+'_'+NormVar+'_Cor'], \
                    ['solid','dashed'],['red','blue'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    LineLabelList=['SEO','IPO'], \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()

# Liquidity Accumulation
for NormVar in NormVarList:
    for SecVar in ['Cor','NonCor']:
        TempFileName    =   GraphFolder+'IRF2MS_LiquidityAccumulation_'+NormVar+'_'+SecVar+'_Quarterly.pdf'
        H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
        ax              =   H_fig.add_subplot(1,1,1)
        
        IRF_SinglePlot(IRF_Q*100, \
                       ['LiqAcc'+'_'+NormVar+'_'+SecVar, \
                        'DebtFinNetLiqAcc'+'_'+NormVar+'_'+SecVar], \
                        ['solid','dashed'],['red','blue'], \
                        ax=ax,DS_STD=STD_Q*100, \
                        LineLabelList=['LiqAcc','DebtFinNetLiqAcc'], \
                        XLabel='Quarter',YLabel='\%',XTickStep=4)
    
        H_pdf.savefig(H_fig,bbox_inches='tight')
        H_pdf.close()
    
## Log-Difference Response Variables
#  Gross Issuance
TempFileName    =   GraphFolder+'IRF2MS_LogGrossIss_Cor_Quarterly.pdf'
H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
ax              =   H_fig.add_subplot(1,1,1)

IRF_SinglePlot(IRF_Q*100, \
               ['EquityGrossIssue_Cor', \
                'DebtGrossIssue_Cor'], \
                ['solid','dashed'],['red','blue'], \
                ax=ax,DS_STD=STD_Q*100, \
                LineLabelList=['Equity','Debt'], \
                XLabel='Quarter',YLabel='\%',XTickStep=4)

H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()

# Investment Flows, Gross Value Added, Total Asset
for TempVar in ['Inv','GrossValAdd','TotalAsset']:
    TempFileName    =   GraphFolder+'IRF2MS_Log'+TempVar+'_CorVsNonCor_Quarterly.pdf'
    H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(5,3))
    ax              =   H_fig.add_subplot(1,1,1)
    
    IRF_SinglePlot(IRF_Q*100, \
                   [TempVar+'_Cor',TempVar+'_NonCor'], \
                    ['solid','dashed'],['red','blue'], \
                    ax=ax,DS_STD=STD_Q*100, \
                    LineLabelList=['Corporate','Non-Corporate'], \
                    XLabel='Quarter',YLabel='\%',XTickStep=4)

    H_pdf.savefig(H_fig,bbox_inches='tight')
    H_pdf.close()

# NIPA Flow
TempFileName    =   GraphFolder+'IRF2MS_AggFlow_Quarterly.pdf'
H_pdf,H_fig     =   Graph_PDF(TempFileName,FigSize=(10,6))
ax              =   H_fig.add_subplot(2,2,1)
IRF_SinglePlot(IRF_Q*100, \
               ['IndProd'],['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='Industrial Production',XLabel='',YLabel='Log-Deviation (\%)', \
               YMin=-2,YMax=2,XTickStep=4)
ax              =   H_fig.add_subplot(2,2,2)
IRF_SinglePlot(IRF_Q*100, \
               ['GDP'],['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='GDP',XLabel='',YLabel='', \
               YMin=-2,YMax=2,XTickStep=4)
ax              =   H_fig.add_subplot(2,2,3)
IRF_SinglePlot(IRF_Q*100, \
               ['INV'],['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='Investment, NIPA',XLabel='Quarter',YLabel='Log-Deviation (\%)', \
               YMin=-6,YMax=6,XTickStep=4)
ax              =   H_fig.add_subplot(2,2,4)
IRF_SinglePlot(IRF_Q*100, \
               ['Inv_Agg'],['solid'],['red'], \
               ax=ax,DS_STD=STD_Q*100, \
               Title='Investment, Flow of Funds',XLabel='Quarter',YLabel='', \
               YMin=-6,YMax=6,XTickStep=4)
H_pdf.savefig(H_fig,bbox_inches='tight')
H_pdf.close()
# End of Section:
###############################################################################


