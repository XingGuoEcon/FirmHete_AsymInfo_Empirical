#%% Import Moduels

## System Tools
import sys
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
import scipy.stats as stats
## Database API
from fredapi import Fred
## API for WRDS
import wrds
idx =  pd.IndexSlice
# End of Section: Import Moduels
###############################################################################


#%% Setup Working Directory
DropboxDirList = ["B:\\Dropbox", "D:\\Dropbox"]

Flag_FindDropboxDir = False
for dir in DropboxDirList:
    if os.path.isdir(dir):
        os.chdir(dir)
        Flag_FindDropboxDir = True
        break
    
if not Flag_FindDropboxDir:
    raise FileNotFoundError("Dropbox directory not found. Please check the path.")

os.chdir("Research Projects\\02_HeteFirm_AsymetricInformation\\Data\\")


CodeFolder      =   "../../../Code/PythonLib/"

sys.path.append(CodeFolder)
# End of Section: Setup Working Directory
###############################################################################

#%% Frequently used functions
# Compute the weighted mean
def WeightedMean(DS,VarList,WeightVar):
    Temp_Num        =   DS[VarList].multiply(DS[WeightVar],axis=0).sum(axis=0)
    Temp_DeNum      =   ( ~pd.isna(DS[VarList]) ).multiply(DS[WeightVar],axis=0).sum(axis=0)
    WM              =   Temp_Num.divide(Temp_DeNum,axis=0)
    WM.name         =   'WMean'
    
    return WM

# Key statistics of returns 
def KeyRetStat(df):
    Num_Total = df.count()
    # Fraction of zero, positive, and negative values 
    Frac_0 = (df==0).sum()/Num_Total
    Frac_Pos = (df>0).sum()/Num_Total
    Frac_Neg = (df<0).sum()/Num_Total
    FracStat = pd.Series([Frac_0, Frac_Pos, Frac_Neg], index=['Frac_0', 'Frac_Pos', 'Frac_Neg'])
    # Mean, median, and standard deviation
    DescStat = df.describe(percentiles=[0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])

    return pd.concat([FracStat, DescStat], axis=0)

# Add the recession indicator
NBER_recessions = [
    (datetime.date(1980, 1, 1), datetime.date(1980, 7, 1)),
    (datetime.date(1981, 7, 1), datetime.date(1982, 11, 1)),
    (datetime.date(1990, 7, 1), datetime.date(1991, 3, 1)),
    (datetime.date(2001, 3, 1), datetime.date(2001, 11, 1)),
    (datetime.date(2007, 12, 1), datetime.date(2009, 6, 1)),
    # Add more recession periods as needed
]

def is_during_nber_recession(date):
    """
    Check if a given date falls within any NBER recession period.
'
    Parameters:
    date (datetime.date): The date to check.

    Returns:
    bool: True if the date is during an NBER recession, False otherwise.
    """
    for start, end in NBER_recessions:
        if start <= date <= end:
            return True
    return False