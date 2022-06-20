"""
Solver file for Structural Change, Gender Gaps and Educational Choice.

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production, three sectors, genders, and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import numpy as np
import pandas as pd
import math as m
import json
import pickle
import re
from scipy.optimize import minimize
from os.path import exists


def make_model_data(income_group, calibration_init=None):
    """Prepare model data for an income group.

    Expected to be used for constructing data for extended model estimations, i.e.
    estimations that include some preference parameters.
    """
    input_data = pd.read_csv("AMS_HCinputs_GMM.csv")
    wage_data = [0.82, 0.84, 0.81]
    consumption_data = [0.23, 0.06, 0.02]

    wage_target_weight = 100
    consumption_target_weight = 100

    def make_labor_target(gender, index):
        data = input_data.iloc[income_group]["L_{}{}".format(gender, index)]
        if gender == "f":

            def prediction(d, x, sf, sm):
                return make_female_time_allocation_control(d, index)(x, sf, sm)

        else:

            def prediction(d, x, sf, sm):
                return make_male_time_allocation_control(d, index)(x, sf, sm)

        return [data, prediction]

    def make_within_gender_labor_ratio_target(gender, over, under):
        data = (
            input_data.iloc[income_group]["L_{}{}".format(gender, over)]
            / input_data.iloc[income_group]["L_{}{}".format(gender, under)]
        )
        if gender == "f":

            def prediction(d, x, sf, sm):
                return make_female_time_allocation_control(d, over)(
                    x, sf, sm
                ) / make_female_time_allocation_control(d, under)(x, sf, sm)

        else:

            def prediction(d, x, sf, sm):
                return make_male_time_allocation_control(d, over)(
                    x, sf, sm
                ) / make_male_time_allocation_control(d, under)(x, sf, sm)

        return [data, prediction]

    def make_across_gender_labor_ratio_target(index):
        data = (
            input_data.iloc[income_group]["L_f{}".format(index)]
            / input_data.iloc[income_group]["L_m{}".format(index)]
        )

        def prediction(d, x, sf, sm):
            return make_female_time_allocation_control(d, index)(
                x, sf, sm
            ) / make_male_time_allocation_control(d, index)(x, sf, sm)

        return [data, prediction]

    targets = {
        # relative female labor allocation
        "Lf_amah": make_within_gender_labor_ratio_target("f", "am", "ah"),
        "Lf_mmmh": make_within_gender_labor_ratio_target("f", "mm", "mh"),
        "Lf_smsh": make_within_gender_labor_ratio_target("f", "sm", "sh"),
        "Lf_amsm": make_within_gender_labor_ratio_target("f", "am", "sm"),
        "Lf_mmsm": make_within_gender_labor_ratio_target("f", "mm", "sm"),
        # relative gender labor allocation
        "Lfm_ah": make_across_gender_labor_ratio_target("ah"),
        "Lfm_am": make_across_gender_labor_ratio_target("am"),
        "Lfm_mh": make_across_gender_labor_ratio_target("mh"),
        "Lfm_sm": make_across_gender_labor_ratio_target("sm"),
        # relative male labor allocation
        "Lm_smmm": make_within_gender_labor_ratio_target("m", "sm", "mm"),
        # leisure allocation
        "dL_fl": make_labor_target("f", "l"),
        "dL_ml": make_labor_target("m", "l"),
        # schooling years
        "sf": [input_data.loc[income_group].sf, lambda d, x, sf, sm: sf],
        "sm": [input_data.loc[income_group].sm, lambda d, x, sf, sm: sm],
        # wage ratio
        "x": [
            wage_data[income_group] * wage_target_weight,
            lambda d, x, sf, sm: x * wage_target_weight,
        ],
        # subsistence share
        "gamma": [
            consumption_data[income_group] * consumption_target_weight,
            lambda d, x, sf, sm: make_subsistence_consumption_share(d)(x, sf, sm)
            * consumption_target_weight,
        ],
        # internal solutions
        "F": [
            0,
            lambda d, x, sf, sm: np.linalg.norm(make_foc(d)(np.asarray([x, sf, sm]))),
        ],
    }

    data = {
        "income_group": income_group,
        "preferences": {
            "eta": 2.27,  # time input substitutability
            "eta_l": 2.27,  # leisure substitutability
            "epsilon": 0.002,  # a-m-s substitutability
            "sigma": 2.0,  # h-m substitutability
            "nu": 0.58,  # log human capital curvature
            "zeta": 0.32,  # log human capital scale
            "rho": 0.04,  # subjective discount factor
        },
        "calibrated": {
            "extended": {
                "estimation_income_group": income_group,
                "beta_f": [None, (1e-3, None)],  # female's schooling cost
                "beta_m": [None, (1e-3, None)],  # male's schooling cost
                "xi_l": [None, (0.01, 0.99)],  # female's share in leisure
                "varphi": [None, (1e-3, None)],  # leisure preference scale
                "hat_c": [None, (0, None)],  # adjusted subsistence term
            },
            "xi_ah": [None, (0.01, 0.99)],  # female's share in household agriculture
            "xi_mh": [None, (0.01, 0.99)],  # female's share in household manufacturing
            "xi_sh": [None, (0.01, 0.99)],  # female's share in household services
            "xi_am": [None, (0.01, 0.99)],  # female's share in modern agriculture
            "xi_mm": [None, (0.01, 0.99)],  # female's share in modern manufacturing
            "xi_sm": [None, (0.01, 0.99)],  # female's share in modern services
            # relative productivities
            "Z_amah": [None, (1e-3, None)],
            "Z_mmmh": [None, (1e-3, None)],
            "Z_smsh": [None, (1e-3, None)],
            "Z_amsm": [None, (1e-3, None)],
            "Z_mmsm": [None, (1e-3, None)],
        },
        "fixed": {
            "Lf": 1.0,  # female's time endowment
            "Lm": 1.0,  # male's time endowment
            "T": input_data.loc[income_group, "T"],  # life expectancy
            "Z_sm": 1.0,  # modern services productivity
        },
        "calibrator": {"step": None, "lambda": 1, "tol": 1e-4, "targets": targets},
        "optimizer": {
            "x0": [
                wage_data[income_group],
                input_data.loc[income_group].sf,
                input_data.loc[income_group].sm,
            ],
            "step": 1e-10,
            "maxn": 15,
            "min_step": 1e-12,
            "lambda": 1e-0,
            "Ftol": 1e-4,
            "htol": 1e-3,
        },
    }

    if calibration_init:
        # this also checks if all parameters are initialized
        for k in data["calibrated"]["extended"].keys():
            if k != "estimation_income_group":
                data["calibrated"]["extended"][k][0] = calibration_init[k]
        for k in data["calibrated"].keys():
            if k != "extended":
                data["calibrated"][k][0] = calibration_init[k]

    return data


def set_calibrated_data(data, calibration_data):
    """Set new calibration parameters.

    User to set calibration parameters from either a list or a dictionary. Expected to be
    used while minimizing the distance from targeted statistics.

    If `calibration_data` is of type `list` or `ndarray`, then the function assumes that the
    parameter order is the same to the order of the keys in `data["calibrated"]`. The key
    `"extended"` is excluded. If the number of items in `calibration_data` is equal to
    `len(data["calibrated"]) - 1` (for the `"extended"` key), then only
    these parameters are set. If the number of items in `calibration_data` is equal to
    `len(data["calibrated"]) + len(data["calibrated"]["extended"]) - 2`, then
    also the extended parameters are set. The extended parameter should be placed at the tail
    of `calibration_data` in the order they appear in data["calibrated"]["extended"].
    For any other length of input list, the function throws an exception.

    If `calibration_data` is a dictionary, the order of parameters dos not matter. If the
    passed dictionary contains a key 'extended', the extended calibration parameters are also
    modified. Raises an exception if some calibrated parameter in model data is not found
    in calibration_data.

    Args:
        calibration_data (dict): New calibrated parameters to be used
    """
    if not isinstance(calibration_data, dict):
        params = [k for k in data["calibrated"].keys() if k != "extended"]
        if not len(params) == len(calibration_data):
            params = params + [
                k
                for k in data["calibrated"]["extended"].keys()
                if k != "estimation_income_group"
            ]
            if not len(params) == len(calibration_data):
                raise Exception("Unexpected number of input parameters")
        print(
            "Calibration Values = {}".format(
                {k: round(v, 4) for k, v in dict(zip(params, calibration_data)).items()}
            )
        )
        calibration_data = dict(zip(params, calibration_data))

    # this also checks if all parameters are set
    for k in data["calibrated"].keys():
        if k != "extended":
            data["calibrated"][k][0] = calibration_data[k]
    if set(calibration_data.keys()) & set(data["calibrated"]["extended"].keys()):
        for k in data["calibrated"]["extended"].keys():
            if k != "estimation_income_group":
                data["calibrated"]["extended"][k][0] = calibration_data[k]

    return data


def get_calibration_bounds(data, length):
    """Get calibration parameter bounds."""
    bounds = [v[1] for k, v in data["calibrated"].items() if k != "extended"]
    if not len(bounds) == length:
        bounds = bounds + [
            v[1]
            for k, v in data["calibrated"]["extended"].items()
            if k != "estimation_income_group"
        ]
        if not len(bounds) == length:
            raise Exception("Unexpected number of parameter bounds")

    return bounds


def update_model_data(data, income_group, calibration_init):
    """Update model data for an income group.

    Expected to be used for constructing data for model estimations not including
    preference parameters.

    Args:
        calibration_init (dict): Initial values for calibrated parameters for the updated model
    """
    data["income_group"] = income_group

    # this also checks if all parameters are initialized
    for k in data["calibrated"].keys():
        if k != "extended":
            data["calibrated"][k][0] = calibration_init[k]

    return data


def print_model_data(data):
    """Indented model data print."""

    class encoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    print(json.dumps(data, indent=2, cls=encoder))


def make_hc_fdf(model_data):
    """Prepare human capital function and derivative."""
    zeta = model_data["preferences"]["zeta"]
    nu = model_data["preferences"]["nu"]

    def H(s):
        return np.exp(zeta / (1 - nu) * np.power(s, 1 - nu))

    return {"h": H, "dh": lambda s: H(s) * zeta * np.power(s, -nu)}


def make_discounter_fdf(model_data):
    """Prepare working life discounter function and derivative."""
    rho = model_data["preferences"]["rho"]
    T = model_data["fixed"]["T"]

    def d(s):
        return 1 / (-rho) * np.exp((-rho) * T) - 1 / (-rho) * np.exp((-rho) * s)

    return {"d": d, "dd": lambda s: -np.exp(-rho * s)}


def make_working_life(model_data):
    """Prepare working life function."""
    T = model_data["fixed"]["T"]

    def delta(s):
        return T - s

    return delta


def make_female_lifetime_schooling_cost_fdf(model_data):
    """Prepare female lifetime cost of schooling function."""
    rho = model_data["preferences"]["rho"]
    beta_f = model_data["calibrated"]["extended"]["beta_f"][0]

    def dW(s):
        return -beta_f * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_f / rho, "dW": dW}


def make_male_lifetime_schooling_cost_fdf(model_data):
    """Prepare male lifetime cost of schooling function."""
    rho = model_data["preferences"]["rho"]
    beta_m = model_data["calibrated"]["extended"]["beta_m"][0]

    def dW(s):
        return -beta_m * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_m / rho, "dW": dW}


def make_female_wage_bill(model_data, index):
    """Prepare female wage bill functions.

    See appendix's equations (A.6), (B.18), and (B.29).
    """
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]

    if index == "l":
        eta = model_data["preferences"]["eta_l"]
        xi_i = model_data["calibrated"]["extended"]["xi_{}".format(index)][0]
    else:
        eta = model_data["preferences"]["eta"]
        xi_i = model_data["calibrated"]["xi_{}".format(index)][0]

    if index.endswith("m"):

        def adjustment(sf, sm):
            return 1

    else:

        def adjustment(sf, sm):
            return d(sf) * h(sf) / d(sm) / h(sm)

    A = m.pow(xi_i / (1 - xi_i), -eta)

    def If(x, sf, sm):
        return 1 / (1 + A * m.pow(x, eta - 1) * m.pow(adjustment(sf, sm), eta - 1))

    return If


def make_male_wage_bill(model_data, index):
    """Prepare female wage bill functions.

    See appendix's equations (A.7) and (B.19).
    """
    If_ip = make_female_wage_bill(model_data, index)

    return lambda x, sf, sm: 1 - If_ip(x, sf, sm)


def has_relative_productivity(model_data, over, under):
    """Check if a relative productivity parameter is calibrated."""
    keys = model_data["calibrated"].keys()
    return (
        1
        if "Z_{}{}".format(over, under) in keys
        else -1
        if "Z_{}{}".format(under, over) in keys
        else 0
    )


def productivity_conjugate_right_indices(model_data, left):
    """Find all calibrated relative productivities with left index."""
    return {
        k[4:]
        for k in model_data["calibrated"].keys()
        if k.startswith("Z_{}".format(left))
    }


def productivity_conjugate_left_indices(model_data, right):
    """Find all calibrated relative productivities with right index."""
    return {
        k[2:4]
        for k in model_data["calibrated"].keys()
        if k.startswith("Z_") and k.endswith(right)
    }


def productivity_conjugate_indices(model_data, index):
    """Find calibrated relative productivities with left or right index."""
    return productivity_conjugate_right_indices(
        model_data, index
    ) | productivity_conjugate_left_indices(model_data, index)


def make_relative_consumption_expenditure(model_data, over, under):
    """Prepare relative consumption (non leisure) expenditure function.

    Expects that both passed indices are of the form 'ip' where 'i' is a sector among agriculture
    ('a'), manufacturing ('m'), or services ('s'), and 'p' is a production type between modern
    ('m') and traditional ('t'). See appendix's equations (B.40),  (B.49), and (B.50).
    """
    # trivial case
    if over == under:
        return lambda x, sf, sm: 1

    # calculate indirectly if we don't have the relative productivity
    direct = has_relative_productivity(model_data, over, under)
    if direct <= 0:
        # check if inverting works
        if direct == -1:
            E_jqip = make_relative_consumption_expenditure(model_data, under, over)
            return lambda x, sf, sm: 1 / E_jqip(x, sf, sm)
        # check if interjecting once works
        over_conj = productivity_conjugate_indices(model_data, over)
        under_conj = productivity_conjugate_indices(model_data, under)
        interject = list(over_conj & under_conj)
        if interject:
            E_ipkr = make_relative_consumption_expenditure(
                model_data, over, interject[0]
            )
            E_krjq = make_relative_consumption_expenditure(
                model_data, interject[0], under
            )
            return lambda x, sf, sm: E_ipkr(x, sf, sm) * E_krjq(x, sf, sm)
        # interject twice
        interject = [
            [left, right]
            for left in over_conj
            for right in productivity_conjugate_indices(model_data, left)
            if right in under_conj
        ]
        if interject:
            interject1 = interject[0][0]
            interject2 = interject[0][1]
            E_ipkr = make_relative_consumption_expenditure(model_data, over, interject1)
            E_krny = make_relative_consumption_expenditure(
                model_data, interject1, interject2
            )
            E_nyjq = make_relative_consumption_expenditure(
                model_data, interject2, under
            )
            return (
                lambda x, sf, sm: E_ipkr(x, sf, sm)
                * E_krny(x, sf, sm)
                * E_nyjq(x, sf, sm)
            )
        # interject three times
        interject = [
            [left, middle, right]
            for left in over_conj
            for middle in productivity_conjugate_indices(model_data, left)
            for right in productivity_conjugate_indices(model_data, middle)
            if right in under_conj
        ]
        interject1 = interject[0][0]
        interject2 = interject[0][1]
        interject3 = interject[0][2]
        E_ipkr = make_relative_consumption_expenditure(model_data, over, interject1)
        E_krny = make_relative_consumption_expenditure(
            model_data, interject1, interject2
        )
        E_nyow = make_relative_consumption_expenditure(
            model_data, interject1, interject3
        )
        E_owjq = make_relative_consumption_expenditure(model_data, interject3, under)
        return lambda x, sf, sm: (
            E_ipkr(x, sf, sm)
            * E_krny(x, sf, sm)
            * E_nyow(x, sf, sm)
            * E_owjq(x, sf, sm)
        )

    # default case
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]
    eta = model_data["preferences"]["eta"]
    sigma = model_data["preferences"]["sigma"]
    xi_ip = model_data["calibrated"]["xi_{}".format(over)][0]
    xi_jq = model_data["calibrated"]["xi_{}".format(under)][0]
    Z_ipjq = model_data["calibrated"]["Z_{}{}".format(over, under)][0]
    I_ip = make_female_wage_bill(model_data, over)
    I_jq = make_female_wage_bill(model_data, under)

    if over[0] == under[0]:
        return lambda x, sf, sm: m.pow(
            Z_ipjq
            * m.pow(xi_ip / xi_jq, eta / (eta - 1))
            * m.pow(I_jq(x, sf, sm) / I_ip(x, sf, sm), 1 / (eta - 1))
            * d(sf)
            * h(sf)
            / d(0),
            sigma - 1,
        )
    else:
        epsilon = model_data["preferences"]["epsilon"]
        ir = over[0] + "h" if over[1] == "m" else "m"
        E_ipir = make_relative_consumption_expenditure(model_data, over, ir)
        jy = under[0] + "h" if under[1] == "m" else "m"
        E_jqjy = make_relative_consumption_expenditure(model_data, under, jy)
        I_ip = make_female_wage_bill(model_data, over)
        I_jq = make_female_wage_bill(model_data, under)

        return lambda x, sf, sm: (
            m.pow(Z_ipjq, epsilon - 1)
            * m.pow(
                m.pow(xi_ip / xi_jq, eta / (eta - 1))
                * m.pow(I_ip(x, sf, sm) / I_jq(x, sf, sm), 1 / (1 - eta)),
                epsilon - 1,
            )
            * m.pow(1 + 1 / E_jqjy(x, sf, sm), (sigma - epsilon) / (sigma - 1))
            * m.pow(1 + 1 / E_ipir(x, sf, sm), (epsilon - sigma) / (sigma - 1))
        )


def make_sectoral_expenditure_share_of_consumption(model_data, sector):
    """Prepare sectoral expenditure share unction.

    Returns a function that calculates the share of a sector's expenditure in total expenditure
    for commodities. Summing these functions over all sectors gives the constant unit function.
    See appendix's equation (B.57).
    """

    def E_j(x, sf, sm):
        sectors = ["a", "m", "s"]
        Eimihvs = [
            make_relative_consumption_expenditure(
                model_data, "{}m".format(s), "{}h".format(s)
            )(x, sf, sm)
            for s in sectors
        ]
        Ejmihvs = [
            make_relative_consumption_expenditure(
                model_data, "{}m".format(sector), "{}h".format(s)
            )(x, sf, sm)
            for s in sectors
        ]
        Ejmjhv = make_relative_consumption_expenditure(
            model_data, "{}m".format(sector), "{}h".format(sector)
        )(x, sf, sm)
        A = Ejmjhv / (1 + Ejmjhv)
        return 1 / sum([A * (1 + Eimihvs[i]) / Ejmihvs[i] for i in range(len(sectors))])

    return E_j


def make_female_labor_ratio(model_data, over, under):
    """Prepare female labor ratio function.

    Expects that both pass indices are as in make_relative_consumption_expenditure().
    See appendix's equation (C.13).
    """
    E_ipjq = make_relative_expenditure(model_data, over, under)
    I_ip = make_female_wage_bill(model_data, over)
    I_jq = make_female_wage_bill(model_data, under)
    d = make_discounter_fdf(model_data)["d"]
    delta = make_working_life(model_data)

    return lambda x, sf, sm: (
        E_ipjq(x, sf, sm)
        * I_ip(x, sf, sm)
        / I_jq(x, sf, sm)
        * m.pow(
            d(sf) / d(0) * delta(0) / delta(sf),
            over.endswith("m") - under.endswith("m"),
        )
    )


def make_male_labor_ratio(model_data, over, under):
    """Prepare male labor ratio function.

    Based on the female ratio calculation of make_female_labor_ratio(). See appendix's
    equation (C.17).
    """
    E_ipjq = make_relative_expenditure(model_data, over, under)
    I_ip = make_male_wage_bill(model_data, over)
    I_jq = make_male_wage_bill(model_data, under)
    d = make_discounter_fdf(model_data)["d"]
    delta = make_working_life(model_data)

    return lambda x, sf, sm: (
        E_ipjq(x, sf, sm)
        * I_ip(x, sf, sm)
        / I_jq(x, sf, sm)
        * m.pow(
            d(sf) / d(0) * delta(0) / delta(sf),
            over.endswith("m") - under.endswith("m"),
        )
    )


def make_aggregate_female_labor_ratio(model_data, index):
    """Prepare aggregate female labor ratio function.

    Sum of all non leisure female labor ratios for fixed right index.
    See appendix's equation (C.15).
    """

    def R(x, sf, sm):
        sectors = ["a", "m", "s"]
        types = ["m", "h"]
        Risjpsv = [
            make_female_labor_ratio(model_data, "{}{}".format(s, t), index)(x, sf, sm)
            for s in sectors
            for t in types
        ]
        return sum(Risjpsv)

    return R


def make_implicit_female_household_technology_coefficient(model_data, sector):
    """Prepare implicit female household technology coefficient function.

    See appendix's equation (E.1).
    """

    def Pih(x, sf, sm):
        ih = "{}h".format(sector)
        im = "{}m".format(sector)

        sigma = model_data["preferences"]["sigma"]
        epsilon = model_data["preferences"]["epsilon"]
        eta = model_data["preferences"]["eta"]
        Zim = model_data["fixed"]["Z_{}".format(im)]
        xiim = model_data["calibrated"]["xi_{}".format(im)][0]
        delta = make_working_life(model_data)

        Eihim = make_relative_consumption_expenditure(model_data, im, ih)
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        Iim = make_female_wage_bill(model_data, im)
        h = make_hc_fdf(model_data)["h"]
        Rimih = make_female_labor_ratio(model_data, im, ih)

        return (
            m.pow(1 + Eihim(x, sf, sm), sigma / (sigma - 1))
            * m.pow(Ei(x, sf, sm), epsilon / (1 - epsilon))
            * Zim
            * m.pow(xiim / Iim(x, sf, sm), eta / (eta - 1))
            * h(sf)
            * delta(sf)
            * Rimih(x, sf, sm)
        )

    return Pih


def make_base_female_household_labor(model_data):
    """Prepare the base female household labor control function.

    The labor control calculation depends on the corresponding sector's household productivity
    level. The sector is picked from the model_data["fixed"] parameters. All remaining labor
    control functions are calculated based on this control. See appendix's equation (E.5).
    """
    sector = [p[2:3] for p in model_data["fixed"] if re.search("Z_[ams]m", p)][0]

    def Lfih(x, sf, sm):
        ih = "{}h".format(sector)
        im = "{}m".format(sector)

        varphi = model_data["calibrated"]["extended"]["varphi"][0]
        hat_c = model_data["calibrated"]["extended"]["hat_c"][0]
        Lf = model_data["fixed"]["Lf"]

        Eimih = make_relative_consumption_expenditure(model_data, im, ih)
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        Il = make_female_wage_bill(model_data, "l")
        Iih = make_female_wage_bill(model_data, ih)

        Rih = make_aggregate_female_labor_ratio(model_data, ih)

        alpha = (
            varphi * Eimih(x, sf, sm) / Ei(x, sf, sm) * Il(x, sf, sm) / Iih(x, sf, sm)
        )

        Pih = make_implicit_female_household_technology_coefficient(model_data, sector)
        return (Lf + (alpha * hat_c) / Pih(x, sf, sm)) / (Rih(x, sf, sm) + alpha)

    return Lfih


def make_subsistence_consumption_share(model_data):
    """Prepare subsistence consumption share function.

    The consumption share is sector independent. The numerical calculation is based on
    make_female_household_labor_control(). See appendix's equation (E.6).
    """
    sector = [p[2:3] for p in model_data["fixed"] if re.search("Z_[ams]m", p)][0]

    def subsh(x, sf, sm):
        hat_c = model_data["calibrated"]["extended"]["hat_c"][0]
        Pih = make_implicit_female_household_technology_coefficient(model_data, sector)
        Lfih = make_base_female_household_labor(model_data)
        return hat_c / Pih(x, sf, sm) / Lfih(x, sf, sm)

    return subsh


def make_non_subsistence_consumption_share(model_data):
    """Prepare non subsistence consumption share function.

    See make_subsistence_consumption_share().
    """

    def nsubsh(x, sf, sm):
        subssh = make_subsistence_consumption_share(model_data)
        return 1 - subssh(x, sf, sm)

    return nsubsh


def make_relative_expenditure(model_data, over, under):
    """Prepare expenditure function.

    This ties up a loose end in the functionality of make_relative_consumption_expenditure().
    It can handle cases where any of the two indices is leisure ('l'). Leisure requires special
    treatment because its relative expenditure equations contains the non subsistence consumption
    share. See appendix's equation (B.59).
    """
    # trivial case
    if over == under:
        return lambda x, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda x, sf, sm: 1 / make_relative_expenditure(model_data, under, over)(
            x, sf, sm
        )
    if over == "l" and under.endswith("m"):
        varphi = model_data["calibrated"]["extended"]["varphi"][0]
        sector = under[0]
        other = under[0] + "h"

        def E_lj(x, sf, sm):
            nsubsh = make_non_subsistence_consumption_share(model_data)
            Ej = make_sectoral_expenditure_share_of_consumption(model_data, sector)
            Eihim = make_relative_consumption_expenditure(model_data, other, under)

            return varphi * nsubsh(x, sf, sm) / Ej(x, sf, sm) * (1 + Eihim(x, sf, sm))

        return E_lj
    if over == "l" and under.endswith("h"):
        E_lsm = make_relative_expenditure(model_data, "l", under[0] + "m")
        E_smsh = make_relative_expenditure(model_data, under[0] + "m", under)
        return lambda x, sf, sm: E_lsm(x, sf, sm) * E_smsh(x, sf, sm)

    # non leisure case
    return make_relative_consumption_expenditure(model_data, over, under)


def make_female_flow_time_allocation_ratio(model_data, over, under):
    """Prepare female flow time allocation ratio function.

    Covers the cases not handled by make_female_labor_ratio(). It can handle
    cases where one of the indices is leisure ('l'). See appendix's equation (C.14).
    """
    # trivial case
    if over == under:
        return lambda x, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda x, sf, sm: (
            1
            / make_female_flow_time_allocation_ratio(model_data, under, over)(x, sf, sm)
        )
    if over == "l":
        Elip = make_relative_expenditure(model_data, over, under)
        Il = make_female_wage_bill(model_data, over)
        Iip = make_female_wage_bill(model_data, under)
        d = make_discounter_fdf(model_data)["d"]
        delta = make_working_life(model_data)
        return lambda x, sf, sm: (
            Elip(x, sf, sm)
            * Il(x, sf, sm)
            / Iip(x, sf, sm)
            * m.pow(d(sf) / d(0) * delta(0) / delta(sf), -under.endswith("m"))
        )

    # non leisure case
    return make_female_labor_ratio(model_data, over, under)


def make_male_flow_time_allocation_ratio(model_data, over, under):
    """Prepare male flow time allocation ratio function.

    Covers the cases not handled by make_male_labor_ratio(). It can handle
    cases where one of the indices is leisure ('l'). See appendix's equation (C.18).
    """
    # trivial case
    if over == under:
        return lambda x, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda x, sf, sm: (
            1 / make_male_flow_time_allocation_ratio(model_data, under, over)(x, sf, sm)
        )
    if over == "l":
        Elip = make_relative_expenditure(model_data, over, under)
        Il = make_male_wage_bill(model_data, over)
        Iip = make_male_wage_bill(model_data, under)
        d = make_discounter_fdf(model_data)["d"]
        delta = make_working_life(model_data)
        return lambda x, sf, sm: (
            Elip(x, sf, sm)
            * Il(x, sf, sm)
            / Iip(x, sf, sm)
            * m.pow(d(sf) / d(0) * delta(0) / delta(sf), -under.endswith("m"))
        )

    # non leisure case
    return make_male_labor_ratio(model_data, over, under)


def make_aggregate_male_labor_ratio(model_data, index):
    """Prepare aggregate male labor ratio function.

    Sum of all non leisure male labor ratios for fixed right index.
    See appendix's equation (C.18).
    """

    def R(x, sf, sm):
        sectors = ["a", "m", "s"]
        types = ["m", "h"]
        Risjpsv = [
            make_male_flow_time_allocation_ratio(
                model_data, "{}{}".format(s, t), index
            )(x, sf, sm)
            for s in sectors
            for t in types
        ]
        return sum(Risjpsv)

    return R


def make_aggregate_female_flow_time_allocation_ratio(model_data, index):
    """Prepare aggregate female flow time allocation ratio function.

    Sum of all female time allocation ratios. In contrast to
    make_aggregate_female_labor_ratio(), the sum includes leisure. The sum over all
    production types and sectors should be equal to one. See
    appendix's equation (C.16).
    """

    def R(x, sf, sm):
        R_it = make_aggregate_female_labor_ratio(model_data, index)
        R_lit = make_female_flow_time_allocation_ratio(model_data, "l", index)
        return R_it(x, sf, sm) + R_lit(x, sf, sm)

    return R


def make_aggregate_male_flow_time_allocation_ratio(model_data, index):
    """Prepare aggregate male flow time allocation ratio function.

    Sum of all male time allocation ratios. In contrast to
    make_aggregate_male_labor_ratio(), the sum includes leisure. The sum over all
    production types and sectors should be equal one.
    """

    def R(x, sf, sm):
        R_it = make_aggregate_male_labor_ratio(model_data, index)
        R_lit = make_male_flow_time_allocation_ratio(model_data, "l", index)
        return R_it(x, sf, sm) + R_lit(x, sf, sm)

    return R


def make_female_time_allocation_control(model_data, index):
    """Prepare a female time allocation control function.

    The female time allocation controls' calculations depend on make_base_female_household_labor().
    The base control is directly calculated. The remaining calculations used the base control. See
    appendix's equation (C.16). The calculation can also be performed based on individual terms of
    (C.12). Using (C.16) is slower, but is numerically more stable (the difference of the aggregate
    female time allocation from the female time endowment is smaller).
    """
    Lf = model_data["fixed"]["Lf"]
    Rfip = make_aggregate_female_flow_time_allocation_ratio(model_data, index)
    return lambda x, sf, sm: Lf / Rfip(x, sf, sm)


def make_female_modern_production_allocation(model_data):
    """Prepare female modern production allocation function.

    The sum of female modern production labor controls.
    """

    def Mf(x, sf, sm):
        sectors = ["a", "m", "s"]
        return sum(
            [
                make_female_time_allocation_control(model_data, "{}m".format(s))(
                    x, sf, sm
                )
                for s in sectors
            ]
        )

    return Mf


def make_female_total_time_allocation(model_data):
    """Prepare female total time allocation function.

    The sum of female time allocation controls.
    """

    def Lf(x, sf, sm):
        sectors = ["a", "m", "s"]
        types = ["h", "m"]
        return sum(
            [
                make_female_time_allocation_control(model_data, "{}{}".format(s, t))(
                    x, sf, sm
                )
                for s in sectors
                for t in types
            ]
        ) + make_female_time_allocation_control(model_data, "l")(x, sf, sm)

    return Lf


def make_male_time_allocation_control(model_data, index):
    """Prepare a male time allocation control function.

    The male time allocation controls' calculations are based on the corresponding female controls.
    See appendix's equations (A.4), (B.16) and (B.27).
    """
    Lm = model_data["fixed"]["Lm"]
    Rmip = make_aggregate_male_flow_time_allocation_ratio(model_data, index)
    return lambda x, sf, sm: Lm / Rmip(x, sf, sm)


def make_male_modern_production_allocation(model_data):
    """Prepare male modern production allocation function.

    The sum of male modern production labor controls.
    """

    def Mm(x, sf, sm):
        sectors = ["a", "m", "s"]
        return sum(
            [
                make_male_time_allocation_control(model_data, "{}m".format(s))(
                    x, sf, sm
                )
                for s in sectors
            ]
        )

    return Mm


def make_male_total_time_allocation(model_data):
    """Prepare male total time allocation function.

    The sum of male time allocation controls.
    """

    def Lm(x, sf, sm):
        sectors = ["a", "m", "s"]
        types = ["h", "m"]
        return sum(
            [
                make_male_time_allocation_control(model_data, "{}{}".format(s, t))(
                    x, sf, sm
                )
                for s in sectors
                for t in types
            ]
        ) + make_male_time_allocation_control(model_data, "l")(x, sf, sm)

    return Lm


def make_female_total_wage_bill(model_data):
    """Prepare female total time allocation wage bill functions.

    See appendix's equation (C.21).
    """
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]

    def If_L(x, sf, sm):
        Lfv = make_female_total_time_allocation(model_data)(x, sf, sm)
        Lmv = make_male_total_time_allocation(model_data)(x, sf, sm)

        return 1 / (1 + Lmv / Lfv * d(sm) / d(sf) * h(sm) / h(sf) / x)

    return If_L


def make_reduced_constraints(model_data, index):
    """Prepare reduced constraints function.

    See appendix's equation (C.24).
    """

    def constraints(x, sf, sm):
        Rfip = make_aggregate_female_flow_time_allocation_ratio(model_data, index)
        sectors = ["a", "m", "s"]
        types = ["m", "h"]
        SumEjqipv = sum(
            [
                make_relative_expenditure(model_data, "{}{}".format(s, t), index)(
                    x, sf, sm
                )
                for s in sectors
                for t in types
            ]
        )
        Iipv = make_female_wage_bill(model_data, index)(x, sf, sm)
        ILv = make_female_total_wage_bill(model_data)(x, sf, sm)

        return Rfip(x, sf, sm) - SumEjqipv * Iipv / ILv

    return constraints


def make_female_schooling_condition(model_data, index):
    """Prepare female schooling condition function.

    See appendix's equation (D.4).
    """

    def schooling(x, sf, sm):
        hc_fdf = make_hc_fdf(model_data)
        d_fdf = make_discounter_fdf(model_data)
        delta = make_working_life(model_data)
        g = hc_fdf["dh"](sf) / hc_fdf["h"](sf) + d_fdf["dd"](sf) / d_fdf["d"](sf)
        nsubc = make_non_subsistence_consumption_share(model_data)
        Lfip = make_female_time_allocation_control(model_data, index)
        sector = index[0]
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        other = sector + ("m" if sector == "h" else "h")
        Eiqip = make_relative_consumption_expenditure(model_data, other, index)
        Iip = make_female_wage_bill(model_data, index)
        Mf = make_female_modern_production_allocation(model_data)
        dWf = make_female_lifetime_schooling_cost_fdf(model_data)["dW"]

        return dWf(sf) + (
            Mf(x, sf, sm)
            / Lfip(x, sf, sm)
            * g
            / nsubc(x, sf, sm)
            * Ei(x, sf, sm)
            / (1 + Eiqip(x, sf, sm))
            * Iip(x, sf, sm)
            * delta(0)
        )

    return schooling


def make_male_schooling_condition(model_data, index):
    """Prepare male schooling condition function.

    See appendix's equation (D.4).
    """

    def schooling(x, sf, sm):
        hc_fdf = make_hc_fdf(model_data)
        d_fdf = make_discounter_fdf(model_data)
        delta = make_working_life(model_data)
        g = hc_fdf["dh"](sm) / hc_fdf["h"](sm) + d_fdf["dd"](sm) / d_fdf["d"](sm)
        nsubc = make_non_subsistence_consumption_share(model_data)
        Lmip = make_male_time_allocation_control(model_data, index)
        sector = index[0]
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        other = sector + ("m" if sector == "h" else "h")
        Eiqip = make_relative_consumption_expenditure(model_data, other, index)
        Im_ip = make_male_wage_bill(model_data, index)
        Mm = make_male_modern_production_allocation(model_data)
        dWm = make_male_lifetime_schooling_cost_fdf(model_data)["dW"]

        return dWm(sm) + (
            Mm(x, sf, sm)
            / Lmip(x, sf, sm)
            * g
            / nsubc(x, sf, sm)
            * Ei(x, sf, sm)
            / (1 + Eiqip(x, sf, sm))
            * Im_ip(x, sf, sm)
            * delta(0)
        )

    return schooling


def make_schooling_condition_ratio(model_data, index):
    """Prepare female to male schooling condition function.

    See appendix's equation (D.7).
    """

    def schooling(x, sf, sm):
        hc_fdf = make_hc_fdf(model_data)
        d_fdf = make_discounter_fdf(model_data)
        dWf = make_female_lifetime_schooling_cost_fdf(model_data)["dW"]
        dWm = make_male_lifetime_schooling_cost_fdf(model_data)["dW"]

        def g(s):
            return (
                (hc_fdf["dh"](s) / hc_fdf["h"](s) + d_fdf["dd"](s) / d_fdf["d"](s))
                * d_fdf["d"](s)
                * hc_fdf["h"](s)
            )

        Mf = make_female_modern_production_allocation(model_data)
        Mm = make_male_modern_production_allocation(model_data)

        return dWf(sf) / dWm(sm) - (Mf(x, sf, sm) / Mm(x, sf, sm) * x * g(sf) / g(sm))

    return schooling


def make_foc(model_data):
    """Prepare the model's first order condition vector function."""
    f1 = make_reduced_constraints(model_data, "sh")
    f21 = make_female_schooling_condition(model_data, "sh")
    f22 = make_male_schooling_condition(model_data, "sh")

    def f2(x, sf, sm):
        return f21(x, sf, sm) + f22(x, sf, sm)

    f3 = make_schooling_condition_ratio(model_data, "sh")

    def F(y):
        Lf = make_female_total_time_allocation(model_data)(y[0], y[1], y[2])
        Lm = make_male_total_time_allocation(model_data)(y[0], y[1], y[2])
        if np.abs(Lf - 1) > 1e-2:
            print("Warning: Lf = {}".format(Lf))
        if np.abs(Lm - 1) > 1e-2:
            print("Warning: Lm = {}".format(Lm))

        return np.asarray(
            [f1(y[0], y[1], y[2]), f2(y[0], y[1], y[2]), f3(y[0], y[1], y[2])]
        )

    return F


