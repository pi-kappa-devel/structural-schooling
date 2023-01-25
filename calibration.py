"""Calibration file.

Version of Model with two types of production technologies (traditional and modern),
three sectors (agriculture, manufacturing, and services), genders , and schooling.
Each household consist of a female and a male. Modern production occurs only after
schooling. Firms choose effective labor units.

@see "Why does the Schooling Gap Close while the Wage Gap Persists across Country
Income Comparisons?".
"""

import numpy as np
import os
import pickle
import scipy
import scipy.optimize

import calibration_mode
import config
import model


def make_calibration_objective(model_data):
    """Prepare calibration function."""
    min_sae = 100

    def errors(y):
        nonlocal model_data, min_sae
        model_data = model.set_calibrated_data(
            model_data, dict(zip(model_data["calibrated"].keys(), y))
        )

        model_data["config"]["logger"].info(
            "Numerically approximating model's solution:"
        )
        y = model.solve_foc(model_data, np.asarray(model_data["optimizer"]["x0"]))
        ae = [
            np.abs(v[0]() - v[1](model_data, y[0], y[1], y[2]))
            for _, v in model_data["calibrator"]["targets"].items()
        ]
        sae = sum(ae)
        if sae < min_sae:
            min_sae = sae
            if model_data["config"]["adaptive_optimizer_initialization"]:
                model_data["optimizer"]["x0"] = y.tolist()
        model_data["config"]["logger"].info(f"Calibration Errors = {ae}")
        model_data["config"]["logger"].info(
            f"Calibration Sum of Absolute Errors = {sae}"
        )

        return ae

    return errors


def save_calibration_if_not_exists(filename, calibration_results):
    """Save calibrated model."""
    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        fh = open(filename, "wb")
        pickle.dump(calibration_results, fh)
        fh.close()
        return True
    return False


def load_calibration(filename):
    """Load a saved calibrated model."""
    fh = open(filename, "rb")
    calibration_results = pickle.load(fh)
    fh.close()
    return calibration_results


def calibrate_and_save_or_load(calibration_mode, income_group, config_init):
    """Calibrate the model and save the results."""
    filename = config.make_output_data_filename(config_init, income_group)
    if not os.path.exists(filename):
        message = f"Calibrating {calibration_mode} with {income_group.capitalize()} Income Data"
    else:
        message = (
            f"Loading {calibration_mode} with {income_group.capitalize()} Income Data"
        )
    config_init["logger"].info(message)

    verbose = config_init["verbose"]
    config_init["verbose"] = False
    model_data = model.make_model_data(income_group, config_init)
    config_init["verbose"] = verbose

    if not os.path.exists(filename):
        if model_data["config"]["verbose"]:
            model_data["config"]["logger"].info(model.json_model_data(model_data))
        errors = make_calibration_objective(model_data)
        bounds = model.get_calibration_bounds(model_data)
        model_data["calibrator"]["results"] = scipy.optimize.minimize(
            lambda x: sum(errors(x)),
            [value[0] for value in model_data["calibrated"].values()],
            bounds=bounds if model_data["calibrator"]["method"] == "L-BFGS-B" else None,
            method=model_data["calibrator"]["method"],
            options={"disp": True, "maxiter": model_data["calibrator"]["maxiter"]},
        )
        save_calibration_if_not_exists(filename, model_data["calibrator"]["results"])
    else:
        model_data["calibrator"]["results"] = load_calibration(filename)
        model.set_calibrated_data(
            model_data,
            {
                key: model_data["calibrator"]["results"]["x"][i]
                for i, key in enumerate(model_data["calibrated"].keys())
            },
        )
    model_data["optimizer"]["xstar"] = model.solve_foc(
        model_data, np.asarray(model_data["optimizer"]["x0"])
    ).tolist()

    return model_data


def calibrate_all_income_groups(mode, config_inputs):
    """Calibrate the model for a given mode."""
    config_init = config.prepare_mode_config(config_inputs, mode)

    solution = {}
    for income_group, initializer in config_init["initializers"].items():
        if "no-income" in mode and "hat_c" in initializer:
            del initializer["hat_c"]
        solution[income_group] = calibrate_and_save_or_load(
            mode, income_group, config_init
        )

    return solution


if __name__ == "__main__":
    config_inputs, modes = config.make_config_from_input()
    calibration_modes = calibration_mode.mapping()
    calibration_modes = {k: v for k, v in calibration_modes.items() if k in modes}

    solutions = {}
    for mode, preparation_callback in calibration_modes.items():
        solutions[mode] = calibrate_all_income_groups(mode, config_inputs)
