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
    config_init = config.prepare_mode_config(config_glob, mode)

    solution = {}
    for income_group, initializer in config_init["initializers"].items():
        if "no-income" in mode and "hat_c" in initializer:
            del initializer["hat_c"]
        solution[income_group] = model.calibrate_and_save_or_load(mode, income_group, config_init)

    return solution


calibration_modes = calibration_mode.mapping()
calibration_modes = {k: v for k, v in calibration_modes.items() if k in modes}

solutions = {}
for mode, preparation_callback in calibration_modes.items():
    solutions[mode] = calibrate(mode)