def make_jacobian(model_data):
    """Calculate the model's Jacobian function."""

    def jacobian(y):
        F = make_foc(model_data)
        n = len(y)

        step = model_data["optimizer"]["step"]
        min_step = model_data["optimizer"]["min_step"]
        half_step = step / 2

        while step > min_step:
            J = np.zeros((n, n)) * np.nan

            for i in range(0, n):
                yl = y.copy()
                yl[i] = yl[i] - half_step
                yr = y.copy()
                yr[i] = yr[i] + half_step

                try:
                    Fl = np.array(F(yl))
                    Fr = np.array(F(yr))
                    J[:, i] = np.array((Fr - Fl) / step).T
                except ZeroDivisionError as e:
                    # print(
                    #     "Jacobian calculation failed for step '{}' with error: {}".format(
                    #         step, e
                    #     )
                    # )
                    pass

            if not m.isnan(np.sum(J)):
                break
            step = step / 10
            half_step = step / 2

        if step <= min_step:
            raise ValueError("Jacobian calculation failed")

        return J

    return jacobian


def solve_foc(model_data, y):
    """Solve the optimization problem."""

    def print_optimization_diagnostics(model_data, optimizer_data):
        print_model_data(model_data)
        print(json.dumps(optimizer_data, indent=2))

    F = make_foc(model_data)
    J = make_jacobian(model_data)

    Ftol = model_data["optimizer"]["Ftol"]
    htol = model_data["optimizer"]["htol"]
    lam = model_data["optimizer"]["lambda"]
    maxn = model_data["optimizer"]["maxn"]
    n = 0
    converged = False
    yn = y.copy()
    while n <= maxn and not converged:
        y = yn.copy()
        Fv = F(y)
        Jv = J(y)
        iJv = np.linalg.inv(Jv)

        h = -iJv @ Fv.T
        Flen = np.linalg.norm(Fv)
        hlen = m.inf

        stepped = False
        alam = lam * 10
        while not stepped and alam > 1e-6:
            alam = alam / 10
            yn = y + alam * np.array(h).T
            try:
                Fvn = F(yn)
                Jvn = J(yn)
                np.linalg.inv(Jvn)
                if np.linalg.norm(Fvn) < Flen:
                    stepped = not np.isnan(Jvn).any()
            except (ValueError, np.linalg.LinAlgError) as e:
                # print(
                #     "Optimizer step caught: '{}' for y = {} and lambda = {} at n = {}".format(
                #         e, y, alam, n
                #     )
                # )
                pass
        if not stepped:
            print("Household optimization solver failed to step at n = {}".format(n))
            break

        n = n + 1
        hlen = np.linalg.norm(yn - y)
        converged = Flen <= Ftol or hlen <= htol
        print(
            "n = {: >2} |F| = {:4.4f} |h| = {:4.4f} y = [{:4.2f} {:4.2f} {:4.2f}]".format(
                n, Flen, hlen, y[0], y[1], y[2]
            )
        )
    if not converged:
        print("Warning: Household optimization solver did not converge")
        # raise Exception("Optimization solver did not converge")
    # print_optimization_diagnostics(
    #     model_data,
    #     {
    #         "n": n,
    #         "y": y.tolist(),
    #         "yn": yn.tolist(),
    #         "F": Fv.tolist(),
    #         "Fn": Fvn.tolist(),
    #         "Jv": Jv.tolist(),
    #         "Jvn": Jvn.tolist(),
    #         "Flen": Flen,
    #         "Fcond": 1 if Flen <= Ftol else 0,
    #         "hlen": hlen,
    #         "hcond": 1 if hlen <= htol else 0,
    #     },
    # )
    print("Returning x, sf, sm = {} with foc = {}".format(y, Fv))

    return y


