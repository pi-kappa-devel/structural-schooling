*********************************************************************************
***   This code compiles, form the country level data, income group averages  ***
*********************************************************************************
clear all

/*Set cd to Gender Gaps directory*/
use "Data/Cleaned_data/sample_modHC", 

local a mod 
local g a

//Percentage of world population
egen pop_a = total(pop_9)        //population in sample
gen popsh = pop_a/1000/6.52		//52.7% of the world population represented
	
	
*Check number of countries in total
bysort q_e9ry: sum gdppc_e9ry 

*Check # of countries with nonmkt service hours
count if cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != . 
bysort q_e9ry: count if cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != . 
	forvalues q = 1/3 {
		count if (cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != . ) & q_e9ry == `q'
		local TUN`q' = r(N)
	}
	
bysort q_e9ry: sum hwp_a_all if (cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != . ) 
bysort q_e9ry: sum hwp_a_all if (cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != . )  & hwp_a_all_ssm != .
	
count if (cooking_`g'_`a'_uc != . | cleaning_`g'_`a'_uc != . | shopping_`g'_`a'_uc != . | collwf_`g'_`a'_uc != .  | childcare_`g'_`a'_uc != .) & hwp_`g'_`a'_ssm != .
egen t = rowtotal(cooking_`g'_`a'_uc cleaning_`g'_`a'_uc  shopping_`g'_`a'_uc collwf_`g'_`a'_uc childcare_`g'_`a'_uc )
order country hwp_`g'_`a'_ssm 	t
drop t

local vars  hwp	sh hwe

local sh Share (in %)
local sh_l 0(10)100
local hwe Hours per Employed
local hwe_l 0(5)60 
local hwp Hours per Week
local hwp_l 0(5)40 

local g_a Men \& Women
local g_m Men
local g_f Women
local g_r Ratio 

local var hwp

*Mkt hours: After education
*Nonmkt hours: already during education, so rename some variables (ending allx,
*which in compilation of country level data is all individuals aged, where poss-
*ible 5 years or older).
foreach g in a m f {
	foreach s in ah mh sh {
		drop `var'_`g'_mod_s`s'
		rename `var'_`g'_allx_s`s' hwp_`g'_mod_s`s'
	}
}

local main_ages mod //age groups for which we compile statistics, one of many dif-
//ferent ones in the country level data (f.e. ages 15-64, ages 25-55 etc.)
//mod is previously compiled for each country based on harmonized microdata, and
//encompasses the age group of the population consistent with the model: All indi-
//viduals aged 5 or older, and out of education (paid hours). For traditional 
//hours in agric and manufacture, we rename above the "allx" age group, which con-
//all individuals aged 5 or above, also those enrolled in education.
local gender a m f	//a

foreach a in `main_ages' {
	foreach v in `var'  {		//sh
		foreach g in `gender' { 
			local `v'mkt `v'_`g'_`a'_sam `v'_`g'_`a'_smm `v'_`g'_`a'_ssm
				
			local `v'g `v'_`g'_`a'_sam `v'_`g'_`a'_smm `v'_`g'_`a'_sah`xt' `v'_`g'_`a'_smh
			local `v'gm `v'_`g'_`a'_sam `v'_`g'_`a'_smm
			local `v'gh `v'_`g'_`a'_sah `v'_`g'_`a'_smh
				
			local ifmkt if `v'_`g'_`a'_sam != . & `v'_`g'_`a'_smm != . & `v'_`g'_`a'_ssm != . 
			local ifhom if `v'_`g'_`a'_sah != . & `v'_`g'_`a'_smh != . & `v'_`g'_`a'_ssh != . 
				
			foreach ss in mkt g gm gh {
				capture noisily drop `v'_`g'_`a'_s`ss'`xt'
				egen `v'_`g'_`a'_s`ss' = rowtotal(``v'`ss'') `ifmkt',m
			}	
		}
	}
}

//compile hours in household services from summing different activities
local vars cooking cleaning childcare collwf shopping
local cooking Cooking
local cleaning Cleaning
local childcare Caring
local collwf Coll. Water \& Firewood
local shopping Shopping

foreach a in `main_ages' {   //the relevant group here is stored under mod in prior codes
	foreach g in `gender' {
		forvalues q = 1/3 {
		local `var'_`g'_`a'_ssh_`q' = 0
		local tu_`g'_`a'_ssh_`q' = 0
			foreach v in `vars' {
					sum `v'_`g'_`a'_uc if q_e9ry == `q' 
					local m_`v'_`g'_`a'_`q' = r(mean)
					local N_`v'_`g'_`a'_`q' = r(N)
				
					local `var'_`g'_`a'_ssh_`q' = ``var'_`g'_`a'_ssh_`q'' + `m_`v'_`g'_`a'_`q''	
					local tu_`g'_`a'_ssh_`q' = `tu_`g'_`a'_ssh_`q'' + `m_`v'_`g'_`a'_`q''	
				
				if "`a'" == "all"   | "`a'" == "young" | "`a'" == "extyoung" {
					forvalues e = 0/1 {
						sum `v'_`g'_`a'_uc_educ`e' if q_e9ry == `q' 
							local m_`v'_`g'_`a'_`q'_educ`e' = r(mean)
							local N_`v'_`g'_`a'_`q'_educ`e' = r(N)
				
						local tu_`g'_`a'_ssh_`q'_educ`e' = `tu_`g'_`a'_ssh_`q'_educ`e'' + `m_`v'_`g'_`a'_`q'_educ`e''	
					}
				}
				
			}
		}
	}
}

