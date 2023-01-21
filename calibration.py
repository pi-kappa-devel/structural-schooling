"""
Solver file for "Why does the Schooling Gap Close when the Wage Gap Remains Constant?".

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import datetime
import getopt
import json
import logging
import os
import sys

import calibration_mode
import model

usage_help = (
    f"{sys.argv[0]} -m <calibration_modes> -i <initializers.json> -p <parameters.json>"
    + " -a <adaptive_mode> -v <verbose_mode>"
)

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hm:i:p:a:v:",
        ["help", "modes=", "input=", "parameters=", "adaptive=", "verbose="],
    )
except getopt.GetoptError as err:
    print("Error parsing input. Expected usage:\n", usage_help)
    print(err)
    sys.exit(2)

modes = []
initialization_file = "initializers.json"
targets = "parameters.json"
adaptive_optimizer_initialization = True
verbose = True

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print(usage_help)
        sys.exit()
    elif opt in ("-m", "--modes"):
        if arg == "all":
            modes = calibration_mode.mapping().keys()
        else:
            modes = arg
        print(modes)
    elif opt in ("-i", "--input"):
        initialization_file = arg
    elif opt in ("-p", "--parameters"):
        targets = arg
    elif opt in ("-a", "--adaptive"):
        adaptive_optimizer_initialization = arg
    elif opt in ("-v", "--verbose"):
        verbose = arg

if not modes:
    print("No calibration mode specified. Expected usage:\n", usage_help)


def calibrate(mode):
    """Calibrate the model for a given mode."""
    calibration_modes = calibration_mode.mapping()
    if mode not in calibration_modes:
        raise ValueError(f"Calibration mode {mode} not found.")
    filename = f"log/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{mode}.log"
    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    logging.basicConfig(
        filename=filename,
        level=logging.DEBUG,
        force=True,
        format="%(levelname)s: %(message)s",
    )

    initializers = {}
    with open("initializers.json") as f:
        data = json.load(f)
        if mode in data:
            initializers = data[mode]
        else:
            initializers = data["default"]
    if initializers is None:
        raise ValueError("Failed to load initializing data.")

    parameters = {}
    with open("parameters.json") as f:
        parameters = json.load(f)
    if parameters is None:
        raise ValueError("Failed to load parameter data.")

    output = {}
    calibration_results = {}
    for key, initializer in initializers.items():
        if "no-income" in mode:
            del initializer["hat_c"]
        calibration_results[key] = model.calibrate_if_not_exists_and_save(
            mode,
            key,
            initializer,
            parameters=parameters,
            adaptive_optimizer_initialization=adaptive_optimizer_initialization,
            verbose=verbose,
            preparation_callback=preparation_callback,
        )
        filename = f"../data/out/{mode}/{key}-income-calibration.pkl"
        solved_model = model.get_calibrated_model_solution(
            key,
            filename,
            initializer.keys(),
            parameters=parameters,
            preparation_callback=preparation_callback,
        )
        variables = list(initializer.keys())
        output[key] = {
            "values": [
                *calibration_results[key]["x"],
                *solved_model["optimizer"]["x0"],
                solved_model["optimizer"]["x0"][1] / solved_model["optimizer"]["x0"][2],
                calibration_results[key]["fun"],
                calibration_results[key]["status"],
            ],
            "variables": [*variables, "tw", "sf", "sm", "ts", "error", "status"],
        }
        if "no-income" in mode:
            output[key]["values"] = [0, *output[key]["values"]]
            output[key]["variables"] = ["hat_c", *output[key]["variables"]]

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


initializers = {}
with open("initializers.json") as f:
    initializers = json.load(f)


calibration_modes = calibration_mode.mapping()
calibration_modes = {k: v for k, v in calibration_modes.items() if k in modes}

output = {}
for mode, preparation_callback in calibration_modes.items():
    output[mode] = calibrate(mode)

print_results(output)
