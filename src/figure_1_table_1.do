*********************************************************************************
***   This code loads our country level data to computes figure 1 & table 1   ***
*********************************************************************************
clear all

/*Set cd to Gender Gaps directory*/
use "Data/Cleaned_data/sample_modHC", 

*Hours in paid work
egen Mf = rowtotal(hwp_f_mod_sam hwp_f_mod_smm hwp_f_mod_ssm), m
egen Mm = rowtotal(hwp_m_mod_sam hwp_m_mod_smm hwp_m_mod_ssm), m
egen Ma = rowtotal(hwp_a_mod_sam hwp_a_mod_smm hwp_a_mod_ssm), m

*Hours as counted in NIPA (excludes household services
egen Tf = rowtotal(hwp_f_mod_sam hwp_f_mod_smm hwp_f_mod_ssm hwp_f_mod_sah hwp_f_mod_smh ), m
egen Tm = rowtotal(hwp_m_mod_sam hwp_m_mod_smm hwp_m_mod_ssm hwp_m_mod_sah hwp_m_mod_smh ), m
egen Ta = rowtotal(hwp_a_mod_sam hwp_a_mod_smm hwp_a_mod_ssm hwp_a_mod_sah hwp_a_mod_smh ), m

*Ratios/Gaps
gen M_mf = Mm/Mf
gen M_fm = 1/M_mf
gen s_mf = yr_sch_m_mod/yr_sch_f_mod
gen s_fm = 1/s_mf
gen gap = 1-oax_e        //Oaxaca residual
gen ln_oax_e = ln(oax_e) //in log terms 

*Service share of economy is hours worked in paid services relative to NIPA hours
gen service_sh = (hwp_m_mod_ssm + hwp_f_mod_ssm)/(Tm + Tf)

order country q_e9ry ln_gdppc_e9ry oax_e gap s_mf service_sh M_mf yr_sch_m_mod  yr_sch_f_mod  Mf Mm 
keep country q_e9ry ln_gdppc_e9ry oax_e gap s_mf s_fm M_mf M_fm service_sh* yr_sch_m_mod  yr_sch_f_mod  Mf Mm  ln_oax_e

*in log terms
gen ln_smf = ln(s_mf)
gen ln_Mmf = ln(M_mf)
gen ln_sfm = ln(s_fm)
gen ln_Mfm = ln(M_fm)
gen ln_service_sh = ln(service_sh)
gen ln_gap = ln(gap)

**********
*Graphics
*Figure 1
local options1 scheme(s2mono) graphregion(color(white) fcolor(white)) legend(region(lcolor(white))) xtitle("log(Female/male paid hours ratio)")
local options2 msize(medlarge) mlab(country) mlabsize(small) mlabpos(3)  ytitle("log(Female/male schooling ratio)") 

graph twoway (scatter ln_sfm ln_Mfm if q_e9ry == 1, mlabcolor(cranberry) mcolor(cranberry) msymbol(d)  `options2') ///
			 (scatter ln_sfm ln_Mfm if q_e9ry == 2, mlabcolor(navy) mcolor(navy) msymbol(t) `options2') ///
			 (scatter ln_sfm ln_Mfm if q_e9ry == 3, mlabcolor(green) mcolor(green) msymbol(o) `options2') ///
			 (lfit ln_sfm ln_Mfm , lcolor(gs0) lp(dash)) /// 
			 , `options1'  legend(off)	 aspectratio(0.75)

	*graph export "text/jedc/fig/fit-log-schooling-log-paid-hours.png", as(png) replace
	
*Table 1:
eststo base: reg ln_sfm ln_Mfm  ,r 				                      
eststo base_ext: reg ln_sfm ln_Mfm if ln_oax_e != . ,r 				
eststo base_gdppc: reg ln_sfm ln_Mfm ln_oax_e ln_gdppc_e9ry  if ln_oax_e != . ,r 				  
eststo base_inc: reg ln_sfm ln_Mfm ln_oax_e ln_gdppc_e9ry i.q_e9ry if ln_oax_e != . ,r 				

eststo ext: reg ln_sfm ln_Mfm ln_oax_e ln_gdppc_e9ry ln_service_sh i.q_e9ry, r 

/*To export as table:
local outpc base base_ext base_inc ext 
esttab `outpc' using "text/jedc/fig/intro-regs.tex", order(ln_Mfm ln_oax_e ln_gdppc_e9ry ln_service_sh) coeflabels(ln_Mfm "Paid Hours Ratio" ln_oax_e "Wage Ratio" ln_gdppc_e9ry "GDPPC (in 2005 PPP adj. US \\$)" ln_service_sh "Share of services in NIPA hours") ///
	fragment nodepvars nonumbers nolines b(a2) replace nomti nocons se r2 nogaps star(* 0.10 ** 0.05 *** 0.01)	
*/	
	
**********
