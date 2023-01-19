"""
Solver file for "Why does the Schooling Gap Close when the Wage Gap Remains Constant?".

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import copy

import calibration_mode
import model

adaptive_optimizer_initialization = True
verbose = True

initializers = {
    "low": {
        "hat_c": 11.136503727229076,
        "varphi": 1.721467380725994,
        "beta_f": 0.383367250170399,
        "Z_ArAh": 0.11947311619961784,
        "Z_MrMh": 0.92640548905085,
        "Z_SrSh": 0.15103457470449383,
        "Z_ArSr": 1.4131381675366543,
        "Z_MrSr": 13.53463375468326,
    },
    "middle": {
        "hat_c": 5.937606000914109,
        "varphi": 1.7195629729163815,
        "beta_f": 0.40735231284001816,
        "Z_ArAh": 0.12397402049398179,
        "Z_MrMh": 2.0783552343617036,
        "Z_SrSh": 0.1670283484738908,
        "Z_ArSr": 5.6793908085572244,
        "Z_MrSr": 13.521797777088413,
    },
    "high": {
        "hat_c": 1.3673004612957913,
        "varphi": 1.4606948832351896,
        "beta_f": 0.5671970749855282,
        "Z_ArAh": 0.23306653682422618,
        "Z_MrMh": 4.204202203663769,
        "Z_SrSh": 0.210277998867694,
        "Z_ArSr": 17.992392497711336,
        "Z_MrSr": 7.013943163527987,
    },
    "all": {
        "hat_c": 11.188021966353041,
        "varphi": 1.6067459794916912,
        "beta_f": 0.4598589272755898,
        "Z_ArAh": 0.1204204304831647,
        "Z_MrMh": 2.0214064754297816,
        "Z_SrSh": 0.17948743189748145,
        "Z_ArSr": 3.125525466231803,
        "Z_MrSr": 11.504307530807974,
    },
}

calibration_modes = calibration_mode.mapping()
calibration_modes = {
    k: v for k, v in calibration_modes.items() if k == "no-schooling-scl-wages"
}

output = {}
for mode, preparation_callback in calibration_modes.items():
    output[mode] = {}
    calibration_results = {}
    for key, invariant_initializer in initializers.items():
        initializer = copy.deepcopy(invariant_initializer)
        if "no-income" in mode:
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
        masks = ["{:>7.4f}" for _ in names]
        values = [
            masks[k].format(v) for k, v in enumerate(calibration_results[key]["values"])
        ]
        results = results + f"| {key:6} | {' | '.join(values)} |\n"
with open("../tmp/calibrations-summary.org", "w") as f:
    f.write(results)
print(results)
