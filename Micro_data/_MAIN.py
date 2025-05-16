#%% Preamble 
# Key pacakges
import argparse
import subprocess
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import sys

# setup the path to the Python executable
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

#%% Functions to execute Python scripts and Jupyter notebooks
def run_python_script(script_path):
    """Run a Python script from a given path."""
    if not os.path.exists(script_path):
        print(f"[ERROR] Python script '{script_path}' not found.")
        return
    print(f"[INFO] Running Python script: {script_path}")
    subprocess.run([sys.executable, script_path], check=True)
    print(f"[INFO] Finished executing script: {script_path}")

def run_jupyter_notebook(notebook_path):
    """Run a Jupyter notebook from a given path."""
    if not os.path.exists(notebook_path):
        print(f"[ERROR] Notebook '{notebook_path}' not found.")
        return
    print(f"[INFO] Running Jupyter notebook: {notebook_path}")
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': os.path.dirname(notebook_path) or '.'}})
    print(f"[INFO] Finished executing notebook: {notebook_path}")

# def main():
#     parser = argparse.ArgumentParser(description="Run Python script or Jupyter notebook.")
#     parser.add_argument('file', help="Path to .py script or .ipynb notebook")
#     args = parser.parse_args()

#     if args.file.endswith('.py'):
#         run_python_script(args.file)
#     elif args.file.endswith('.ipynb'):
#         run_jupyter_notebook(args.file)
#     else:
#         print("[ERROR] Unsupported file type. Please provide a .py or .ipynb file.")

# if __name__ == '__main__':
#     main()

#%% Step 0: Construct the data sets 
# SDC sample 
"""
 Notes:
 Input data sets:
 Output data sets:
"""
run_python_script("Micro_data/codes/0_DataConstruction_1_SDC.py")

# CRSP stock price history 
"""
 Notes: 
 Input data sets:
 Output data sets:
 WARNING: This script takes a long time to run, and it requires a WRDS account to download these data.
"""
# run_python_script("Micro_data/codes/0_DataConstruction_2_DailyStockPriceHistory.py")

#%% Step 1: Data cleaning
# SDC issuance information 
"""
 Notes:
    This script cleans the SDC issuance information and generate a relatively clean sample for analysis.
 Input data sets:
    1. Micro_data/datasets/SDC/IssuanceSample.p
    2. Micro_data/datasets/SDC/SDC_CRSP_Info.p
 Output data sets:
    1. Micro_data/datasets/SDC/SDC_IssuanceInfo.p
"""
run_python_script("Micro_data/codes/1_DataCleaning_1_SDC_Sample.py")

# Daily stock price history associated with the SEOs in the cleaned SDC sample. 
"""
 Notes:
    This script cleans the daily stock price history associated with the SEOs in the cleaned SDC sample.
 Input data sets:
    1. Micro_data/datasets/SDC/CRSP_SDC.p
    2. Micro_data/datasets/SDC/CRSP_SP.p
    3. Micro_data/datasets/SDC/FF_FactorDaily.p
 Output data sets:
    1. Micro_data/datasets/SDC/SDC_Ret.p
"""
run_python_script("Micro_data/codes/1_DataCleaning_2_StockReturnHistory.py")

#%% Step 2: Compute various type of stock price changes associated with stock issuance
# Baseline: stock price change around event dates
"""
 Notes:
    This script computes the (non-filtered) stock price changes associated with stock issuance.
 Input data sets:
    1. Micro_data/datasets/SDC/SDC_IssuanceInfo.p
    2. Micro_data/datasets/SDC/SDC_Ret.p
 Output data sets:
    1. Micro_data/datasets/SDC/PriceChange.p
"""
run_python_script("Micro_data/codes/2_GenPriceChange_1_AccRet.py")
# Abnormal returns based on the factor model
"""
 Notes:
    This script computes the abnormal returns based on the various types of factor model.
 Input data sets:
    1. Micro_data/datasets/SDC/SDC_Ret.p
 Output data sets:
    1. Micro_data/datasets/SDC/SDC_AlphaBeta.p
"""
run_python_script("Micro_data/codes/2_GenAbRet_1_FactorModelRegression.py")



#%% Step 3: Analysis 
run_jupyter_notebook("Micro_data/codes/3_Analysis_1_EventStudy.ipynb")