"""
Code Introduction:
    
Version History:
    Created: Tue Aug 18 17:57:56 2020
    Current: 

@author: Xing Guo (guoxing.econ@gmail.com)

"""

#%% Import Moduels

## System Tools
import os
import numpy as np
from collections import OrderedDict
import time
## I/O Tools
import _pickle as pickle
## Data Process Tools
import pandas as pd
# import modin.pandas as pd
import datetime
## Graphs
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as figpdf
## Statistical Tools
import statsmodels.formula.api as sm
from statsmodels.tsa.api import VAR
from scipy.stats import mstats
import statsmodels.api as SMAPI
from statsmodels.tsa.tsatools import detrend as DeTrend
from statsmodels.tsa.filters.hp_filter import hpfilter as HPfilter
from statsmodels.tsa.filters.bk_filter import bkfilter as BKfilter
## Database API
from fredapi import Fred
## Numerical API
from scipy.interpolate import interp1d
## Regular Expression API
import re
import multiprocessing as mp

idx = pd.IndexSlice

# from Toolbox_Graph import Graph_PDF, MultiLine_SinglePlot, NBER_RecessionBar, IRF_SinglePlot
# End of Section: Import Moduels
###############################################################################


#%% Setup Working Directory


## Windows System Path
FolderList = [xx+"\Dropbox (Bank of Canada)\Research Projects\EquityMarkets_MonetaryPolicy\Data\Micro_data\Trial_SideEvidence_InformationAsymmetry" \
              for xx in ["E:\\","B:\\","/mnt/b/"]]
for Folder in FolderList:
    if os.path.exists(Folder):
        os.chdir(Folder)    

# End of Section: Setup Working Directory
###############################################################################



#%% Convert the Pickles to Stata
Temp = pickle.load(open("../temp/RegSample.p",'rb'))
Temp.to_csv('RegSample.csv')
for vv in Temp.columns:
    if Temp[vv].dtype=='float64':
        Temp.loc[~np.isfinite(Temp[vv]),vv] = np.nan

#%% Convert Pickles to Stata
pickle.load(open("RegSample.p",'rb')).to_csv("RegSample.csv")
pickle.load(open("Sample_CleanedCS_Q.p",'rb')).to_csv("Sample_CleanedCS_Q.csv")
pickle.load(open("Link_SDC_Compustat.p","rb")).to_csv("Link_SDC_Compustat.csv")