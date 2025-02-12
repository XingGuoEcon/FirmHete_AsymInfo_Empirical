
clear all 
*cd  /Users/leticiajuarez/Desktop/RAwork/RA_summer_2020/GOW/
*insheet using "Dataset/RegSample.csv"
*save
use Dataset/RegSample.dta, clear

*Summary Statistics
tostring i_90d_mswidehf_calendarqtr_year, replace
g year = substr(i_90d_mswidehf_calendarqtr_year,3,2)
destring year, replace
label var i_90d_mswidehf_equity_common EquityCommon
label var i_90d_mswidehf_debt Debt
label var i_90d_mswidehf_sales Sales
label var i_90d_mswidehf_investment Investment
label var i_90d_mswidehf_stockprice_close StockPrice

eststo sum: estpost tabstat i_90d_mswidehf_equity_common i_90d_mswidehf_debt i_90d_mswidehf_sales i_90d_mswidehf_investment i_90d_mswidehf_stockprice_close  ///
	, statistics( mean sd max min p25 p50 p75 n) columns(statistics)  
esttab sum using "Updates/tableDI.tex", nonumber unstack cells("mean sd max min p25 p50 p75") title("Summary Statistics") label replace



*Regression
label var i_90d_mswidehf "Exposure" 
label var i_90d_mswidehf_offeredtotalshare "Primary/total outstanding shares" 
ffind sic, newvar(ffi) type(5)

local exposure "i_90d_mswidehf"
local macrocontrols "i_90d_mswidehf_gdpgrowth i_90d_mswidehf_inflation i_90d_mswidehf_unemploymentrate i_90d_mswidehf_fedfundsrate i_90d_mswidehf_spret_sum i_90d_mswidehf_spret_std"
local firm " i_abretrunup i_abretstd i_90d_mswidehf_leverage i_90d_mswidehf_offeredtotalshare i_90d_msrr_diff_logsales_lowquan i_90d_msrr_diff_logsales_uppquan i_90d_mswidehf_lag_asset_lowquan i_90d_mswidehf_lag_asset_uppquan ffi primarysecondaryflag onlysecondaryflag shelfissueflag"

*========================================================================================================

* Replicate regression

eststo rega: reg i_accabret_1_1  i_90d_mswidehf , robust
estadd local clustery "No" , replace
estadd local macroc "No" , replace
estadd local firmc "No" , replace
eststo regb: reg i_accabret_1_1  i_90d_mswidehf , vce(cluster year) 
estadd local clustery "Yes" , replace
estadd local macroc "No" , replace
estadd local firmc "No" , replace
eststo regc: reg i_accabret_1_1  i_90d_mswidehf `macrocontrols' `firm', vce(cluster year) 
estadd local clustery "Yes" , replace
estadd local macroc "Yes" , replace
estadd local firmc "No" , replace
eststo regd: reg i_accabret_1_1  i_90d_mswidehf `firm', vce(cluster year)
estadd local clustery "Yes" , replace
estadd local macroc "Yes" , replace
estadd local firmc "Yes" , replace

esttab rega regb regc regd using "Updates/tablereplicate.tex", p  unstack mtitle("Model 1" "Model 2" "Model 3" "Model 3" ) label s(clustery macroc firmc  N, label("Cluster Year" "Macro Controls" "Firm Characteristics")) drop(`macrocontrols' `firm') replace


*========================================================================================================

*Table 1: Base Regression and different FE

eststo reg01: reghdfe i_accabret_1_1  `exposure' ,noabsorb
estadd local fixed "No" , replace
estadd local macroc "No" , replace
estadd local firmc "No" , replace
estadd local Industry "No" , replace
estadd local Year "No" , replace

eststo reg02: reghdfe i_accabret_1_1  `exposure' `macrocontrols' ,  noabsorb
estadd local fixed "No" , replace
estadd local macroc "Yes" , replace
estadd local firmc "No" , replace
estadd local Industry "No" , replace
estadd local Year "No" , replace

eststo reg03: reghdfe i_accabret_1_1  `exposure' `macrocontrols' `firm' ,  noabsorb
estadd local fixed "No" , replace
estadd local macroc "Yes" , replace
estadd local firmc "Yes" , replace
estadd local Industry "No" , replace
estadd local Year "No" , replace

eststo reg04: reghdfe i_accabret_1_1  `exposure' `macrocontrols' `firm' ,  a(gvkey)
estadd local fixed "Yes" , replace
estadd local macroc "Yes" , replace
estadd local firmc "Yes" , replace
estadd local Industry "No" , replace
estadd local Year "No" , replace

eststo reg05: reghdfe i_accabret_1_1  `exposure' `macrocontrols' `firm' ,  a(gvkey ffi year2)
estadd local fixed "Yes" , replace
estadd local macroc "Yes" , replace
estadd local firmc "Yes" , replace
estadd local Industry "Yes" , replace
estadd local Year "Yes" , replace

