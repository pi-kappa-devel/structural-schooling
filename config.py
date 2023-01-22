"""Configuration file."""

import datetime
import getopt
import json
import logging
import os
import sys

import calibration_mode


def make_config(
    mode,
    parameter_filename,
    initializers_filename,
    result_path,
    tmp_path,
    log_path,
    adaptive_optimizer_initialization,
    verbose,
):
    """Prepare configuration."""
    config = {}
    config["mode"] = mode
    config["parameter_filename"] = parameter_filename
    config["parameter"] = None
    config["initializers_filename"] = initializers_filename
    config["initializers"] = None

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    result_path = result_path.replace("timestamp", timestamp)
    log_path = log_path.replace("timestamp", timestamp)

    for path in [result_path, tmp_path, log_path]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    config["result_path"] = result_path
    config["tmp_path"] = tmp_path
    config["log_path"] = log_path
    config["logger"] = None

    config["adaptive_optimizer_initialization"] = adaptive_optimizer_initialization
    config["verbose"] = verbose

    return config


def make_config_from_input():
    """Prepare configuration."""
    usage_help = (
        f"{sys.argv[0]} -m <calibration_modes> -i <initializers.json> -p <parameters.json>"
        + " -r <results path> -t <temp path> -l <log path>"
        + " -a <adaptive_mode> -v <verbose_mode>"
    )

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hm:i:p:r:t:l:a:v:",
            [
                "help",
                "modes=",
                "input=",
                "parameters=",
                "results=",
                "temp=",
                "log=",
                "adaptive=",
                "verbose=",
            ],
        )
    except getopt.GetoptError:
        print("Error parsing input. Expected usage:\n", usage_help)
        sys.exit(2)

    modes = calibration_mode.mapping().keys()
    parameter_filename = "parameters.json"
    initializers_filename = "initializers.json"
    result_path = "../tmp/out.timestamp"
    tmp_path = "../tmp"
    log_path = "../tmp/log.timestamp"
    adaptive_optimizer_initialization = True
    verbose = True

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_help)
            sys.exit()
        elif opt in ("-m", "--modes"):
            modes = [arg]
        elif opt in ("-i", "--input"):
            initializers_filename = arg
        elif opt in ("-p", "--parameters"):
            parameter_filename = arg
        elif opt in ("-r", "--results"):
            result_path = arg
        elif opt in ("-t", "--temp"):
            tmp_path = arg
        elif opt in ("-l", "--log"):
            log_path = arg
        elif opt in ("-a", "--adaptive"):
            adaptive_optimizer_initialization = arg
        elif opt in ("-v", "--verbose"):
            verbose = arg

    if not modes:
        print("No calibration mode specified. Expected usage:\n", usage_help)

    return (
        make_config(
            None,
            parameter_filename=parameter_filename,
            initializers_filename=initializers_filename,
            result_path=result_path,
            tmp_path=tmp_path,
            log_path=log_path,
            adaptive_optimizer_initialization=adaptive_optimizer_initialization,
            verbose=verbose,
        ),
        modes,
    )


def setup_logger(config, mode):
    """Initialize logger."""
    calibration_modes = calibration_mode.mapping()
    if mode not in calibration_modes:
        raise ValueError(f"Calibration mode {mode} not found.")

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
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
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
    filename = f"{config['result_path']}/{config['mode']}/{income_group}-income-calibration.pkl"

    return filename
