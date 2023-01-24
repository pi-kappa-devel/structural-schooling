"""Configuration file."""

import datetime
import getopt
import json
import logging
import os
import sys

import calibration_mode


def preconfigure():
    """Return default configuration placeholders."""
    return {
        "mode": None,
        "parameter_filename": "parameters.json",
        "parameters": None,
        "initializers_filename": "initializers.json",
        "initializers": None,
        "output_path": "../tmp/out.timestamp",
        "results_path": "../tmp/res.timestamp",
        "log_path": "../tmp/log.timestamp",
        "logger": None,
        "adaptive_optimizer_initialization": True,
        "verbose": True,
    }


def setup_timestamps(
    config, timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
):
    """Replace timestamps in configuration paths."""
    config["output_path"] = config["output_path"].replace("timestamp", timestamp)
    config["results_path"] = config["results_path"].replace("timestamp", timestamp)
    config["log_path"] = config["log_path"].replace("timestamp", timestamp)

    return config


def make_config(
    mode,
    parameter_filename,
    initializers_filename,
    output_path,
    results_path,
    log_path,
    adaptive_optimizer_initialization,
    verbose,
):
    """Prepare configuration."""
    config = {}
    config["mode"] = mode
    config["parameter_filename"] = parameter_filename
    config["parameters"] = None
    config["initializers_filename"] = initializers_filename
    config["initializers"] = None
    config["output_path"] = output_path
    config["results_path"] = results_path
    config["log_path"] = log_path

    config = setup_timestamps(config)

    for path in [config["output_path"], config["results_path"], config["log_path"]]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    config["logger"] = None

    config["adaptive_optimizer_initialization"] = adaptive_optimizer_initialization
    config["verbose"] = verbose

    return config


def make_config_from_input():
    """Prepare configuration."""
    usage_help = (
        f"{sys.argv[0]} -m <calibration_modes> -i <initializers.json> -p <parameters.json>"
        + " -o <output path> -r <results path> -l <log path>"
        + " -a <adaptive_mode> -v <verbose_mode>"
    )

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hm:i:p:o:r:l:a:v:",
            [
                "help",
                "modes=",
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

    modes = calibration_mode.mapping().keys()
    preconfig = preconfigure()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_help)
            sys.exit()
        elif opt in ("-m", "--modes"):
            modes = [arg]
        elif opt in ("-i", "--input"):
            preconfig["initializers_filename"] = arg
        elif opt in ("-p", "--parameters"):
            preconfig["parameter_filename"] = arg
        elif opt in ("-o", "--output"):
            preconfig["output_path"] = arg
        elif opt in ("-r", "--results"):
            preconfig["results_path"] = arg
        elif opt in ("-l", "--log"):
            preconfig["log_path"] = arg
        elif opt in ("-a", "--adaptive"):
            preconfig["adaptive_optimizer_initialization"] = arg
        elif opt in ("-v", "--verbose"):
            preconfig["verbose"] = arg

    if not modes:
        print("No calibration mode specified. Expected usage:\n", usage_help)

    return (
        make_config(
            None,
            parameter_filename=preconfig["parameter_filename"],
            initializers_filename=preconfig["initializers_filename"],
            output_path=preconfig["output_path"],
            results_path=preconfig["results_path"],
            log_path=preconfig["log_path"],
            adaptive_optimizer_initialization=preconfig[
                "adaptive_optimizer_initialization"
            ],
            verbose=preconfig["verbose"],
        ),
        modes,
    )


def setup_logger(config, mode):
    """Initialize logger."""
    calibration_modes = calibration_mode.mapping()
    if mode not in calibration_modes:
        raise ValueError(f"Calibration mode {mode} not found.")

    filename = None
    if config["log_path"]:
        filename = f"{config['log_path']}/{mode}.log"
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
    config["logger"].info(f"Logging {mode} to {filename}")

    return config


def load_parameters(config):
    """Load parameters."""
    parameters = {}
    with open("parameters.json") as f:
        parameters = json.load(f)
    if parameters is None:
        raise ValueError("Failed to load parameter data.")

    config["parameters"] = parameters
    return config


def load_initializers(config, mode):
    """Load initializing values."""
    calibration_modes = calibration_mode.mapping()
    if mode not in calibration_modes:
        raise ValueError(f"Calibration mode {mode} not found.")

    initializers = {}
    with open("initializers.json") as f:
        data = json.load(f)
        if mode in data:
            initializers = data[mode]
        else:
            initializers = data["default"]
    if initializers is None:
        raise ValueError("Failed to load initializing data.")

    config["initializers"] = initializers
    return config


def prepare_mode_config(config, mode):
    """Prepare mode configuration."""
    calibration_modes = calibration_mode.mapping()
    if mode not in calibration_modes:
        raise ValueError(f"Calibration mode {mode} not found.")
    config["mode"] = mode
    config["preparation_callback"] = calibration_modes[mode]

    config = setup_logger(config, mode)
    config = load_parameters(config)
    config = load_initializers(config, mode)

    return config


def make_output_data_filename(config, income_group):
    """Make output data filename."""
    filename = f"{config['output_path']}/{config['mode']}/{income_group}-income-calibration.pkl"

    return filename
