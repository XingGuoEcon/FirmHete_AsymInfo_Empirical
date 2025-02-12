# -*- coding: utf-8 -*-
"""
Code Introduction:
    This code 
Version History:
    Created: Tue Mar 19 11:49:18 2019
    Current: 

@author: Xing Guo (xingguo@umich.edu)

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as figpdf
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as TickerFun
#%% Creat the Standard PDF Graph Handle
def Graph_PDF(FileName,FigSize=(5,3),Dpi=200):
    
    PDF_Handle      =   figpdf.PdfPages(FileName)
    FIG_Handle      =   plt.figure(figsize=FigSize,dpi=Dpi)
    plt.rc('text',usetex=True)
    plt.rc('font',family='serif')
    
    return PDF_Handle, FIG_Handle

#%% Setup the Standard Axis Apperance 
def AxisFormatSetup(ax):
    
    ## Invisible Top and Right borders
    # close the borders
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    # delete the ticks
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    
    ## Format the Bottom and Left Borders
    # Bottom Border
    ax.spines['bottom'].set_bounds(max(np.min(ax.get_xticks()),ax.get_xlim()[0]), \
                                   min(np.max(ax.get_xticks()),ax.get_xlim()[1]))
    ax.spines['left'].set_bounds(max(np.min(ax.get_yticks()),ax.get_ylim()[0]), \
                                 min(np.max(ax.get_yticks()),ax.get_ylim()[1]))
    ## Add the Gridlines
    ax.grid('on',axis='both',linestyle='dashed',alpha=0.5) 
    return ax
    
#%% IRF Plot with Error Band
def IRF_SinglePlot(DS_IRF,IRFVarList,LineStyleList,LineColorList, \
                   ax=None,DS_STD=pd.DataFrame(),XVar='', \
                   LineWidthList=[],LineLabelList=[],XLabel='',YLabel='',Title='', \
                   ErrorBandWidth=1,XTickStep=None, \
                   YMax=-np.nan,YMin=np.nan,SymmetricY=True):
    ## Axis Handle
    if ax==None:
        ax              =   plt.figure().add_subplot(1,1,1)
        
    ## Data for XAxis
    if XVar=='':
        XAxis           =   DS_IRF.index
    else:
        XAxis           =   DS_IRF[XVar]
            
    ## Number of IRF Variables
    NumIRF          =   len(IRFVarList)
    
    ## Plot Error Band or not
    if (ErrorBandWidth<=0) | (DS_STD.empty):
        FlagErrorBand   =   0
    else:
        FlagErrorBand   =   1
        IRF_UppBound    =   DS_IRF[IRFVarList]+ErrorBandWidth*DS_STD[IRFVarList]
        IRF_LowBound    =   DS_IRF[IRFVarList]-ErrorBandWidth*DS_STD[IRFVarList]    
    
    ## IRF 
    for ii in range(NumIRF):
        # Line Width
        if (LineWidthList==[]) | (len(LineWidthList)!=NumIRF):
            TempWidth   =   3
        else:
            TempWidth   =   LineWidthList[ii]
        # Line Label
        if (LineLabelList==[]) | (len(LineLabelList)!=NumIRF):
            TempLabel   =   ''
        else:
            TempLabel   =   LineLabelList[ii]
        # Plot the Line
        if TempLabel=='':
            ax.plot(XAxis,DS_IRF[IRFVarList[ii]], \
                    linestyle=LineStyleList[ii],linewidth=TempWidth, \
                    color=LineColorList[ii])
        else:
            ax.plot(XAxis,DS_IRF[IRFVarList[ii]],label=TempLabel, \
                    linestyle=LineStyleList[ii],linewidth=TempWidth, \
                    color=LineColorList[ii])
        # Plot the Error Band
        if FlagErrorBand==1:
            ax.fill_between(XAxis, \
                            IRF_UppBound[IRFVarList[ii]],IRF_LowBound[IRFVarList[ii]], \
                            facecolor=LineColorList[ii],alpha=0.2)
     
    ## Axises Scale
    # X-Axis
    XMin            =   XAxis.min()
    XMax            =   XAxis.max()
    ax.set_xlim(XMin,XMax)        
    # Y-Axis
    if FlagErrorBand==1:
        YMax            =   np.nanmax([np.nanmax(IRF_UppBound[IRFVarList].values),YMax])
        YMin            =   np.nanmin([np.nanmin(IRF_LowBound[IRFVarList].values),YMin])
    else:
        YMax            =   np.nanmax([np.nanmax(DS_IRF[IRFVarList].values),YMax])
        YMin            =   np.nanmin([np.nanmin(DS_IRF[IRFVarList].values),YMin])
    
    if SymmetricY:
        AbsY            =   np.nanmax(np.abs([YMin,YMax]))
        YMax            =   AbsY
        YMin            =   -AbsY
    ax.set_ylim(YMin,YMax)   
    ## Axises Tickers
    # X-Axis
    if XTickStep==None:
        ax.xaxis.set_major_locator(TickerFun.MaxNLocator(nbins=4,steps=[4]))
    else:
        ax.xaxis.set_major_locator(TickerFun.MaxNLocator(steps=[XTickStep]))
    # Y-Axis
    ax.yaxis.set_major_locator(TickerFun.MaxNLocator(nbins=7,steps=[2,5,10]))
    
    ## Basic Setup
    # Benchmark Horizontal Line
    if (YMax>0) & (YMin<0):
        plt.axhline(y=0, linewidth=1,color='k',alpha=0.5)
    # Axis Labels
    if XLabel!='':
        plt.xlabel(XLabel,fontsize=12,**{'fontname':'serif'})
    if YLabel!='':
        plt.ylabel(YLabel,fontsize=12,**{'fontname':'serif'})
    # Legend
    if len(LineLabelList)==NumIRF:
        plt.legend(loc='best',frameon=False,fontsize=12)
    # Title
    if Title!='':
        plt.title(Title,fontsize=12,**{'fontname':'serif'})
        
    ax      =   AxisFormatSetup(ax)
    
    return ax
    



#%% Multiple Lines within a Single Plot with only the Left Y-Axis
def MultiLine_SinglePlot(DS,VarList,LineStyleList,LineColorList, \
                           ax=None,XVar='',
                           LineLabelList=[], \
                           LineWidth=3, \
                           YLabel='',XLabel='',Title='', \
                           YLimit=[-np.nan,np.nan], \
                           SymmetricY=False, \
                           YMid=None):

    ## Axis Handle
    if ax==None:
        ax              =   plt.figure().add_subplot(1,1,1)
    ## X-Axis
    # Scale
    if XVar=='':
        XAxis           =   DS.index
    else:
        XAxis           =   DS[XVar]
    XMin        =   XAxis.min()
    XMax        =   XAxis.max()
    
    ax.set_xlim(XMin,XMax)
    # Ticks
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    # Label
    if XLabel!='':
        plt.xlabel(XLabel,fontsize=15,**{'fontname':'serif'})
        
    ## Plots
    Num         =   len(VarList)
    LegendFlag  =   0
    for ii in range(Num):
        if LineLabelList==[]:
            TempLabel   =   ''
        else:
            TempLabel   =   LineLabelList[ii]

        if TempLabel=='':
            ax.plot(XAxis,DS[VarList[ii]], \
                    linestyle=LineStyleList[ii],linewidth=LineWidth, \
                    color=LineColorList[ii])
        else:
            LegendFlag  =   1
            
            ax.plot(XAxis,DS[VarList[ii]],label=TempLabel, \
                    linestyle=LineStyleList[ii],linewidth=LineWidth, \
                    color=LineColorList[ii])

    ## Y-Axis 
    # Scale
    YMax    =   np.nanmax([np.nanmax(DS[VarList].values),YLimit[1]])
    YMin    =   np.nanmin([np.nanmin(DS[VarList].values),YLimit[0]])
    
    if SymmetricY:
        if YMid==None:
            YMid    =   ( YMax+YMin )/2
        else:
            AbsY    =   np.nanmax(np.abs([YMin-YMid,YMax-YMid]))
            YMax    =   YMid+AbsY
            YMin    =   YMid-AbsY
        
    if YMid!=None:
        plt.axhline(y=YMid,linewidth=1,color='k',alpha=0.5)
    
    ax.set_ylim(YMin,YMax)
    # Ticks
    ax.yaxis.set_major_locator(MaxNLocator(steps=[5,10]))
    # Label
    if YLabel!='':
        plt.ylabel(YLabel,fontsize=15,**{'fontname':'serif'})
    # Legend
    if LegendFlag:
        ax.legend(loc='best',frameon=False,fontsize=12)
    
    if Title!='':
        plt.title(Title,fontsize=12,**{'fontname':'serif'})
        
    ax.grid('on',axis='both',linestyle='dashed',alpha=0.5)  
    
    return ax

#%% Multiple Lines within a Single Plot with 2 Y-Axis
def MultiLine_2ySinglePlot(DS,VarList,LineStyleList,LineColorList, \
                           ax=None,XVar='',
                           LineLabelList={'Left':[],'Right':[]}, \
                           LineWidth={'Left': 3,'Right':2}, \
                           YLabel={'Left': '','Right': ''},XLabel='',Title='', \
                           YLimit={'Left': [-np.nan,np.nan],'Right': [-np.nan,np.nan]}, \
                           SymmetricY={'Left': False,'Right': False}, \
                           YMid={'Left': 0, 'Right': 0}):

    ## Axis Handle
    if ax==None:
        ax              =   plt.figure().add_subplot(1,1,1)
    ## X-Axis
    # Scale
    if XVar=='':
        XAxis           =   DS.index
    else:
        XAxis           =   DS[XVar]
        
    XMin            =   XAxis.min()
    XMax            =   XAxis.max()
    
    ax.set_xlim(XMin,XMax)
    # Ticks
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    # Label
    if XLabel!='':
        plt.xlabel(XLabel,fontsize=12,**{'fontname':'serif'})
        
    AxList      =   {'Left': ax, 'Right': ax.twinx()}
    
    LegendFlag  =   0
    LineList    =   []
    for LR in ['Left','Right']:
        ## Axis
        TempAx              =   AxList[LR]
        ## Information about each line 
        TempVarList         =   VarList[LR]
        TempStyleList       =   LineStyleList[LR]
        TempColorList       =   LineColorList[LR]
        TempLabelList       =   LineLabelList[LR]
        TempYLimit          =   YLimit[LR]
        TempSymmetricY      =   SymmetricY[LR]
        TempYMid            =   YMid[LR]
        TempYLabel          =   YLabel[LR]
        TempWidth           =   LineWidth[LR]
        TempNum             =   len(TempVarList)
        
        
        
        ## Plots
        for ii in range(TempNum):
            if TempLabelList==[]:
                TempLabel   =   ''
            else:
                TempLabel   =   TempLabelList[ii]
    
            if TempLabel=='':
                TempAx.plot(XAxis,DS[TempVarList[ii]], \
                            linestyle=TempStyleList[ii],linewidth=TempWidth, \
                            color=TempColorList[ii])
            else:
                LegendFlag  =   1
                
                TempLine    =   TempAx.plot(XAxis,DS[TempVarList[ii]],label=TempLabel, \
                                            linestyle=TempStyleList[ii],linewidth=TempWidth, \
                                            color=TempColorList[ii])
                LineList    =   LineList+TempLine
    
        ## Y-Axis 
        # Scale
        TempYMax    =   np.nanmax([np.nanmax(DS[TempVarList].values),TempYLimit[1]])
        TempYMin    =   np.nanmin([np.nanmin(DS[TempVarList].values),TempYLimit[0]])
        
        if TempSymmetricY:
            TempAbsY    =   np.nanmax(np.abs([TempYMin-TempYMid,TempYMax-TempYMid]))
            TempYMax    =   TempYMid+TempAbsY
            TempYMin    =   TempYMid-TempAbsY
            plt.axhline(y=TempYMid,linewidth=1,color='k',alpha=0.5)
        
        TempAx.set_ylim(TempYMin,TempYMax)
        # Ticks
        TempAx.yaxis.set_major_locator(MaxNLocator(steps=[5,10]))
        # Label
        if TempYLabel!='':
            TempAx.set_ylabel(TempYLabel,fontsize=15,**{'fontname':'serif'})
        
    # Legend
    if LegendFlag:
        ax.legend(LineList,[x.get_label() for x in LineList],loc='best',frameon=False,fontsize=12)
        
    if Title!='':
        plt.title(Title,fontsize=12,**{'fontname':'serif'})
        
    ax.grid('on',axis='both',linestyle='dashed',alpha=0.5)  
    
    return ax

#%% NBER Recession Bar
def NBER_RecessionBar(ax,ShadowType='area',Xtype='DateTime'):
    import pandas as pd
    import datetime
    limit   =   ax.get_ylim()
    if Xtype=='DateTime':
        DateLimit   =   pd.to_datetime(ax.get_xlim())
    elif Xtype=='DecimalYear':
        DateLimit   =   ax.get_xlim()
        
    StartDate   =   DateLimit[0]
    EndDate     =   DateLimit[1]

    Date    =   [['1945-2-1',	'1945-10-1'],
                 ['1948-11-1','1949-10-1'],
                 ['1953-7-1','1954-5-1'],
                 ['1957-8-1','1958-4-1'],
                 ['1960-4-1','1961-2-1'],
                 ['1969-12-1','1970-11-1'],
                 ['1973-11-1','1975-3-1'],
                 ['1980-1-1','1980-7-1'],
                 ['1981-7-1','1982-11-1'],
                 ['1990-7-1','1991-3-1'],
                 ['2001-3-1','2001-11-1'],
                 ['2007-12-1','2009-6-1']]
    for date in Date:
        date_temp   =   pd.to_datetime(date)
        if Xtype=='DateTime':
            Xdate       =   date_temp
            Xlength     =   datetime.timedelta(30)
        elif Xtype=='DecimalYear':
            Xdate       =   date_temp.year+date_temp.month/12
            Xdate       =   Xdate.tolist()
            Xlength     =   1/12
        if all(Xdate>StartDate):   
            if ShadowType=='area':
                ax.fill_between(x=Xdate,y1=[limit[0],limit[0]],\
                        y2=[limit[1],limit[1]],edgecolor='pink',\
                        facecolor='pink',alpha=0.5)
            elif ShadowType=='interval':
                ax.fill_between(x=[Xdate[0],\
                                   Xdate[0]+Xlength],\
                                   y1=[limit[0],limit[0]],\
                                   y2=[limit[1],limit[1]],edgecolor='blue',\
                                   facecolor='blue',alpha=0.5)
                
                ax.fill_between(x=[Xdate[1],\
                                   Xdate[1]+Xlength],\
                                   y1=[limit[0],limit[0]],\
                                   y2=[limit[1],limit[1]],edgecolor='red',\
                                   facecolor='red',alpha=0.5)
        
    ax.set_ylim(limit)
    
    return ax