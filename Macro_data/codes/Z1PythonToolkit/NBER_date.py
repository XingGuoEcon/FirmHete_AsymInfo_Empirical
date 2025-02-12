# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# This subfunction is used to creat the NBER recession period shadow
def NBER_date(ax,StartDate='1944-12-1',ShadowType='area',Xtype='DateTime'):
    limit   =   ax.get_ylim()
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
        if all(date_temp>pd.to_datetime(StartDate)):
            if Xtype=='DateTime':
                Xdate   =   date_temp
                Xlength =   datetime.timedelta(30)
            elif Xtype=='DecimalYear':
                Xdate   =   date_temp.year+date_temp.month/12
                Xdate   =   Xdate.tolist()
                Xlength =   1/12
            if ShadowType=='area':
                ax.fill_between(x=Xdate,y1=[limit[0],limit[0]],\
                        y2=[limit[1],limit[1]],edgecolor='pink',\
                        facecolor='pink',alpha=0.5)
            elif ShadowType=='interval':
                ax.fill_between(x=[Xdate[0],\
                                   Xdate[0]+Xlength],\
                                   y1=[limit[0],limit[0]],\
                                   y2=[limit[1],limit[1]],edgecolor='pink',\
                                   facecolor='blue',alpha=0.5)
                
                ax.fill_between(x=[Xdate[1],\
                                   Xdate[1]+Xlength],\
                                   y1=[limit[0],limit[0]],\
                                   y2=[limit[1],limit[1]],edgecolor='pink',\
                                   facecolor='red',alpha=0.5)
        
    ax.set_ylim(limit)       