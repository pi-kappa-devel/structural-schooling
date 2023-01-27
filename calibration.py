"""Calibration file."""

import copy
import numpy as np
import os
import pickle
import scipy
import scipy.optimize

import config
import calibration_traits
import model


def make_calibration_data(invariant_model):
    """Prepare calibration data.

    Model data are deeply copied to the resulting dictionary.
    Args:
        invariant_model (dict): Invariant model data.
    """
    model_data = copy.deepcopy(invariant_model)

    weights = {
        "sf": 1 / model_data["config"]["parameters"]["T"],
        "sm": 1 / model_data["config"]["parameters"]["T"],
        "tw": 1,
        "gamma": 1,
    }

    data = {
        "model": model_data,
        "calibrator": {
            "weights": weights,
            "targets": None,
            "method": "Nelder-Mead",
            "maxiter": 10 ** 4,
        },
    }

    targets = {
        # relative female time allocation
        "Lf_ArAh": calibration_traits.make_within_gender_time_allocation_ratio_target(
            data, "f", "Ar", "Ah"
        ),
        "Lf_MrMh": calibration_traits.make_within_gender_time_allocation_ratio_target(
            data, "f", "Mr", "Mh"
        ),
        "Lf_SrSh": calibration_traits.make_within_gender_time_allocation_ratio_target(
            data, "f", "Sr", "Sh"
        ),
        "Lf_ArSr": calibration_traits.make_within_gender_time_allocation_ratio_target(
            data, "f", "Ar", "Sr"
        ),
        "Lf_MrSr": calibration_traits.make_within_gender_time_allocation_ratio_target(
            data, "f", "Mr", "Sr"
        ),
        # leisure allocation
        "Lf_l": calibration_traits.make_time_allocation_target(data, "f", "l"),
        # schooling years
        "sf": calibration_traits.make_schooling_target(data, "f"),
        "sm": calibration_traits.make_schooling_target(data, "m"),
        # wage ratio
        "tw": calibration_traits.make_wage_ratio_target(data),
        # subsistence share
        "gamma": calibration_traits.make_subsistence_share_target(data),
    }

    data["calibrator"]["targets"] = targets

    return data


def make_calibration_objective(data):
    """Prepare calibration function."""
    min_sae = 100

    def errors(y):
        nonlocal data, min_sae
        data["model"] = model.set_free_parameters(
            data["model"], dict(zip(data["model"]["free"].keys(), y))
        )

        data["model"]["config"]["logger"].info(
            "Numerically approximating model's solution:"
        )
        y = model.solve_foc(data["model"], np.asarray(data["model"]["optimizer"]["x0"]))
        ae = {
            k: np.abs(v[0]() - v[1](data, y[0], y[1], y[2]))
            for k, v in data["calibrator"]["targets"].items()
        }
        sae = sum(ae.values())
        if sae < min_sae:
            min_sae = sae
            if data["model"]["config"]["adaptive_optimizer_initialization"]:
                data["model"]["optimizer"]["x0"] = y.tolist()
        data["model"]["config"]["logger"].info(f"Calibration Errors = {ae}")
        data["model"]["config"]["logger"].info(
            f"Calibration Sum of Absolute Errors = {sae}"
        )

        return list(ae.values())

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


def calibrate_and_save_or_load(config_init):
    """Calibrate the model and save the results."""
    group = config_init["group"]
    setup = config_init["setup"]
    filename = config.make_output_data_filename(config_init)
    if not os.path.exists(filename):
        message = f"Calibrating {setup} with {group.capitalize()} Income Data"
    else:
        message = f"Loading {setup} with {group.capitalize()} Income Data"
    config_init["logger"].info(message)

    verbose = config_init["verbose"]
    config_init["verbose"] = False
    model_data = model.make_model_data(config_init)
    calib_data = make_calibration_data(model_data)
    config_init["verbose"] = verbose

    if not os.path.exists(filename):
        if calib_data["model"]["config"]["verbose"]:
            calib_data["model"]["config"]["logger"].info(model.json_calib_data(calib_data))
        errors = make_calibration_objective(calib_data)
        bounds = model.get_calibration_bounds(calib_data["model"])
        calib_data["calibrator"]["results"] = scipy.optimize.minimize(
            lambda x: sum(errors(x)),
            [value[0] for value in calib_data["model"]["free"].values()],
            bounds=bounds if calib_data["calibrator"]["method"] == "L-BFGS-B" else None,
            method=calib_data["calibrator"]["method"],
            options={"disp": True, "maxiter": calib_data["calibrator"]["maxiter"]},
        )
        save_calibration_if_not_exists(filename, calib_data["calibrator"]["results"])
    else:
        calib_data["calibrator"]["results"] = load_calibration(filename)
        model.set_free_parameters(
            calib_data,
            {
                key: calib_data["calibrator"]["results"]["x"][i]
                for i, key in enumerate(calib_data["free"].keys())
            },
        )
    calib_data["model"]["optimizer"]["xstar"] = model.solve_foc(
        calib_data["model"], np.asarray(calib_data["model"]["optimizer"]["x0"])
    ).tolist()

    return calib_data


if __name__ == "__main__":
    config_inputs = config.make_config_from_input()
    calibrate_and_save_or_load(config_inputs)
