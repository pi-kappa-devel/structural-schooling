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

calibration_results = {}
for key, initializer in initializers.items():
    calibration_results[key] = model.calibrate_and_save(
        key,
        initializer,
        adaptive_optimizer_initialization=adaptive_optimizer_initialization,
        verbose=verbose,
    )
    solution = model.get_calibrated_model_solution(key, initializers[key])
    calibration_results[key]["y"] = np.append(
        calibration_results[key]["x"], solution[:-1]
    )
    initializer["tw"] = solution[0]
    initializer["sf"] = solution[1]
    initializer["sm"] = solution[2]

print(f"| group  | {' | '.join([f'{key:7}' for key in initializers['low'].keys()])} |")
for key, initializer in initializers.items():
    masks = [f"{{:>7.4f}}" for _ in initializers["low"].keys()]
    values = [masks[k].format(v) for k, v in enumerate(calibration_results[key]["y"])]
    print(f"| {key:6} | {' | '.join(values)} |")
