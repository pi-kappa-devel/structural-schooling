"""
Solver file for Why does the Schooling Gap Close when the Wage Gap Remains Constant?

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import model
import numpy as np
from importlib import reload

model = reload(model)

adaptive_optimizer_initialization = True
verbose = True

initializers = {
    "low": {
        "hat_c": 9.14372805352047,
        "varphi": 1.734066168909285,
        "beta_f": 0.4203204066647108,
        "Z_ArAh": 0.125554778691364,
        "Z_MrMh": 0.9522505707487174,
        "Z_SrSh": 0.15499427677725858,
        "Z_ArSr": 1.0022611645599255,
        "Z_MrSr": 16.531965509708265,
    },
    "middle": {
        "hat_c": 4.151718827645201,
        "varphi": 1.59748141012399,
        "beta_f": 0.3794130523513011,
        "Z_ArAh": 0.09467944783236808,
        "Z_MrMh": 2.073215080000164,
        "Z_SrSh": 0.1537037258927218,
        "Z_ArSr": 6.305131536817823,
        "Z_MrSr": 16.2178733018523,
    },
    "high": {
        "hat_c": 0.6277191879556749,
        "varphi": 1.3235400214854853,
        "beta_f": 0.5163446855687661,
        "Z_ArAh": 0.23164829737128284,
        "Z_MrMh": 4.142648994172241,
        "Z_SrSh": 0.1895014655945092,
        "Z_ArSr": 21.6906107672981,
        "Z_MrSr": 10.25425762798882,
    },
    "all": {
        "hat_c": 9.468789089099825,
        "varphi": 1.509445556273255,
        "beta_f": 0.4500793204862588,
        "Z_ArAh": 0.09755107569134108,
        "Z_MrMh": 2.0241204377455637,
        "Z_SrSh": 0.17321682756721676,
        "Z_ArSr": 3.718612070659791,
        "Z_MrSr": 13.403446832409394,
    },
}

calibration_modes = [
    "abs-schooling",
    "abs-schooling-no-wages",
    "abs-schooling-scl-wages",
    "base",
    "no-schooling",
    "no-schooling-scl-wages",
    "no-wages",
    # "no-income-no-wages",
]

output = {}
for calibration_mode in calibration_modes:
    output[calibration_mode] = {}
    calibration_results = {}
    for key, initializer in initializers.items():
        if calibration_mode == "no-income-no-wages":
            del initializer["hat_c"]
        calibration_results[key] = model.calibrate_if_not_exists_and_save(
            calibration_mode,
            key,
            initializer,
            adaptive_optimizer_initialization=adaptive_optimizer_initialization,
            verbose=verbose,
        )
        filename = f"../data/out/{calibration_mode}/{key}_income_calibration.pkl"
        solved_model = model.get_calibrated_model_solution(
            key, filename, initializers[key].keys()
        )
        output[calibration_mode][key] = {
            "values": np.append(
                calibration_results[key]["x"], solved_model["optimizer"]["x0"]
            ),
            "initializer": [*initializer.keys(), "tw", "sf", "sm"],
        }

for calibration_mode, calibration_results in output.items():
    print(f"calibration_mode = {calibration_mode}")
    names = calibration_results["all"]["initializer"]
    print(f"| group  | {' | '.join([f'{key:7}' for key in names])} |")
    for key, initializer in initializers.items():
        masks = [f"{{:>7.4f}}" for _ in names]
        values = [
            masks[k].format(v) for k, v in enumerate(calibration_results[key]["values"])
        ]
        print(f"| {key:6} | {' | '.join(values)} |")
