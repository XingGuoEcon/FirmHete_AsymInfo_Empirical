
/*
*From csv to stata
clear all
cd  /Users/leticiajuarez/Desktop/RAwork/RA_summer_2020/GOW/
insheet using "Dataset/Sample_CleanedCS_Q.csv"
save
*/

clear all 
cd  /Users/leticiajuarez/Desktop/RAwork/RA_summer_2020/GOW/


use "Dataset/Sample_CleanedCS_Q.dta", clear
duplicates report gvkey fiscalqtr
g year = substr(calendarqtr,3,2)
destring year, replace
g quarter = substr(calendarqtr,6,1)
destring quarter, replace
duplicates report gvkey year quarter
save Cleaned_temp.dta, replace


*Merge Link + Reg.Sample
use "Dataset/Reg.Sampleold.dta", clear
merge 1:1 issueid using "Dataset/Link.dta"
drop if _merge==2

split filingdate_quarter, p(/)
split filingdate_year, p(/)

rename filingdate_quarter1 month
destring month, replace

g quarter = 1 if month==1 |month==2| month==3
	replace quarter= 2 if month==4 |month==5| month==6
	replace quarter= 3 if month==7 |month==8| month==9
	replace quarter = 4 if month==10 |month==11| month==12


rename filingdate_year3 year
destring year, replace

replace gvkey="1" if gvkey=="nan"
drop if gvkey=="1"
drop if year==.
drop if quarter==.
rename gvkey oldgvkey
g gvkey=substr(oldgvkey,1,5)
destring gvkey, replace
rename _merge merge1
duplicates report gvkey year quarter
save Reg_temp.dta, replace
merge m:1 gvkey year quarter using Cleaned_temp.dta
keep if _merge==3

*keep if _merge==3
*bysort gvkey: keep if _n==1
*sort gvkey
*drop if gvkey==gvkey[_n-1]



*erase Cleaned_temp.dta


*SEE HOW MANY ID MATCH

use Reg_temp.dta, clear
g base1=1
keep gvkey base1
sort gvkey
drop if gvkey==gvkey[_n-1] // 2321 observations
tempfile unique
save `unique'


use "Dataset/Sample_CleanedCS_Q.dta", clear //15625 observations
sort gvkey
drop if gvkey==gvkey[_n-1]
merge 1:1 gvkey using `unique'

*matched:521
erase Reg_temp.dta
*/

















/*

BEFORE USING DATE ----- ERASE THIS
split issueid, p(_) g(issue)
g year1 = substr(issue3,1,4)
g year2 = substr(issue4,1,4)
g month1= substr(issue3,4,2)
g month2= substr(issue4,4,2)

destring year* month*, replace
forvalues i = 1/2{
	g qtr`i' = 1 if month`i'==1 |month`i'==2| month`i'==3
	replace qtr`i' = 2 if month`i'==4 |month`i'==5| month`i'==6
	replace qtr`i' = 3 if month`i'==7 |month`i'==8| month`i'==9
	replace qtr`i' = 4 if month`i'==10 |month`i'==11| month`i'==12
}
*/