def make_calibration(model_data):
    """Prepare calibration function."""
    min_sae = 100

    def errors(y):
        nonlocal model_data, min_sae
        model_data = set_calibrated_data(model_data, y)

        print("Numerically approximating model's solution:")
        y = solve_foc(model_data, np.asarray(model_data["optimizer"]["x0"]))
        sae = sum(
            [
                np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
                for k, v in model_data["calibrator"]["targets"].items()
            ]
        )
        if sae < min_sae:
            min_sae = sae
            model_data["optimizer"]["x0"] = y.tolist()
        print(
            "Calibration Errors = {}".format(
                {
                    k: np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
                    for k, v in model_data["calibrator"]["targets"].items()
                }
            )
        )
        print(
            "Calibration Sum of Absolute Errors = {}".format(
                sum(
                    [
                        np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
                        for k, v in model_data["calibrator"]["targets"].items()
                    ]
                )
            )
        )

        return [
            np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
            for k, v in model_data["calibrator"]["targets"].items()
        ]

    return errors


def calibrate_and_save(income_group, initializers, mode=0):
    """Calibrate the Model and Save the Results."""
    income_group_string = {0: "low", 1: "middle", 2: "high"}
    calibration_mode = {0: "normal", 1: "restrictive"}
    print(
        f"Calibrating Model with {income_group_string[income_group].capitalize()} Income Data ({calibration_mode[mode].capitalize()} Mode)"
    )

    income_data = make_model_data(income_group)
    income_data = set_calibrated_data(income_data, initializers)
    if mode == 1:
        del income_data["calibrator"]["targets"]["sf"]
        del income_data["calibrator"]["targets"]["sm"]
        #del income_data["calibrator"]["targets"]["x"]
        initializers = initializers[0:-5]
    print_model_data(income_data)

    errors = make_calibration(income_data)
    bounds = get_calibration_bounds(income_data, len(initializers))
    calibration_results = {}

    filename = f"out/{income_group_string[income_group]}_income_data_{calibration_mode[mode]}_calibration.pkl"
    if not exists(filename):
        calibration_results = minimize(
            lambda x: sum(errors(x)),
            initializers,
            bounds=bounds,
            method="Nelder-Mead",
            options={"gtol": 1e-2, "disp": True},
        )
        fh = open(filename, "wb")
        pickle.dump(calibration_results, fh)
        fh.close()
    else:
        fh = open(filename, "rb")
        calibration_results = pickle.load(fh)
        fh.close()
        print(calibration_results)

    return calibration_results