esttab reg01 reg02 reg03 reg04 reg05 using "Updates/tableI.tex", p  unstack mtitle("Model 1" "Model 2" "Model 3" "Model 4" "Model 5") label s(macroc firmc fixed Industry Year N, label("Macro Controls" "Firm Characteristics" "Firm FE" "Industry FE" "Year2 FE")) drop(`macrocontrols' `firm') replace



*========================================================================================================
*Table 2: Assymetric Information Variables
*Potencial assymetric information variables
*age: i_90d_mswidehf_age_q_year1
*industry: ffi
eststo reg11: reghdfe i_accabret_1_1  `exposure' `macrocontrols' `firm' , a(gvkey) keepsingleton
estadd local fixed "Yes" , replace
eststo reg12: reghdfe i_accabret_1_1  `exposure' i_90d_mswidehf_age_q_year1 `macrocontrols' `firm' , a(gvkey)
estadd local fixed "Yes" , replace
eststo reg13: reghdfe i_accabret_1_1  `exposure' ffi `macrocontrols' `firm', noabsorb 
estadd local fixed "Yes" , replace
eststo reg14: reghdfe i_accabret_1_1  `exposure' i_90d_mswidehf_rdexp `macrocontrols' `firm' ,  a(gvkey)
estadd local fixed "Yes" , replace
eststo reg15: reghdfe i_accabret_1_1  `exposure' i_90d_mswidehf_age_q_year1 ffi i_90d_mswidehf_rdexp  `macrocontrols'  `firm',   noabsorb 
estadd local fixed "Yes" , replace
esttab reg11 reg12 reg13 reg14 reg15 using "Updates/tableII.tex",p  unstack mtitle("No AI" "Age as AI" "Industry as AI" "R and D as AI" "All AI") label s(fixed N , label("Firm FE")) replace


*========================================================================================================

*Table 3: By Categories
forval i = 1/5 {
eststo reg2`i': reghdfe i_accabret_1_1  `exposure' `macrocontrols' `firm' if ffi==`i' , a(gvkey year2) 
estadd local macroc "Yes" , replace
estadd local firmc "Yes" , replace
estadd local fixed "Yes" , replace
estadd local Year "Yes" , replace

}
esttab reg21 reg22 reg23 reg24 reg25 using "Updates/tableIII.tex",p unstack mtitle("Durables, NonDurables, Wholesales" "Manufacturing, Energy, Utilities" "Equipment, Telephone, TV" "Healthcare \& Drugs" "Other, Mines, Constr, BldMt, Trans, H") label s(macroc firmc fixed Industry Year N, label("Macro Controls" "Firm Characteristics" "Firm FE" "Industry FE" "Year2 FE")) drop(`macrocontrols' `firm') replace



*========================================================================================================




*VARIABLES
*Exposure: total sum of the monetary shocks during the 90 days right before: i_90d_mswidehf

****** Macro
*Gdp growth rate: i_90d_mswidehf_gdpgrowth
*Inflation: i_90d_mswidehf_inflation
*Unemployment: i_90d_mswidehf_unemploymentrate
*Average effective federal funds rate: i_90d_mswidehf_fedfundsrate
*Total S%P 500 index return: i_90d_mswidehf_spret_sum 
*Standard deviation of the S&P 500 index daily return: i_90d_mswidehf_spret_std

**** make them match 90 days always and wide

******Firm Level

* Age but with _____ 90 days

***First Group
*The total sum and volatility of the daily abnormal return history: i_abretrunup i_abretstd


***Second Group
*Leverage: i_90d_mswidehf_leverage not long term debt or other.
*Ratio between the offered primary shares and total outstanding common shares: i_90d_mswidehf_offeredtotalshare
*Dummy variables for whether the firm i’s sales growth rate is within the top 25% or bottom 25% quantile within the Compustat industrial firm population: i_90d_msrr_diff_logsales_lowquan i_90d_msrr_diff_logsales_uppquan
*Dummy variables for whether the firm i’s size is within the top 25% or bottom 25% quantile within the Compustat firm population: i_90d_mswidehf_lag_asset_lowquan i_90d_mswidehf_lag_asset_uppquan 

***Third Group
*Dummy variables for each firms’ industry category based on the Fama and French 5 industry group categorization: ffi
*Dummy variables for whether the issuance only has secondary shares, and whether the issuance includes both primary and secondary shares: primarysecondaryflag onlysecondaryflag
*Dummy variable for whether the issuance is shelf-registered under the SEC Rule 415: shelfissueflag




/*

Questions:
- for outcome varibale use 1,1
- pre(right before so dont use), 30, 90:
within the 90 day window etc

monetary 90
type of shock both 30,90


- wide or rr?
(rr = romer, wide window or narrow window )

- size
- number
- I,L,F: use i 

*/
