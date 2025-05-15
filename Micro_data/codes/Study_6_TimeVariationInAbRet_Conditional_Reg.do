clear 
cd "D:\Dropbox\Research Projects\02_HeteFirm_AsymetricInformation\Data\Micro_data\codes\"

use "../temp/AbRetCyclicality_withFirmInfo.dta"


********************************************************************************
* Clean the data
********************************************************************************
* Sector
generate NAICS_2 = substr(naics, 1, 2)
encode(NAICS_2), generate(NAICS_2_Code)
* Exchange 
encode(Exchange), generate(Exchange_Code)
* Firm id 
encode(gvkey), generate(gvkey_Code)
* Issuance size 
gen IssuanceSize = ProceedsAmount/MarketValue
* Calendar quarter 
gen Date = date(EventDate_Quarter, "YMD")
gen Year = year(Date)

********************************************************************************
* Check extreme values 
********************************************************************************
sum AccAbRet, d 
sum IssuanceSize, d
********************************************************************************
* Regression
********************************************************************************
reghdfe AccAbRet Lag_Asset_Quant Lag_Diff_LogSales_Quant Lag_Equity_M2B_Quant Lag_Leverage if AccAbRet>=-50 & AccAbRet<=50 & IssuanceSize<2 & Year>=1983, absorb(i.NAICS_2_Code i.NAICS_2_Code#c.Year i.Exchange_Code i.ShelfIssueFlag ) 

reghdfe AccAbRet Lag_Asset_Quant Lag_Diff_LogSales Lag_Equity_M2B Lag_Leverage Year if AccAbRet>=-50 & AccAbRet<=50 & IssuanceSize<2 & Year>=1983, absorb(i.NAICS_2_Code i.Exchange_Code i.ShelfIssueFlag ) 
// res(res_AccAbRet)

// reghdfe IssuanceSize Lag_Asset_Quant Lag_Diff_LogSales_Quant Lag_Equity_M2B_Quant Lag_Leverage if AccAbRet>=-50 & AccAbRet<=50 & IssuanceSize<2, absorb(i.NAICS_2_Code#i.Quarter i.Exchange_Code i.ShelfIssueFlag) res(res_IssuanceSize)
