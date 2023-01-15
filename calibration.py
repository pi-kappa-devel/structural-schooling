"""
Solver file for "Why does the Schooling Gap Close when the Wage Gap Remains Constant?".

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import model
import calibration_mode

adaptive_optimizer_initialization = True
verbose = True

initializers = {
    "low": {
        "hat_c": 11.7882,
        "varphi": 1.8200,
        "beta_f": 0.3595,
        "Z_ArAh": 0.1025,
        "Z_MrMh": 0.9511,
        "Z_SrSh": 0.1609,
        "Z_ArSr": 1.0672,
        "Z_MrSr": 22.2323,
    },
    "middle": {
        "hat_c": 6.1534,
        "varphi": 1.7221,
        "beta_f": 0.4415,
        "Z_ArAh": 0.1560,
        "Z_MrMh": 2.0811,
        "Z_SrSh": 0.1758,
        "Z_ArSr": 6.7940,
        "Z_MrSr": 12.5163,
    },
    "high": {
        "hat_c": 0.7215,
        "varphi": 1.3723,
        "beta_f": 0.5823,
        "Z_ArAh": 0.2275,
        "Z_MrMh": 4.1438,
        "Z_SrSh": 0.2129,
        "Z_ArSr": 22.6727,
        "Z_MrSr": 7.5768,
    },
    "all": {
        "hat_c": 10.7180,
        "varphi": 1.6343,
        "beta_f": 0.4697,
        "Z_ArAh": 0.1351,
        "Z_MrMh": 2.0580,
        "Z_SrSh": 0.1761,
        "Z_ArSr": 3.7595,
        "Z_MrSr": 14.4149,
    },
}

calibration_modes = calibration_mode.mapping()
calibration_modes = {
    k: v for k, v in calibration_modes.items()
}

output = {}
for mode, preparation_callback in calibration_modes.items():
    output[mode] = {}
    calibration_results = {}
    for key, initializer in initializers.items():
        if mode == "no-income-no-wages":
            del initializer["hat_c"]
        calibration_results[key] = model.calibrate_if_not_exists_and_save(
            mode,
            key,
            initializer,
            adaptive_optimizer_initialization=adaptive_optimizer_initialization,
            verbose=verbose,
            preparation_callback=preparation_callback,
        )
        filename = f"../data/out/{mode}/{key}-income-calibration.pkl"
        solved_model = model.get_calibrated_model_solution(
            key, filename, initializer.keys(), preparation_callback=preparation_callback
        )
        names = list(initializer.keys())
        output[mode][key] = {
            "values": [
                *calibration_results[key]["x"],
                *solved_model["optimizer"]["x0"],
                solved_model["optimizer"]["x0"][1] / solved_model["optimizer"]["x0"][2],
                calibration_results[key]["fun"],
                calibration_results[key]["status"],
            ],
            "initializer": [*names, "tw", "sf", "sm", "ts", "error", "status"],
        }


results = ""
for mode, calibration_results in output.items():
    results = results + f"calibration_mode = {mode}\n"
    names = calibration_results["all"]["initializer"]
    results = results + f"| group  | {' | '.join([f'{key:7}' for key in names])} |\n"
    for key, initializer in initializers.items():
        masks = [f"{{:>7.4f}}" for _ in names]
        values = [
            masks[k].format(v) for k, v in enumerate(calibration_results[key]["values"])
        ]
        results = results + f"| {key:6} | {' | '.join(values)} |\n"
with open(f"../tmp/calibrations-{mode}.org", "w") as f:
    f.write(results)
print(results)
