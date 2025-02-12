# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 20:57:12 2019

@author: Xing Guo
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm

def RomerRomerReg(RegSample,ResVar,ShockVar,SeasonVar, \
                  LagNum_Res,LagNum_Shock,LagMin_Shock, \
                  StartEndIndex=[], \
                  ResType='Original',IRFType='NonAccumulated'):
    RegData         =   RegSample.copy()
    ## Generate Response Variable
    if ResType=='Original':
        RegData['Res']      =   RegData[ResVar]
    elif (ResType=='Log'):
        RegData['Res']      =   np.log(RegData[ResVar])
    elif ResType=='Diff':
        RegData['Res']      =   RegData[ResVar].diff(1)
    elif ResType=='Log-Diff':
        RegData['Res']      =   np.log(RegData[ResVar]).diff(1)
    else:
        RegData['Res']      =   RegData[ResVar]
    ## Generate the Lag Variables
    # Shock Variable
    LagShockList    =   []
    if LagNum_Shock>0:
        for i in range(LagMin_Shock,LagNum_Shock+1):
            RegData['LagShock_'+str(i)]     =   RegData[ShockVar].shift(i)
            LagShockList.append('LagShock_'+str(i))
    # Response Variable
    LagResList      =   []
    if LagNum_Res>0:
        for i in range(1,LagNum_Res+1):
            RegData['LagRes_'+str(i)]       =   RegData['Res'].shift(i)
            LagResList.append('LagRes_'+str(i))
    ## Generate the Season Dummy Variables
    if SeasonVar!=[]:
        SeasonList      =   RegData[SeasonVar].unique().tolist()
        SeasonList.sort()
        if len(SeasonList)>1:
            SeasonIDList    =   []
            for ii in range(1,len(SeasonList)):
                TempSeasonID                =   'SeasonID_'+str(ii)
                RegData[TempSeasonID]       =   RegData[SeasonVar]*0
                RegData.loc[RegData[SeasonVar]==SeasonList[ii],TempSeasonID] \
                                            =   1
                SeasonIDList.append(TempSeasonID)
                
    ## Regression
    XVarList        =   LagShockList+LagResList+SeasonIDList
    if StartEndIndex!=[]:
        RegData         =   RegData[ (RegData.index>=StartEndIndex[0]) & \
                                     (RegData.index<=StartEndIndex[1])]
    RegResult       =   sm.OLS(endog=RegData['Res'], \
                               exog=sm.add_constant(RegData[XVarList]), \
                               missing='drop').fit()
    
    IRF             =   pd.DataFrame(RegResult.params[LagShockList],columns=[ResVar])
    IRF.index       =   pd.to_numeric(IRF.index.str.split(pat='_').str[1],downcast='integer')
    if IRFType=='Accumulated':
        IRF.sort_index(inplace=True)
        IRF[ResVar]     =   IRF[ResVar].cumsum()
        
        TempFullCov     =   RegResult.cov_params().loc[LagShockList,LagShockList]
        TempFullCov.index \
                        =   pd.to_numeric(TempFullCov.index.str.split(pat='_').str[1], \
                                          downcast='integer')
        TempFullCov.columns \
                        =   pd.to_numeric(TempFullCov.columns.str.split(pat='_').str[1], \
                                          downcast='integer')
        TempFullCov.sort_index(axis=0,inplace=True)
        TempFullCov.sort_index(axis=1,inplace=True)
        Temp_Std        =   []
        TempLagList     =   list(TempFullCov.index)
        for ii in range(len(TempLagList)):
            Temp_Std.append(np.sqrt( np.ones([1,ii+1])@ \
                                     TempFullCov.loc[TempLagList[0:ii+1],TempLagList[0:ii+1]]@ \
                                     np.ones([ii+1,1]) )[0][0])
        STD             =   pd.DataFrame(Temp_Std,index=TempLagList,columns=[ResVar])
    else:
        STD             =   pd.DataFrame(RegResult.bse[LagShockList],columns=[ResVar])
        STD.index       =   pd.to_numeric(STD.index.str.split(pat='_').str[1], \
                                          downcast='integer')
        STD.sort_index(axis=0,inplace=True)
    return IRF, STD, RegResult