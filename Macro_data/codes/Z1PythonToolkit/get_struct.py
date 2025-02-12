# -*- coding: utf-8 -*-
"""
Created on Sun Sep 18 14:35:15 2016

@author: xguob
"""

#Main Section 
## Read the Structure Information
CL_dict=ParseStruct()

## Read the dataset 
Z1_data_root = ET.parse('Z1_data.xml').getroot()
## Return the list of the instruments available under the Household Sector
# Generate the search reference for HH sector

HH_search_id    =   genID(inst_code='',sect_code='15',pref_code='FL',\
                          freq_code='162',name_code='',type_code='')
HH_ds_sum       =   ParseFRB(Z1_data_root,HH_search_id,'sum_only',CL_dict,True)
HH_ds_sum       =   HH_ds_sum[HH_ds_sum.type_code!='6']
HH_ds_sum['flag']   =   pd.Series(HH_ds_sum.duplicated(['inst_code'],False)==False).astype('int')
HH_ds_sum.set_index('inst_code',inplace=True)
writer          =   pd.ExcelWriter('HH_sum.xlsx',engine='xlsxwriter')
HH_ds_sum[['name_code','curr_code','type_code','inst_text',\
           'description_s','flag']].sort_index().to_excel(writer)
writer.save()
