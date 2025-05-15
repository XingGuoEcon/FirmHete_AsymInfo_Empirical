clear 
cd "D:\Dropbox\Research Projects\02_HeteFirm_AsymetricInformation\Data\Micro_data\codes\"

use "../results/Analysis_EventStudy/PriceChange.dta"


********************************************************************************
* Clean the data
********************************************************************************
* Exchange 
encode(Exchange), generate(Exchange_Code)
* Firm id 
// encode(gvkey), generate(gvkey_Code)
* Issuance size 
gen s_Funding = ProceedsAmount/MarketValue
* Calendar quarter 
gen Date = date(IssueDate_Quarter, "YMD")
gen Year = year(Date)

********************************************************************************
* Check extreme values 
********************************************************************************
sum PC_Total_Event PC_FirstEvent, d 
sum s_Share, d
sum s_Funding, d

********************************************************************************
* Regression
********************************************************************************
gen Flag_Sample = 1
replace Flag_Sample=0 if s_Share>2 | s_Share<0.0001
replace Flag_Sample=0 if s_Funding>2 | s_Funding<0.00001
replace Flag_Sample=0 if PC_Total_Event>0.5 | PC_Total_Event<-0.5

reghdfe PC_Total_Event s_Share if Flag_Sample==1, noabsorb 

reghdfe PC_Total_Event s_Share if Flag_Sample==1, absorb(i.FF10_Code#i.Year i.ShelfIssueFlag ) 

reghdfe PC_Total_Event s_Funding if Flag_Sample==1, absorb(i.FF10_Code#i.Year i.ShelfIssueFlag ) 