def get_calibrated_model_solution(income_group, calibrated_data):
    income_data = make_model_data(income_group)
    income_data = set_calibrated_data(income_data, calibrated_data)
    y = solve_foc(income_data, np.asarray(income_data["optimizer"]["x0"])).tolist()
    gamma = make_subsistence_consumption_share(income_data)(*y)

    return [*y, gamma]


calibration_results = {}

h0 = [
    0.4031965021635868,  # xi_ah
    0.3391205747601498,  # xi_mh
    0.5149952603968808,  # xi_sh
    0.09372496593258939,  # xi_am
    0.4334664033061566,  # xi_mm
    0.4411272026959281,  # xi_sm
    0.20435859208677465,  # Z_amah
    3.5842152755679955,  # Z_mmmh
    0.680446929964031,  # Z_smsh
    2.338081396068727,  # Z_amsm
    2.2904058464889685,  # Z_mmsm
    1.758860666117454,  # beta_f
    3.3286225174893413,  # beta_m
    0.49929863386113027,  # xi_l
    0.881360673192487,  # varphi
    33.5000491033924,  # hat_c
]
calibration_results[2] = calibrate_and_save(2, h0)

m0 = [
    0.46893249922666075,  # xi_ah
    0.352154690555463,  # xi_mh
    0.5574813571166507,  # xi_sh
    0.12668599697824975,  # xi_am
    0.44763834846445005,  # xi_mm
    0.4514297722300901,  # xi_sm
    0.3242305788619658,  # Z_amah
    0.8552615596296405,  # Z_mmmh
    0.7895966117223241,  # Z_smsh
    7.004466805040579,  # Z_amsm
    2.633316263824618,  # Z_mmsm
    1.911154543357428,  # beta_f
    3.8055712105287256,  # beta_m
    0.5327175413699853,  # xi_l
    1.091554000493862,  # varphi
    78.20552409269834,  # hat_c
]
calibration_results[1] = calibrate_and_save(1, m0)

