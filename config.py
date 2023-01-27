"""Configuration file."""

import datetime
import getopt
import json
import logging
import os
import sys

import model_traits
import calibration_traits


def preconfigure():
    """Return default configuration placeholders."""
    return {
        "setup": None,
        "group": None,
        "parameters": "parameters.json",
        "initializers": "initializers.json",
        "paths": {
            "output": "../tmp/out.timestamp",
            "results": "../tmp/res.timestamp",
            "log": "../tmp/log.timestamp",
        },
        "logger": None,
        "adaptive_optimizer_initialization": True,
        "verbose": True,
    }


def make_output_data_filename(config):
    """Make output data filename."""
    output_path = config["paths"]["output"]
    filename = (
        f"{output_path}/{config['setup']}/{config['group']}-income-calibration.pkl"
    )

    return filename


def replace_path_timestamps(
    paths, timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
):
    """Replace timestamps in configuration paths."""
    return {
        key: path.replace("timestamp", timestamp) for key, path in paths.items() if path
    }


def load_parameters(filename, group):
    """Load parameters."""
    parameters = {}
    with open(filename) as f:
        data = json.load(f)
        if group in data:
            parameters = data[group]
        else:
            parameters = data[group]
    if parameters is None:
        raise ValueError("Failed to load parameter data.")

    return parameters


def load_initializers(filename, setup, group):
    """Load initializing values."""
    initializers = {}
    with open("initializers.json") as f:
        data = json.load(f)
        if setup in data and group in data[setup]:
            initializers = data[setup][group]
        else:
            initializers = data["default"][group]
    if initializers is None:
        raise ValueError("Failed to load initializing data.")

    return initializers


def setup_logger(config):
    """Initialize logger."""
    filename = None
    setup = config["setup"]
    group = config["group"]
    if "log" in config["paths"]:
        filename = f"{config['paths']['log']}/{setup}-{group}.log"
        if not os.path.exists(filename):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
    config["logger"] = logging.getLogger()
    config["logger"].setLevel(logging.INFO)
    handler = (
        logging.StreamHandler(sys.stdout)
        if filename is None
        else logging.FileHandler(filename)
    )
    if not filename:
        filename = "stdout"
    print(f"Logging to {filename}")
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    config["logger"].handlers.clear()
    config["logger"].addHandler(handler)
    config["logger"].info(f"Logging {setup} to {filename}")

    return config


def make_config(
    setup,
    group,
    parameter_filename,
    initializers_filename,
    output_path,
    results_path,
    log_path,
    adaptive_optimizer_initialization,
    verbose,
):
    """Create configuration."""
    if setup not in calibration_traits.setups():
        raise ValueError(f"Calibration setup {setup} not found.")
    if group not in model_traits.income_groups():
        raise ValueError(f"Income group {group} not found.")

    config = {}
    config["setup"] = setup
    config["group"] = group
    config["parameters"] = load_parameters(parameter_filename, group)
    config["initializers"] = load_initializers(initializers_filename, setup, group)
    config["paths"] = replace_path_timestamps(
        {"output": output_path, "results": results_path, "log": log_path}
    )

    for path in config["paths"].values():
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    config = setup_logger(config)

    config["adaptive_optimizer_initialization"] = adaptive_optimizer_initialization
    config["verbose"] = verbose

    return config


def make_config_from_input():
    """Create configuration from standard input."""
    usage_help = (
        f"{sys.argv[0]} -s <calibration_setup> -g <income_group>"
        + " -i <initializers.json> -p <parameters.json>"
        + " -o <output path> -r <results path> -l <log path>"
        + " -a <adaptive_mode> -v <verbose>"
    )

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hs:g:i:p:o:r:l:a:v:",
            [
                "help",
                "setup=",
                "group=",
                "input=",
                "parameters=",
                "output=",
                "results=",
                "log=",
                "adaptive=",
                "verbose=",
            ],
        )
    except getopt.GetoptError:
        print("Error parsing input. Expected usage:\n", usage_help)
        sys.exit(2)

    preconfig = preconfigure()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_help)
            sys.exit()
        elif opt in ("-s", "--setup"):
            preconfig["setup"] = arg
        elif opt in ("-g", "--group"):
            preconfig["group"] = arg
        elif opt in ("-i", "--input"):
            preconfig["initializers"] = arg
        elif opt in ("-p", "--parameters"):
            preconfig["parameter"] = arg
        elif opt in ("-o", "--output"):
            preconfig["paths"]["output"] = arg
        elif opt in ("-r", "--results"):
            preconfig["paths"]["results"] = arg
        elif opt in ("-l", "--log"):
            preconfig["paths"]["log"] = arg
        elif opt in ("-a", "--adaptive"):
            preconfig["adaptive_optimizer_initialization"] = arg
        elif opt in ("-v", "--verbose"):
            preconfig["verbose"] = arg

    if not preconfig["setup"]:
        print("No calibration setup specified. Expected usage:\n", usage_help)
        sys.exit(2)
    if not preconfig["group"]:
        print("No income group specified. Expected usage:\n", usage_help)
        sys.exit(2)

    return make_config(
        setup=preconfig["setup"],
        group=preconfig["group"],
        parameter_filename=preconfig["parameters"],
        initializers_filename=preconfig["initializers"],
        output_path=preconfig["paths"]["output"],
        results_path=preconfig["paths"]["results"],
        log_path=preconfig["paths"]["log"],
        adaptive_optimizer_initialization=preconfig[
            "adaptive_optimizer_initialization"
        ],
        verbose=preconfig["verbose"],
    )
