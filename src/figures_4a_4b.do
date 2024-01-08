*********************************************************************************
*** This code compiles the schooling data predicted by the model and compares ***
***    these values to our country level data to compute figures 4a and 4b    ***
*********************************************************************************
clear all

/*Set cd to Gender Gaps directory*/
use "Data/Cleaned_data/sample_modHC",  clear
local a mod 

forvalues t=1/2{
	sum t`t'_e9ry
	local t`t'=r(mean)
	global t`t' = r(mean)
}

foreach g in m f {
	egen M_`g'_CF0 = rowtotal(hwp_`g'_`a'_sam hwp_`g'_`a'_smm hwp_`g'_`a'_ssm),m 	
	gen s`g'_CF0 = yr_sch_`g'_`a'
}

local N1 = _N
local N = _N + 3
set obs `N'
gen id = .

local s_m_noschool_q1 = 7.5522
local s_m_noschool_q2 = 8.3759
local s_m_noschool_q3 = 10.4155
local s_f_noschool_q1 = 5.7369
local s_f_noschool_q2 = 7.7322
local s_f_noschool_q3 = 9.8589

gen s_m_noschool = .
gen s_f_noschool = .

forvalues q = 1/3 {
	local N1 = `N1'+1	

	sum ln_gdppc_e9ry if q_e9ry == `q'
		replace ln_gdppc_e9ry = r(mean) in `N1'
	
	foreach g in m f {
		sum M_`g'_CF0 if q_e9ry == `q'
			replace M_`g'_CF0 = r(mean) in `N1'
		sum s`g'_CF0 if q_e9ry == `q'
			replace s`g'_CF0 = r(mean) in `N1'

		replace s_`g'_noschool = `s_`g'_noschool_q`q'' 	in `N1'
	}
	
	replace id = `q' in `N1'
}

keep country q_e9ry ln_gdppc_e9ry M_m_CF0 M_f_CF0 s_* sm* sf*

replace country = "q" if country == ""

local mcol navy
local fcol cranberry
local options1 scheme(s2mono) graphregion(color(white) fcolor(white)) legend(region(lcolor(white))) xtitle("log(GDP per Capita)")
local sch_l 1(2)13
local M_l 0(5)30
local M_lf 0(5)20
local M_lm 10(5)30

local line_options xline(`t1', lpattern(dot) lcolor(gs5)) xline(`t2', lpattern(dot) lcolor(gs8))
local options1 scheme(s2mono) graphregion(color(white) fcolor(white)) legend(region(lcolor(background))) xtitle("log(GDP per Capita)")

local lms Years of schooling
local lfs Years of schooling

local lmh Hours
local lfh Hours

foreach g in m f { //m is figure 4a, f is figure 4b
 
local options2 msize(medlarge) /*mlab(country) mlabsize(small)*/ mlabpos(3) msymbol(x)  ylabel(`sch_l', angle(0)) xlabel(7(0.5)11) ytitle("`l`g's'") plotregion( m(b=0) ) //aspectratio(1.5)

graph twoway (scatter s`g'_CF0 ln_gdppc_e9ry if country != "q",  mcolor(`mcol'*0.60) `options2' msymbol(x)) ///
 			 (scatter s`g'_CF0 ln_gdppc_e9ry if country == "q",  mcolor(navy)  msymbol(d) msize(large) ) ///
			 (line s`g'_CF0 ln_gdppc_e9ry if country == "q",  lp(solid)  lw(medthick)) ///
			 (line s_`g'_noschool ln_gdppc_e9ry if country == "q", lp(longdash) lw(medthick) lcolor(cranberry)  ) ///
			 (scatter s_`g'_noschool ln_gdppc_e9ry if country == "q", mcolor(cranberry)  msymbol(o) msize(large)  ) ///
			 ,  `options1' `line_options'  legend(order (1 2 5) rows(1) label(1 "Country data") label(2 "Data averages") label(5 "Model predictions"))  aspectratio(0.75)
	*graph export "text/jedc/fig/g_pred_s`g'-no-school.pdf", as(pdf) replace
		
}	
		
