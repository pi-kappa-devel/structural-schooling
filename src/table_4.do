*********************************************************************************
***   This code loads our country-income-group level data to compute table 4  ***
*********************************************************************************
clear all

/*Set cd to Gender Gaps directory*/
use "Data\Cleaned_data\sumstats_q_HCmod.dta" , clear
local a mod  

local q1 Low
local q2 Middle
local q3 High
local q4 All

local m Males 
local f Females

/*Maß data for income groups 1:1 into tex table*/
global name="data_labor_leisure_schooling"			
global write="file write ${name}"
global nextl=`"${write} ("\\") _n"'
global lastl=`"${write} ("\end{tabular}")"'
global close="file close ${name}"
				
local rp 2
file open ${name} using "text/jedc/tab/${name}.tex", write replace

*------------------------------------------------------------------------------*
$write ("\begin{tabular}{lcccccccccccc} ") _n
$write "\toprule \midrule" _n
*$write ("   &  \multicolumn{2}{c}{\textbf{\textit{Agric.}}} & &  \multicolumn{2}{c}{\textbf{\textit{Manuf.}}} & &  \multicolumn{2}{c}{\textbf{\textit{Services}}} &  & \textbf{\textit{Leisure}} && \textbf{\textit{School}} \\ ") _n
$write ("  \multirow{2}{*}{\textbf{Country Income Group}} & \multicolumn{2}{c}{\textbf{Agric.}} & &  \multicolumn{2}{c}{\textbf{Manuf.}} & &  \multicolumn{2}{c}{\textbf{Services}} &  & \textbf{Leisure} && \textbf{School.} \\ ") _n
$write ("   & $ L^{g}_{Ah} $ & $ L^{g}_{Ar} $ && $ L^{g}_{Mh} $ & $ L^{g}_{Mr} $ && $ L^{g}_{Sh} $ & $ L^{g}_{Sr} $ & & $ \ell^{g} $ & & $ s^{g} $ \\ ") _n
$write ("   \midrule") _n
		
foreach g in f m {
	$write ("  \multicolumn{13}{c}{\textbf{``g''}} \\ \midrule") _n
	egen hwp_`g'_`a'_sl = rowtotal(hwp_`g'_`a'_sah hwp_`g'_`a'_sam hwp_`g'_`a'_smh hwp_`g'_`a'_smm hwp_`g'_`a'_ssh hwp_`g'_`a'_ssm)
	replace hwp_`g'_`a'_sl = 112 - hwp_`g'_`a'_sl
	
		forvalues q = 1/3 {
		$write ( "\textbf{`q`q''}") 
			foreach s in ah am mh mm sh sm l {
				$write ("`l`v''")
				local x = round(hwp_`g'_`a'_s`s'[`q'], .01)
 				*local x = hwp_`g'_`a'_s`s'[`q']
				$write ("& `x' ")   /*\numprint[round-mode=places,round-precision=1]{`x'}*/
				if "`s'" == "am" | 	"`s'" == "mm"  | 	"`s'" == "sm" | 	"`s'" == "l"	{
					$write ("& ")
				}
			}
			local x = round(yr_sch_`g'_`a'[`q'],.1)
			$write ("& `x' ")
					
			$write ( "\\") _n
		}
		$write ( "\textbf{`q4'}") _n
			foreach s in ah am mh mm sh sm l {
				$write ("`l`v''")
				local x = round((hwp_`g'_`a'_s`s'[1] + hwp_`g'_`a'_s`s'[2] + hwp_`g'_`a'_s`s'[3])/3, .01)
					$write ("& `x' ")   /*\numprint[round-mode=places,round-precision=1]{`x'}*/
				if "`s'" == "am" | 	"`s'" == "mm"  | 	"`s'" == "sm" | 	"`s'" == "l"	{
					$write ("& ")
				}
			}
			local x = round((yr_sch_`g'_`a'[1] + yr_sch_`g'_`a'[2] + yr_sch_`g'_`a'[3])/3,.1)
			$write ("& `x' ")
					
		$write ( "\\") _n
			
		*$write ( "\rule{0pt}{2ex} \\" ) _n 
		$write ( " \bottomrule" ) _n

}	//gender
${lastl}
${close}	
	

