

use  "Data/Cleaned_data/sumstats_q_HCmod.dta", replace  
local ages mod //nonedu //25_64
local a `ages'

rename yr_sch_m_`a' sm
rename yr_sch_f_`a' sf

gen T = LfExp_`a'
local rho = 0.04
gen a_T = -1/`rho'*exp(-`rho'*T) + 1/`rho'

local sp 4.0 //4.0
local nu 0.58 //
	gen nu = `nu'
local theta = 0.32 //`nu'*`sp'^(`nu'-1)
	gen theta = `theta'
local fac 1.0 //157968
	gen fac = `fac'
		
	
foreach g in m f {
	gen H_s`g' = `fac'*exp(`theta'/(1-`nu')*s`g'^(1-`nu'))
	gen Hd_s`g' = s`g'^(-`nu')*`theta'*H_s`g'
	
	gen d_s`g' = 1/(-`rho')*exp((-`rho')*T) - 1/(-`rho')*exp((-`rho')*s`g')	
	gen dd_s`g' = - exp((-`rho')*s`g')
	
	gen dH_`g' = d_s`g'*H_s`g'
	
	gen A_s`g' = Hd_s`g'/H_s`g' + dd_s`g'/d_s`g'
}

gen tdH = dH_f/dH_m
gen td = d_sf/d_sm
gen tH = H_sf/H_sm
gen tT = (T-sf)/(T-sm)
gen tTH = (T-sf)/(T-sm)*tH		
		

*------------------------------------------------------------------------------*
*	Hours
*------------------------------------------------------------------------------*
gen hwp_f_`a'_sl = 112 - (hwp_f_`a'_sah + hwp_f_`a'_sam + hwp_f_`a'_smh + hwp_f_`a'_smm + hwp_f_`a'_ssh + hwp_f_`a'_ssm)
gen hwp_m_`a'_sl = 112 - (hwp_m_`a'_sah + hwp_m_`a'_sam + hwp_m_`a'_smh + hwp_m_`a'_smm +  hwp_m_`a'_ssh + hwp_m_`a'_ssm)

gen eta = 2.27
gen eta_l = 0.19

local keepv

foreach s in  am  mm  sm {
	gen r_`s' = hwp_m_`a'_s`s'/hwp_f_`a'_s`s'
	gen txi_`s' = (r_`s'/tTH/(oax_e^eta))^(-1/eta)
	gen xi_`s' = txi_`s'/(1+txi_`s')

	local keepv `keepv' xi_`s'

}

foreach s in  ah  mh  sh l {
	gen r_`s' = hwp_m_`a'_s`s'/hwp_f_`a'_s`s'
	gen txi_`s' = r_`s'^(-1/eta)*(tdH*oax_e)
	gen xi_`s' = txi_`s'/(1+txi_`s')
	
	local keepv `keepv' xi_`s'
}


keep `keepv' oax_e

export delimited "C:\Users\paulr\Google Drive-Streaming\.shortcut-targets-by-id\16Qaxl3QACGN7NQkT0Ixjt21Ql7j_v_Sy\GenderGaps\data/xi_params.csv", delim(",")