l0 = [
    0.4749767445900056,  # xi_ah
    0.36918552699815016,  # xi_mh
    0.5320555646642038,  # xi_sh
    0.1283943589097189,  # xi_am
    0.3571812266226453,  # xi_mm
    0.4474431715900655,  # xi_sm
    0.3619299629688616,  # Z_amah
    0.7139589995942215,  # Z_mmmh
    0.761866437767019,  # Z_smsh
    7.652850106696286,  # Z_amsm
    2.980507856666135,  # Z_mmsm
    2.039113628511629,  # beta_f
    4.638697399561042,  # beta_m
    0.53788018191344,  # xi_l
    1.1517474321526664,  # varphi
    158.1642194891241,  # hat_c
]
calibration_results[0] = calibrate_and_save(0, l0)

calibration_results[12] = calibrate_and_save(2, calibration_results[1]["x"], mode=1)
calibration_results[10] = calibrate_and_save(0, calibration_results[1]["x"], mode=1)

print(get_calibrated_model_solution(2, calibration_results[2]["x"]))
print(get_calibrated_model_solution(1, calibration_results[1]["x"]))
print(get_calibrated_model_solution(0, calibration_results[0]["x"]))
print(
    get_calibrated_model_solution(
        2,
        calibration_results[12]["x"].tolist()
        + calibration_results[1]["x"].tolist()[-5:],
    )
)
print(
    get_calibrated_model_solution(
        0,
        calibration_results[10]["x"].tolist()
        + calibration_results[1]["x"].tolist()[-5:],
    )
)


