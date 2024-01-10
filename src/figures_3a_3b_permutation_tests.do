*********************************************************************************
*** This code compiles the wage gap data from the ilo (2018 and from Schober and 
*** Winter Ebmer (2011) manually, then loads our country level data to compare 
***                           and to compute figure 3b                        ***
*********************************************************************************
clear all

/*Manually compile the data from the ILO, see 
*https://www.ilo.org/wcmsp5/groups/public/---dgreports/---dcomm/---publ/documents/publication/wcms_650553.pdf
*On average over the world, women are paid 20% less than men (p. 23)
*/
local KOR 26.2 
local KORy 2016
local GHA . 
local KEN .
local RWA .
local KHM .
local PAK 36.3 
local PAKy 2015
local LKA 24.0 
local LKAy 2013
local UKR 19.1 
local UKRy 2012
local VNM 11.4 
local VNMy 2016
local BGD -4.7 
local BGDy 2017
local NPL 18.9 
local NPLy 2008
local MDG 17.1 
local MDGy 2012
local MWI 10.4 
local MWIy 2012
local TZA 7.7 
local TZAy 2014
local GMB 1.0 
local GMBy 2012
local UGA .
local URY 17.3 
local URYy 2016
local LTU 15.7 
local LTUy 2014
local CAN 15.4 
local CANy 2015
local LVA 21.6 
local LVAy 2014
local IRQ .
local BGR 18.7 
local BGRy 2014
local PRY 16.9 
local PRYy 2016
local PER 16.2 
local PERy 2016
local MEX 15.6 
local MEXy 2016
local JOR 15.5 
local JORy 2014
local ROM 12.4 
local ROMy 2014
local CRI 12.3 
local CRIy 2016
local BWA .
local POL 20.7 
local POLy 2014
local COL .
local MNG 17.0 
local MNGy 2016
local SLV 16.0 
local SLVy 2016
local PHL 15.7 
local PHLy 2016
local TUN 14.5
local TUNy 2014
local CPV 14.3 
local CPVy 2015
local EGY 12.6 
local EGYy 2012
local GRC .
local TUR 12.0 
local TURy 2015
local SVN 12.6 
local SVNy 2014
local FIN 19.1 
local FINy 2014
local SWE 10.2 
local SWEy 2014
local GBR 16.6 
local GBRy 2014
local NLD 8.8 
local NLDy 2014
local LUX 7.4 
local LUXy 2014
local CHE 6.8 
local CHEy 2016
local BEL 2.7 
local BELy 2015
local ESP 14.8 
local ESPy 2014
local AUS 13.3 
local AUSy 2016
local CYP 12.4 
local CYPy 2014
local FRA 13.3 
local FRAy 2014
local ARG 13.0 
local ARGy 2015
local CHL 23.7 
local CHLy 2013
local SVK 18.1 
local SVKy 2014
local USA 15.3 
local USAy 2014
local DEU .
local PRT 22.1 
local PRTy 2014
local CZE 19.6 
local CZEy 2014
local HUN 12.4 
local HUNy 2014
local NOR 11.7 
local NORy 2014
local ITA 11.0 
local ITAy 2014
local PAN 11.0 
local PANy 2016
local AUT . 
local MLT 10.2 
local MLTy 2014
local EST 25.7 
local ESTy 2014
local DNK 
local ECU 11.9 
local ECUy 2015
local ALB 11.2 
local ALBy 2013
local THA 10.9 
local THAy 2015
local ZAF 28.5 
local ZAFy 2015
local BRA 26.4 
local BRAy 2015
local ARM 26.3 
local ARMy 2015
local RUS 24.9 
local RUSy 2015
local CHN 20.8 
local CHNy 2013
local NAM 18.9 
local NAMy 2012

gen ilo_gap = .
gen year = .
gen country = ""
local countries  VNM UKR LKA PAK KOR BGD GBR SWE FIN SVN TUR EGY CPV TUN PHL SLV MNG POL CRI ROM JOR MEX PER PRY BGR LVA CAN LTU URY GMB TZA MWI MDG NPL  NAM CHN RUS ARM BRA ZAF THA ALB ECU EST MLT PAN ITA NOR HUN CZE PRT USA SVK CHL ARG FRA CYP AUS ESP BEL CHE LUX NLD
local N = _N+1
foreach c in `countries' {
display("Country `c'")
	set obs `N'
	replace country = "`c'" in `N'
	replace ilo_gap = ``c'' if country == "`c'"
	replace year = ``c'y' if country == "`c'"
	
	local N = `N'+1
}
replace year = 2014 if year > 2014 //We take 2014 max, as this is latest values we could compute in PWT 9

/*Merge with GDPPC (as in text, real 2005 Int Dollar) info and with our own data*/
merge 1:1 country year using "Data/Cleaned_data/gdppc_all.dta"
rename _merge merge1 
merge 1:1 country year using "Data/Cleaned_data/sample_modHC", keepusing(country year ln_gdppc_e9ry t1_e9ry t2_e9ry oax_e q_e9ry)

/*Now manually compile the wage gap data from the reported table in Schober and 
Winter-Ebmer 2011, see here
https://reader.elsevier.com/reader/sd/pii/S0305750X11001288?token=AEE73F2382CFFB08487E4829DA1ED287581661F9051EE6155D94EA785E4546901CF4C56CDA4C28CC39960FA2368DCA80&originRegion=eu-west-1&originCreation=20221107203746
*/
local BRA2 45.2
local CHL2 25.0
local CRI2 18.5
local SLV2 27.0
local HKG2 13.5
local IDN2 54.0
local KOR2 16.8
local MYS2 25.0
local MEX2 13.3
local PHL2 37.3
local PRT2 18.5
local SGP2 4.0
local TAI2 22.8
local THA2 21.9
local CHN2 25.8
local GTM2 18.4
local NIC2 63.1
local PAK2 26.6 
local PAN2 18.9
local ZAF2 51.1
local TZA2 7.3
local URY2 20.1
local ARG2 32.9 
local BRB2 21.1
local BOL2 38.0
local CAN2 21.2
local DNK2 10.6
local IND2 24.0
local IRL2 17.0
local KEN2 17.0  
local VNM2 11.4
local UGA2 31.2  
local LTU2 15.7
local LVA2 21.6
local IRQ2 .
local BGR2 18.7
local PER2 22.3
local ROM2 12.4
local BWA2 .
local POL2 34.5 
local COL2 11.5  
local MNG2 17.0
local TUR2 12.0
local SVN2 12.6
local FIN2 19.1
local SWE2 11.8 
local GBR2 18.8 
local NLD2 13.6 
local BEL2 2.7
local ESP2 20.7 
local CYP2 37.0 
local SVK2 18.0
local USA2 18.2 
local DEU2 21.2 
local CZE2 19.6
local HUN2 35.4
local ITA2 10.8 
local AUT2 25.1 
local AUS2 12.7
local FRA2 13.3
local EST2 25.7
local DNK2 10.6 
local ECU2 18.0 
local JPN2 40.4
local NZL2 19.6
local NOR2 18.5
local SDN2 29.6
local CHE2 19.9
local TTO2 34.1
local VEN2 23.1

/*Fill the data*/
local countries MNG POL ROM PER BGR LVA LTU UGA VNM PAK KEN IRL IND HKG DNK CAN BOL BRB ARG URY TZA ZAF PAN PAK NIC  KEN GTM CHN THA TAI SGP PRT PHL MEX MYS KOR IDN HKG SLV CRI COL CHL BRA VEN TTO CHE SDN NOR NZL JPN ECU DNK EST FRA AUS AUT ITA HUN CZE PRT DEU USA SVK CYP ESP BEL NLD GBR SWE FIN  SVN TUR
gen swe_gap = .
foreach c in `countries' {
display("Country `c'")
	replace swe_gap = ``c'2' if country == "`c'" & year == 1990
	
}

