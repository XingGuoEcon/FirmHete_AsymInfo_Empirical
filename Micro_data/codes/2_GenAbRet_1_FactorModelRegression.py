#%% Load in the packages
from _Public import *


#%% 1-Factor CAPM Regression => Alpha and Beta


### Setup
DataFolder      =   "Micro_data\\datasets\\SDC\\"
RegSample       =   pd.read_pickle(DataFolder+'SDC_Ret.p')



### Regression of factor models

## Sub-function for running a unit regression 
def TempSubFun_Reg(x, RetVar, FactorVarList, RfVar):
    Y           =   (x[RetVar] - x[RfVar]).values
    FactorData  =   [x[vv].values for vv in FactorVarList]
    X           =   np.column_stack([np.ones(x.shape[0])] + FactorData)
    RegCoef     =   np.linalg.lstsq(X,Y,rcond=None)[0]
    
    RegInfo     =   np.append(RegCoef,x.shape[0])
    InfoList    =   ['Alpha'] + ['Beta_'+vv for vv in FactorVarList] + ['Obs']
    
    return pd.DataFrame(RegInfo,index=InfoList).T
    
## Sub-function for running the factor regression for all issuance events given a regression specification
def FactorModelReg(DS, EventDateType='F', \
                   RetVar='DiffLogPrice', \
                   FactorVarList=['mktrf', 'smb', 'hml', 'rmw', 'cma'], \
                   RfVar='rf', \
                   RegWindow=(11, 160), \
                   RelativeDateType='Adj'):
    # Clean the sample 
    RelDateVar      =   EventDateType+'Date_'+RelativeDateType
    TempInd         =   DS[RelDateVar].between(RegWindow[0], RegWindow[1])
    TempVarList     =   ['IssueID'] + [RetVar, RfVar] + FactorVarList
    TempRegSample   =   DS.loc[TempInd,TempVarList].dropna()
    TempRegResult   =   TempRegSample.groupby('IssueID')[[RetVar, RfVar] + FactorVarList].apply(lambda x: TempSubFun_Reg(x, RetVar, FactorVarList, RfVar))
    TempRegResult.reset_index(level=1,drop=True,inplace=True)
    TempRegResult.reset_index(inplace=True)
    
    return TempRegResult


## Different model setups 
FF_Dict = {'FF5': ['mktrf', 'smb', 'hml', 'rmw', 'cma'], 'FF3': ['mktrf', 'smb', 'hml'], 'FF1': ['mktrf']}
RegWindow_Dict = {'PreEvent': [-160, -11], 'PostEvent': [11, 160]}
RegSetupDict = {}
for ff in ['FF5', 'FF3', 'FF1']:
    for window in ['PreEvent', 'PostEvent']:
        RegSetupDict[ff+'_'+window] = {'RetVar': 'DiffLogPrice', 'RfVar': 'rf', 'FactorVarList': FF_Dict[ff], \
                                       'RegWindow': RegWindow_Dict[window], 'RelativeDateType': 'Adj'}
### Regressions for Alpha and Beta

## Regression Results
RegResultDict = {} 
EventDateTypeList = ['F', 'L', 'I']
for RegSetup in RegSetupDict.keys():
    print(f"Starting the '{RegSetup}' factor regression:")
    TempDict = {}
    for EventDateType in EventDateTypeList:
        print(f"Event date type: '{EventDateType}'")
        TempDict[EventDateType] = FactorModelReg(RegSample, EventDateType=EventDateType, **RegSetupDict[RegSetup])
    RegResultDict[RegSetup] = pd.concat([TempDict[vv].set_index('IssueID') for vv in EventDateTypeList], \
                                        axis=1, join='outer', keys=EventDateTypeList)

### Save the regression results
SDC_AlphaBeta = {'RegSetupDict': RegSetupDict, 'RegResultDict': RegResultDict}
pickle.dump(SDC_AlphaBeta, open(DataFolder+"SDC_AlphaBeta.p", 'wb'))

