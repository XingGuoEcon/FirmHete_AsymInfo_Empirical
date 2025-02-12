# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 17:28:11 2016

@author: admin
"""

import xml.etree.ElementTree as ET
import pandas as pd

#Class Definition Section

        


class Parse_RST:
    def __init__(self,data=[],sum=[],flag=[]):
        self.data = data
        self.sum  = sum
        self.flag = flag


#Function Definition Section
def genID(inst_code='',sect_code='',pref_code='',freq_code='',name_code='',\
          type_code='',CodeLists_dict={}):
    "This function is used to generate the search reference to be used in ParseFRB"
    ID                   =   {}
    ID['code']           =   {}
    ID['text']           =   {}
    ID['code']['inst']   =   inst_code
    ID['code']['sect']   =   sect_code
    ID['code']['pref']   =   pref_code
    ID['code']['freq']   =   freq_code
    ID['code']['name']   =   name_code
    ID['code']['type']   =   type_code
#    ID['text']['inst']   =   CodeLists_dict['inst'][inst_code]
#    ID['text']['sect']   =   CodeLists_dict['sect'][sect_code]
    return ID
    
def ParseFRB(search_root,search_ID,rst_type='sum_only',CodeLists_dict={},TextName=False):
    "this function is used to parse the data given the key reference"
    frb_ns  =   'http://www.federalreserve.gov/structure/compact/common'
    kf_ns   =   'http://www.federalreserve.gov/structure/compact/Z1_Z1'
    SERIES  =   {'inst':"[@SERIES_INSTRUMENT=",'sect':"[@SERIES_SECTOR=",
                 'pref':"[@SERIES_PREFIX=",'freq':"[@FREQ=",\
                 'name':"[@SERIES_NAME=",'type':"[@SERIES_TYPE="}
    xpath_series = ".//{"+kf_ns+"}Series"
    for key in search_ID['code'].keys():
        if search_ID['code'][key]!='':
            xpath_series = xpath_series+SERIES[key]+"'"+search_ID['code'][key]+"']"      
    
    search_rst   =   search_root.findall(xpath_series)
    search_flag  =   len(search_rst)
    if rst_type=='sum_only':
        if CodeLists_dict!={} and TextName==True:
            rst_sum      =   pd.DataFrame([[elem.attrib['SERIES_NAME'],\
                                            elem.attrib['SERIES_SECTOR'],\
                                            elem.attrib['SERIES_INSTRUMENT'],\
                                            elem.attrib['SERIES_PREFIX'],\
                                            elem.attrib['FREQ'],\
                                            elem.attrib['CURRENCY'],\
                                            elem.attrib['SERIES_TYPE'],\
                                            elem.attrib['UNIT'],\
                                            elem.attrib['UNIT_MULT'],\
                                            CodeLists_dict['sect'][elem.attrib['SERIES_SECTOR']],\
                                            CodeLists_dict['inst'][elem.attrib['SERIES_INSTRUMENT']],\
                                            CodeLists_dict['pref'][elem.attrib['SERIES_PREFIX']],\
                                            CodeLists_dict['freq'][elem.attrib['FREQ']],\
                                            CodeLists_dict['curr'][elem.attrib['CURRENCY']],\
                                            CodeLists_dict['type'][elem.attrib['SERIES_TYPE']],\
                                            CodeLists_dict['unit'][elem.attrib['UNIT']],\
                                            CodeLists_dict['mult'][elem.attrib['UNIT_MULT']],\
                                            elem[0][0][1].text,\
                                            elem[0][1][1].text]\
                                        for elem in search_rst],\
                                     columns=['name_code',\
                                              'sect_code','inst_code',\
                                              'pref_code','freq_code',\
                                              'curr_code','type_code',\
                                              'unit_code','mult_code',\
                                              'sect_text','inst_text',\
                                              'pref_text','freq_text',\
                                              'curr_text','type_text',\
                                              'unit_text','mult_text',\
                                              'description_s',\
                                              'description_l'])
        else:
            rst_sum      =   pd.DataFrame([[elem.attrib['SERIES_NAME'],\
                                            elem.attrib['SERIES_SECTOR'],\
                                            elem.attrib['SERIES_INSTRUMENT'],\
                                            elem.attrib['SERIES_PREFIX'],\
                                            elem.attrib['FREQ'],\
                                            elem.attrib['CURRENCY'],\
                                            elem.attrib['SERIES_TYPE'],\
                                            elem.attrib['UNIT'],\
                                            elem.attrib['UNIT_MULT'],\
                                            elem[0][0][1].text]\
                                        for elem in search_rst],\
                                     columns=['name_code',\
                                              'sect_code','inst_code',\
                                              'pref_code','freq_code',\
                                              'curr_code','type_code',\
                                              'unit_code','mult_code',\
                                              'description_s'])
        
        return rst_sum
    elif rst_type=='data_only':
        xpath_obs    =   ".//{"+frb_ns+"}Obs"
        rst_data     =   []
        for series in search_rst:
            df_rst       =   pd.DataFrame([[elem.attrib['TIME_PERIOD'],\
                                            elem.attrib['OBS_VALUE'],\
                                            elem.attrib['OBS_STATUS']]\
                                      for elem in series.findall(xpath_obs)],\
                            columns=['TIME_PERIOD','OBS_VALUE','OBS_STATUS'])
            rst_data.append(df_rst)
        return rst_data
    elif rst_type=='both':
        search_flag  =   len(search_rst)
        if CodeLists_dict!={} and TextName==True:
            rst_sum      =   pd.DataFrame([[elem.attrib['SERIES_NAME'],\
                                            elem.attrib['SERIES_SECTOR'],\
                                            elem.attrib['SERIES_INSTRUMENT'],\
                                            elem.attrib['SERIES_PREFIX'],\
                                            elem.attrib['FREQ'],\
                                            elem.attrib['CURRENCY'],\
                                            elem.attrib['SERIES_TYPE'],\
                                            elem.attrib['UNIT'],\
                                            elem.attrib['UNIT_MULT'],\
                                            CodeLists_dict['sect'][elem.attrib['SERIES_SECTOR']],\
                                            CodeLists_dict['inst'][elem.attrib['SERIES_INSTRUMENT']],\
                                            CodeLists_dict['pref'][elem.attrib['SERIES_PREFIX']],\
                                            CodeLists_dict['freq'][elem.attrib['FREQ']],\
                                            CodeLists_dict['curr'][elem.attrib['CURRENCY']],\
                                            CodeLists_dict['type'][elem.attrib['SERIES_TYPE']],\
                                            CodeLists_dict['unit'][elem.attrib['UNIT']],\
                                            CodeLists_dict['mult'][elem.attrib['UNIT_MULT']],\
                                            elem[0][0][1].text,\
                                            elem[0][1][1].text]\
                                        for elem in search_rst],\
                                     columns=['name_code',\
                                              'sect_code','inst_code',\
                                              'pref_code','freq_code',\
                                              'curr_code','type_code',\
                                              'unit_code','mult_code',\
                                              'sect_text','inst_text',\
                                              'pref_text','freq_text',\
                                              'curr_text','type_text',\
                                              'unit_text','mult_text',\
                                              'description_s',\
                                              'description_l'])
        else:
            rst_sum      =   pd.DataFrame([[elem.attrib['SERIES_NAME'],\
                                            elem.attrib['SERIES_SECTOR'],\
                                            elem.attrib['SERIES_INSTRUMENT'],\
                                            elem.attrib['SERIES_PREFIX'],\
                                            elem.attrib['FREQ'],\
                                            elem.attrib['CURRENCY'],\
                                            elem.attrib['SERIES_TYPE'],\
                                            elem.attrib['UNIT'],\
                                            elem.attrib['UNIT_MULT'],\
                                            elem[0][0][1].text]\
                                        for elem in search_rst],\
                                     columns=['name_code',\
                                              'sect_code','inst_code',\
                                              'pref_code','freq_code',\
                                              'curr_code','type_code',\
                                              'unit_code','mult_code',\
                                              'description_s'])
        xpath_obs    =   ".//{"+frb_ns+"}Obs"
        rst_data     =   []
        for series in search_rst:
            df_rst       =   pd.DataFrame([[elem.attrib['TIME_PERIOD'],\
                                            elem.attrib['OBS_VALUE'],\
                                            elem.attrib['OBS_STATUS']]\
                                      for elem in series.findall(xpath_obs)],\
                            columns=['TIME_PERIOD','OBS_VALUE','OBS_STATUS'])
            rst_data.append(df_rst)
        return Parse_RST(rst_data,rst_sum,search_flag)
def ParseStruct(write=False):
    "This function is used to parse the data structure, generate a table/dict,\
     or print the Code Lists"
    CL_elem = ET.parse('Z1_struct.xml').getroot()[1]
    CL  =   {'type':CL_elem[0],'inst':CL_elem[1],'sect':CL_elem[2],\
             'pref':CL_elem[3],'curr':CL_elem[4],'unit':CL_elem[5],\
             'mult':CL_elem[6],'freq':CL_elem[7],'stts':CL_elem[8]}
    CL_table =CL.copy()
    CL_dict = CL.copy()
    if write==True:
        writer  =   pd.ExcelWriter('CodeLists.xlsx',engine='xlsxwriter')
    for key in CL.keys():
        CL_table[key] = pd.DataFrame([[elem.attrib['value'], elem[0].text] \
        for elem in CL[key][1:] ],columns=['code','text'])
        CL_table[key].set_index('code',inplace=True)
        CL_dict[key]  = CL_table[key].to_dict()['text'] 
        if write==True:
            CL_table[key].to_excel(writer,sheet_name=key)
    if write==True:
        writer.save()
    return CL_dict


                             