/*Compare to our data*/
replace oax_e = . if country == "ECU" //Data is totally inconsistent with other sources, there must be systematic issue
gen our_gap = (1-oax_e)*100
keep if our_gap != . | ilo_gap != . | swe_gap != .

gen ilo_ratio = 1-ilo_gap/100
gen swe_ratio = 1-swe_gap/100
gen our_ratio = 1-our_gap/100


/*Graphics*/
*Compute the threshold lines separating low-middle and middle-high income countries
sum t1_e9ry
	local t1 = r(mean) 
sum t2_e9ry
	local t2 = r(mean) 
local line_options xline(`t1', lpattern(dash) lcolor(gs5)) xline(`t2', lpattern(dash) lcolor(gs5))

*Some options
local options1 scheme(s2mono) graphregion(color(white) fcolor(white)) legend(rows(1) region(lcolor(white))) xtitle("log(GDP per Capita)")
local options2 mlabsize(vsmall)  mlabpos(3)  ylabel(, gmin gmax angle(0))  ytitle("Female/male wage ratio") xlabel(7(0.5)11.5)


graph twoway (scatter ilo_ratio ln_gdppc_e9ry, `options2' mcol(cranberry*0.75) /*mlab(country)*/  mlabcol(cranberry*0.5) msymbol(+) msize(medium) )	///
			 (scatter swe_ratio ln_gdppc_e9ry, `options2' mcol(orange*0.75) /*mlab(country)*/ mlabcol(orange*0.75) msymbol(x) msize(large) )	///
			 (scatter our_ratio ln_gdppc_e9ry, `options2' mcol(navy) mlab(country) mlabcol(navy) msymbol(d) msize(medlarge) ) ///
			 , aspectratio(0.85) `options1'  `line_options' legend(order(3 2 1) label(3 "Our data") label(1 "ILO 2018") label(2 "SWE-2011"))
	*graph export "text/jedc/fig/figure-3-b.png", as(png) replace 	
		

egen m_gap = rowmean(our_gap ilo_gap swe_gap)
bysort q_e9ry: sum our_gap our_ratio ilo_gap ilo_ratio swe_gap swe_ratio m_gap 

/*Compute permutation tests for differences in wage gaps/ratios across country income 
groups (switch v = swe_gap, or our_gap, or ilo_gap.*/
local v  swe_gap //our_gap //ilo_gap 
keep if `v' != .
*replace `v' = 1-`v'/100

forvalues q = 1/3 {
	count if q_e9ry == `q'
	local N`q' = r(N)
}

drop if country == "NIC" | country == "IDN" //to check their role for 
local its 10000
qui {

set obs `its'
gen obs = _n

gen diff = .

local sn 1
local savein 1
forvalues n = 1/`its' {
	set seed `sn'
	
	bysort q_e9ry: gen r`n' = runiform() if `v' != .
	
	sort q_e9ry r`n'
	bysort q_e9ry: gen n`n' = _n/_N if country != ""

			sum `v' if q_e9ry == 1 & n`n' < 1/3
				local q1 = r(mean)
			
			sum `v' if q_e9ry == 3 & n`n' < 1/3
				local q3 = r(mean)
				
			replace diff = `q1' - `q3'	 if obs == `savein'
		
	local sn = `sn'+1
	local savein = `savein'+1
	display(`savein')
	drop r`n'* n`n'*
}
}

sum diff*
*swe: diff = 10.2, std err 5.98; BUT: mostly dirven by outliers (NIC and IDN, 
*without them, diff = 5.86 but not significantly different from zero, std 4.44)
*	-0.10 & 0.059 bzw. -0.059 & 0.045
*ilo: -6.7, not significant (std err 8.4) ; 0.066 & 0.084 for ratios
*ours: -1.08, but not significant (std 5.78); 0.011 & 0.058 for ratios
	
