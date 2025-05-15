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



