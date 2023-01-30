Gender Labor Biased Technological Change with Schooling
=======================================================

The *structural-schooling* repository provides a collection of modular
scripts used to calibrate an economic model of technological structural
changes with households comprised of two individuals of distinct genders
with endogenous schooling choices. The model is semi-analytically
solvable and the optimization procedure for approximating its solutions
is nested in the calibration procedure. 

<img src='rsc/working-life-model.png' style="max-width:70%;margin:10px 15%;"/>

The model is part of the work on gender schooling differences by
[Karapanagiotis & Reimers (n.d.)](#ref-karapanagiotis2022). It combines the
structural change elements of the model of 
[Ngai & Petrongolo (2017)](#ref-ngai2017) with the educational choice 
elements of [Restuccia & Vandenbroucke (2014)](#ref-restuccia2014).


# Usage
The [calibration.py](src/calibration.py) script can be called from the shell
of the command line. An expected call with all options set is of the form
```bash 
python calibration.py -s <calibration_setup> -g <income_group> -i <initializers_file> -p <parameter_file> -o <output_path> -r <results_path> -l <log_path> -a <adaptive_mode> -v <verbose>
```
where 

- `calibration_setup` is the (extendable) calibration setup,
- `income_group` is a country-income group enumeration with values 
  [low, middle, high, all],
- `initializers_file` is a JSON file with initialing values for the
  calibrated free model parameters,
- `parameters_file` is a JSON file with values for the fixed model and
  calibration targets,
- `output_path` is a system path where the output files are stored,
- `results_path` is a system path where the tables and 
   visualizations of the calibration results are stored,
- `log_path` is a system path where the calibration log files are 
   stored,
- `adaptive_mode` is an option determining whether the nested 
   optimization procedure uses as initializing values 
   the calculated solution from the last calibration iteration, and
- `verbose` controls the verbosity level of the logger.

# Extend the Calibration Functionality

The calibration procedure can be easily extended to use different 
targets and weights. One can modify the `setups` of 
[calibration_traits.py](src/calibration_traits.py) and add a custom
calibration setup by inserting a key-callback pair at the
retiring dictionary. The callback is called after the default
initialization of the calibration data structure. Examples of how
to write a callback can be found in the same file. All function of
[calibration_traits.py](src/calibration_traits.py) using a `_prepare_`
prefix in their names are the callbacks used by the out-of-the-box
calibration setups.

# Design
The code is written using the functional paradigm to minimize the
possibility of side effects from the mathematical complications. The
implemented functions follow the derived equations for the semi-analytic
equilibrium solutions of the model. The implemented expressions can be
found in the online
appendix of [Karapanagiotis & Reimers (n.d.)](#ref-karapanagiotis2022).

# Dependencies

The nested calibration procedure is implemented in Python (originally
with version 3.8.10). We use NumPy (version 1.22.3) for vector
calculations. For the inner optimization procedure, we implement a
customized version of gradient descent with adaptive step size and 
additional validity checks based on the model's economic properties. For
the outer minimization problem, we use the Nelder-Mead implementation of
SciPy (version 1.3.3). The minimization routine can be modified by
setting the `["calibrator"]["method"]` value of the calibration data
dictionary created by `calibration.make_calibration_data`.

# Contributors

[Pantelis Karapanagiotis](https://www.pikappa.eu)

[Paul Reimers](https://www.wiwi.uni-frankfurt.de/profs/fuchs/reimers.php)

Feel free to share and distribute. If you would like to contribute, please
send a pull request.

# License

The code is distributed under the Expat [License](LICENSE).

# References

<div id="refs" class="references">

<div id="ref-karapanagiotis2022">

Karapanagiotis, Pantelis, and Reimers, Paul. (n.d.). “Why does the Schooling
Gap Close while the Wage Gap Persists across Country Income 
Comparisons?” Working Paper.
<https://doi.org/10.2139/ssrn.3525622>.

</div>

<div id="ref-ngai2017">

Ngai, L. R., & Petrongolo, B. (2017, October). Gender gaps and the rise of
the service economy. American Economic Journal: Macroeconomics, 9 (4), 1–44.
<https://doi.org/10.1257/mac.20150253>.

</div>

<div id="ref-restuccia2014">

Restuccia, D., & Vandenbroucke, G. (2014). Explaining educational attainment across
countries and over time. Review of Economic Dynamics, 17 (4), 824–841.
<https://doi.org/10.1016/j.red.2014.03.002>.

</div>

</div>