foreach a in `main_ages' {
	foreach g in `gender' {
		foreach v in `var' {
			forvalues q = 1/3 {
					sum hwp_`g'_`a' if q_e9ry == `q' & `v'_`g'_mod_ssm != .
						local `v'_`g'_`a'`q' = r(mean)
						local `v'_`g'_`a'N`q' = r(N)
						
				foreach s in ah am mh mm sh sm /*mkt g gm gh*/ {  
				
					sum `v'_`g'_`a'_s`s' if q_e9ry == `q' `sumif' & `var'_`g'_mod_ssm != .
						local `v'_`g'_`a'_s`s'N`q' = r(N)
						
						if "`s'" == "sh" {
							local `v'_`g'_`a'_s`s'`q' = r(mean) + ``var'_`g'_`a'_ssh_`q''
							local `v'_`g'_`a'_s`s'`q'NIPA = r(mean) 
						}	
						if "`s'" != "sh" {
							local `v'_`g'_`a'_s`s'`q' = r(mean) 						
						}	//ifcond
					
					if "`a'" == "all" | "`a'" == "young" | "`a'" == "extyoung" {
						forvalues e = 0/1 {
						local aa `a'
						if  "`a'" == "mod" {
							local aa nonedu
						}
							sum `v'_`g'_`aa'_s`s'_educ`e' if q_e9ry == `q'  `sumif'
								local `v'_`g'_`a'_s`s'N`q'_educ`e' = r(N)
								
								if "`s'" == "sh" {
									local `v'_`g'_`a'_s`s'`q'_educ`e' = r(mean) + `tu_`g'_`a'_ssh_`q'_educ`e''
								}	
								if "`s'" != "sh"  {
									local `v'_`g'_`a'_s`s'`q'_educ`e' = r(mean) 						
								}	//ifcond	
						}
					}
				
				}	//sec				
			}	//q
		}	//v
		
	}	//gender
}	//age


//Now the schooling country income group averages
foreach a in mod {
local svars yr_sch_m_`a' yr_sch_f_`a' yr_sch_m_`a'_USage yr_sch_f_`a'_USage ln_gdppc_e9ry gdppc_e9ry LfExp_`a' VA_a VA_m VA_s oax_e
	foreach sv in `svars' {
		forvalues q = 1/3 {
			sum `sv' if q_e9ry == `q' `sumif' 
				local `sv'm`q' = r(mean)
				local `sv'N`q' = r(N)
				
		}	
	}	
}	
	
//Now that we have all the stats stored as locals, create and fill new dataset	
clear
set obs 3
gen q = _n

