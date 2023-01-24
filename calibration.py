"""
Solver file for "Why does the Schooling Gap Close when the Wage Gap Remains Constant?".

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import calibration_mode
import config
import model

config_glob, modes = config.make_config_from_input()


def calibrate(mode):
    """Calibrate the model for a given mode."""
    config_init = config.prepare_config(config_glob, mode)

    output = {}
    for income_group, initializer in config_init["initializers"].items():
        if "no-income" in mode and "hat_c" in initializer:
            del initializer["hat_c"]
        solved_model = model.calibrate_and_save_or_load(mode, income_group, config_init)
        variables = list(solved_model["calibrated"].keys())
        output[income_group] = {
            "values": [
                *solved_model["calibrator"]["results"]["x"],
                *solved_model["optimizer"]["xstar"],
                solved_model["optimizer"]["xstar"][1]
                / solved_model["optimizer"]["xstar"][2],
                solved_model["calibrator"]["results"]["fun"],
                solved_model["calibrator"]["results"]["status"],
            ],
            "variables": [*variables, "tw", "sf", "sm", "ts", "error", "status"],
        }
        if "no-income" in mode:
            output[income_group]["values"] = [0, *output[income_group]["values"]]
            output[income_group]["variables"] = [
                "hat_c",
                *output[income_group]["variables"],
            ]

    return output


def print_results(output):
    """Print calibration results."""
    results = ""
    for mode, calibration_results in output.items():
        results = results + f"calibration_mode = {mode}\n"
        variables = calibration_results["all"]["variables"]
        results += f"| group  | {' | '.join([f'{key:7}' for key in variables])} |\n"
        masks = ["{:>7.4f}" for _ in variables]
        for group in calibration_results.keys():
            values = [
                masks[k].format(v)
                for k, v in enumerate(calibration_results[group]["values"])
            ]
            results = results + f"| {group:6} | {' | '.join(values)} |\n"
    with open("../tmp/calibrations-summary.org", "w") as f:
        f.write(results)
    print(results)


def get_calibrated_values(output, mode, group):
    """Get calibrated values."""
    return {
        output[mode][group]["variables"][i]: output[mode][group]["values"][i]
        for i in range(8)
    }


calibration_modes = calibration_mode.mapping()
calibration_modes = {k: v for k, v in calibration_modes.items() if k in modes}

output = {}
for mode, preparation_callback in calibration_modes.items():
    output[mode] = calibrate(mode)

print_results(output)