//fill in the hours averages
foreach a in `main_ages' {
	foreach v in `var' {
		foreach g in a m f {
			gen `v'_`g'_`a' = .
			gen `v'_`g'_`a'_N = .
			forvalues q = 1/3 {
				replace `v'_`g'_`a' = ``v'_`g'_`a'`q'' if q == `q'
				replace `v'_`g'_`a'_N = ``v'_`g'_`a'N`q'' if q == `q'
			}
			
			foreach s in ah am mh mm sh sm  {  
				gen `v'_`g'_`a'_s`s' = .	
				gen `v'_`g'_`a'_s`s'_educ0 = .
				gen `v'_`g'_`a'_s`s'_educ1 = .
				
				gen `v'_`g'_`a'_s`s'_N = .			
				
					forvalues q = 1/3 {
						replace `v'_`g'_`a'_s`s' = ``v'_`g'_`a'_s`s'`q'' if q == `q'
					
						if "`s'" != "sh" {
							replace `v'_`g'_`a'_s`s'_N = ``v'_`g'_`a'_s`s'N`q'' if q == `q'	
						}
						if "`a'" == "all" | "`a'" == "young" | "`a'" == "extyoung" {
							forvalues e = 0/1 {
								replace `v'_`g'_`a'_s`s'_educ`e' = ``v'_`g'_`a'_s`s'`q'_educ`e'' if q == `q'						
							}
						}
					}
			}
		}
	}
}
//fill in the schooling averages
foreach sv in `svars' {
	gen `sv' = .
	gen `sv'_N = .
	forvalues q = 1/3 {
		replace `sv' = ``sv'm`q'' if q == `q'
		replace `sv'_N = ``sv'N`q'' if q == `q'

	}	
}	

//sum across the household service activities
foreach v in cooking cleaning shopping childcare collwf {
	foreach a in `main_ages' {
		foreach g in a m f {
			gen  `v'_`g'_`a' = .
			gen `v'_`g'_`a'_N = .
			forvalues q = 1/3 {
				 replace `v'_`g'_`a' = `m_`v'_`g'_`a'_`q'' if q == `q'
				 replace `v'_`g'_`a'_N = `N_`v'_`g'_`a'_`q'' if q == `q'
			}
			local ord `ord' `v'_`g'_`a'
		}
	}
}

gen TU_N = .
foreach g in a m f {
foreach a in `main_ages' {
		gen TU_`g'_`a'_ssh = .
		gen NIPA_`g'_`a'_ssh = .
		forvalues q = 1/3 {
			replace TU_N = `TUN`q'' if q == `q'
			replace TU_`g'_`a'_ssh = `tu_`g'_`a'_ssh_`q'' if q == `q'
			replace NIPA_`g'_`a'_ssh = ``var'_`g'_`a'_ssh`q'NIPA' if q == `q'
		}
	}
}

*Market and nonmarket hour aggregates 
foreach a in `main_ages' {
	foreach g in a m f {
		egen N`g'_`a' = rowtotal(`var'_`g'_`a'_sah `var'_`g'_`a'_smh `var'_`g'_`a'_ssh),m
		egen N`g'_`a'_NIPA = rowtotal(`var'_`g'_`a'_sah `var'_`g'_`a'_smh NIPA_`g'_`a'_ssh),m

		egen M`g'_`a' = rowtotal(`var'_`g'_`a'_sam `var'_`g'_`a'_smm `var'_`g'_`a'_ssm),m
		
		if "`a'" == "all" | "`a'" == "young" | "`a'" == "extyoung"  {
			forvalues e = 0/1 {
				egen N`g'_`a'_educ`e' = rowtotal(`var'_`g'_`a'_sah_educ`e' `var'_`g'_`a'_smh_educ`e' `var'_`g'_`a'_ssh_educ`e'),m
				egen M`g'_`a'_educ`e' = rowtotal(`var'_`g'_`a'_sam_educ`e' `var'_`g'_`a'_smm_educ`e' `var'_`g'_`a'_ssm_educ`e'),m

			}
		}
		
		egen Tot_`g'_`a'_NIPA = rowtotal(M`g'_`a' N`g'_`a'_NIPA),m
		
	}
}

gen id = _n
	
save "Data/Cleaned_data/sumstats_q_HCmod.dta", replace	
