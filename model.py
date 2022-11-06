"""
Model file for "Why does the Schooling Gap Close when the Wage Gap Remains Constant?"

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
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


def make_discounter_fdf(model_data):
    """Prepare working life discounter function and derivative.

    See section (A.1)."""
    rho = model_data["fixed"]["rho"]
    T = model_data["fixed"]["T"]

    def d(s):
        return 1 / (-rho) * np.exp((-rho) * T) - 1 / (-rho) * np.exp((-rho) * s)

    return {"d": d, "dd": lambda s: -np.exp(-rho * s)}


def make_hc_fdf(model_data):
    """Prepare human capital function and derivative.

    See equation (C.6)."""
    zeta = model_data["fixed"]["zeta"]
    nu = model_data["fixed"]["nu"]

    def H(s):
        return np.exp(zeta / (1 - nu) * np.power(s, 1 - nu))

    return {"h": H, "dh": lambda s: H(s) * zeta * np.power(s, -nu)}


def make_model_data(income_group, calibration_init=None):
    """Prepare model data for an income group.

    Expected to be used for constructing data for model calibrations. 

    Args:
        income_group (str): Income group string, among "low", "middle", "high",
            and "all".
        calibration_init (dict): Used to override default initialization values
            for calibrated variables.
    """
    input_data = pd.read_csv("../data/calibration_input.csv")
    sectors = ["A", "M", "S"]
    technologies = ["h", "r"]
    income_groups = ["low", "middle", "high", "all"]
    income_group_index = income_groups.index(income_group)

    wage_target_weight = 1
    female_schooling_target_weight = 1 / input_data.loc[income_group_index, "T"]
    male_schooling_target_weight = 1 / input_data.loc[income_group_index, "T"]
    consumption_target_weight = 1

    def make_labor_target(gender, index):
        data = input_data.iloc[income_group_index]["L{}_{}".format(gender, index)]
        if gender == "f":

            def prediction(d, tw, sf, sm):
                return make_female_time_allocation_control(d, index)(tw, sf, sm)

        else:

            def prediction(d, tw, sf, sm):
                return make_male_time_allocation_control(d, index)(tw, sf, sm)

        return [data, prediction]

    def make_within_gender_labor_ratio_target(gender, over, under):
        data = (
            input_data.iloc[income_group_index]["L{}_{}".format(gender, over)]
            / input_data.iloc[income_group_index]["L{}_{}".format(gender, under)]
        )
        if gender == "f":

            def prediction(d, tw, sf, sm):
                return make_female_time_allocation_control(d, over)(
                    tw, sf, sm
                ) / make_female_time_allocation_control(d, under)(tw, sf, sm)

        else:

            def prediction(d, tw, sf, sm):
                return make_male_time_allocation_control(d, over)(
                    tw, sf, sm
                ) / make_male_time_allocation_control(d, under)(tw, sf, sm)

        return [data, prediction]

    targets = {
        # relative female labor allocation
        "Lf_ArAh": make_within_gender_labor_ratio_target("f", "Ar", "Ah"),
        "Lf_MrMh": make_within_gender_labor_ratio_target("f", "Mr", "Mh"),
        "Lf_SrSh": make_within_gender_labor_ratio_target("f", "Sr", "Sh"),
        "Lf_ArSr": make_within_gender_labor_ratio_target("f", "Ar", "Sr"),
        "Lf_MrSr": make_within_gender_labor_ratio_target("f", "Mr", "Sr"),
        # leisure allocation
        "Lf_l": make_labor_target("f", "l"),
        # schooling years
        "sf": [
            input_data.loc[income_group_index].sf * female_schooling_target_weight,
            lambda d, tw, sf, sm: sf * female_schooling_target_weight,
        ],
        "sm": [
            input_data.loc[income_group_index].sm * male_schooling_target_weight,
            lambda d, tw, sf, sm: sm * male_schooling_target_weight,
        ],
        # wage ratio
        "tw": [
            input_data.loc[income_group_index].tw * wage_target_weight,
            lambda d, tw, sf, sm: tw * wage_target_weight,
        ],
        # subsistence share
        "gamma": [
            input_data.loc[income_group_index].gamma * consumption_target_weight,
            lambda d, tw, sf, sm: make_subsistence_consumption_share(d)(tw, sf, sm)
            * consumption_target_weight,
        ],
        # internal solutions
        # "F": [
        #     0,
        #     lambda d, tw, sf, sm: np.linalg.norm(make_foc(d)(np.asarray([tw, sf, sm]))),
        # ],
    }

    data = {
        "income_group": income_group,
        "calibrated": {
            "hat_c": [None, (0, None)],  # adjusted subsistence term
            "varphi": [None, (1e-3, None)],  # leisure preference scale
            "beta_f": [None, (1e-3, None)],  # female's schooling cost
            # relative productivities
            "Z_ArAh": [None, (1e-3, None)],
            "Z_MrMh": [None, (1e-3, None)],
            "Z_SrSh": [None, (1e-3, None)],
            "Z_ArSr": [None, (1e-3, None)],
            "Z_MrSr": [None, (1e-3, None)],
        },
        "fixed": {
            # "hat_c": 0,  # adjusted subsistence term
            "eta": 2.27,  # labor input gender substitutability
            "eta_l": 2.27,  # leisure gender substitutability
            "epsilon": 0.002,  # output sectoral  substitutability
            "sigma": 2.0,  # output technological substitutability
            "nu": 0.58,  # log human capital curvature
            "zeta": 0.32,  # log human capital scale
            "rho": 0.04,  # subjective discount factor
            "Lf": 1.0,  # female's time endowment
            "Lm": 1.0,  # male's time endowment
            "T": input_data.loc[income_group_index, "T"],  # life expectancy
            "Z_Sr": 1.0,  # modern services productivity
            "tbeta": input_data.loc[
                income_group_index
            ].tbeta,  # relative schooling cost
        },
        "sectors": sectors,
        "technologies": technologies,
        "income_groups": income_groups,
        "calibrator": {"step": None, "lambda": 1, "tol": 1e-6, "targets": targets},
        "optimizer": {
            "x0": [
                input_data.loc[income_group_index].tw,
                input_data.loc[income_group_index].sf,
                input_data.loc[income_group_index].sm,
            ],
            "step": 1e-10,
            "maxn": 35,
            "min_step": 1e-12,
            "lambda": 1e-0,
            "Ftol": 1e-8,
            "htol": 1e-8,
        },
    }

    def calculate_labor_share(index):
        d = make_discounter_fdf(data)["d"]
        td = d(input_data.loc[income_group_index].sf) / d(
            input_data.loc[income_group_index].sm
        )
        H = make_hc_fdf(data)["h"]
        tH = H(input_data.loc[income_group_index].sf) / H(
            input_data.loc[income_group_index].sm
        )
        tL = (
            input_data.iloc[income_group_index]["Lf_{}".format(index)]
            / input_data.iloc[income_group_index]["Lm_{}".format(index)]
        )
        eta = data["fixed"]["eta_l"] if index == "l" else data["fixed"]["eta"]
        txi = input_data.loc[income_group_index].tw * td * tH * (tL ** (1 / eta))
        return txi / (1 + txi)

    data["fixed"]["xi_Ah"] = calculate_labor_share(
        "Ah"
    )  # female's share in traditional agriculture
    data["fixed"]["xi_Mh"] = calculate_labor_share(
        "Mh"
    )  # female's share in traditional manufacturing
    data["fixed"]["xi_Sh"] = calculate_labor_share(
        "Sh"
    )  # female's share in traditional services
    data["fixed"]["xi_Ar"] = calculate_labor_share(
        "Ar"
    )  # female's share in modern agriculture
    data["fixed"]["xi_Mr"] = calculate_labor_share(
        "Mr"
    )  # female's share in modern manufacturing
    data["fixed"]["xi_Sr"] = calculate_labor_share(
        "Sr"
    )  # female's share in modern services
    data["fixed"]["xi_l"] = calculate_labor_share("l")  # female's share in leisure

    if calibration_init:
        # this also checks if all parameters are initialized
        for k in data["calibrated"].keys():
            data["calibrated"][k][0] = calibration_init[k]

    return data


def set_calibrated_data(data, calibration_data, verbose=False):
    """Set new calibration parameters.

    Used to set calibration parameters from either a list or a dictionary. The argument
    `calibration_data` is expected to be a dictionary, the order of parameters does not matter. 

    Args:
        data (dict): Model data.
        calibration_data (dict): New calibrated parameters to be used.
    """
    for k in calibration_data.keys():
        data["calibrated"][k][0] = calibration_data[k]
    if verbose:
        print(f"Calibrated Values = {calibration_data}")

    return data


def get_calibration_bounds(data, keys):
    """Get the calibration parameter bounds.

    Returns a list of tuples with lower and upper bounds for the calibrated variables.

    Args:
        data (dict): Model data.
        keys (list): List of calibrated parameter names.
    """
    bounds = [data["calibrated"][k][1] for k in keys]

    return bounds


def update_model_data(data, income_group, calibration_init):
    """Update model data for an income group.

    Expected to be used for constructing model data structures for estimations not including
    preference parameters. Overrides the income group and the calibration initializing values
    of an existing (passed) data structure.

    Args:
        data (dict): Model data.
        income_group (str): Income group string, among "low", "middle", "high",
            and "all".
        calibration_init (dict): Initial values for calibrated parameters for the updated model.
    """
    data["income_group"] = income_group

    # this also checks if all parameters are initialized
    for k in data["calibrated"].keys():
        data["calibrated"][k][0] = calibration_init[k]

    return data


def print_model_data(model_data):
    """Indented model data print."""

    class encoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    print(json.dumps(model_data, indent=2, cls=encoder))


def make_working_life(model_data):
    """Prepare working life function.

    See section (A.1)."""
    T = model_data["fixed"]["T"]

    def delta(s):
        return T - s

    return delta


def make_female_lifetime_schooling_cost_fdf(model_data):
    """Prepare female lifetime cost of schooling function.

    See equation (C.1). The expression is part of the objective."""
    rho = model_data["fixed"]["rho"]
    beta_f = model_data["calibrated"]["beta_f"][0]

    def dW(s):
        return -beta_f * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_f / rho, "dW": dW}


def make_male_lifetime_schooling_cost_fdf(model_data):
    """Prepare male lifetime cost of schooling function.

    See equation (C.1). The expression is part of the objective."""
    rho = model_data["fixed"]["rho"]
    beta_m = model_data["calibrated"]["beta_f"][0] / model_data["fixed"]["tbeta"]

    def dW(s):
        return -beta_m * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_m / rho, "dW": dW}


def make_female_wage_bill(model_data, indices):
    """Prepare female wage bill functions.

    See equations (B.4), (C.18), and (C.32).
    """
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]

    if indices == "l":
        eta = model_data["fixed"]["eta_l"]
        xi_i = model_data["fixed"]["xi_{}".format(indices)]
    else:
        eta = model_data["fixed"]["eta"]
        xi_i = model_data["fixed"]["xi_{}".format(indices)]

    if indices.endswith("r"):

        def adjustment(sf, sm):
            return 1

    else:

        def adjustment(sf, sm):
            return d(sf) * h(sf) / d(sm) / h(sm)

    A = m.pow(xi_i / (1 - xi_i), -eta)

    def If(tw, sf, sm):
        return 1 / (1 + A * m.pow(tw, eta - 1) * m.pow(adjustment(sf, sm), eta - 1))

    return If


def make_male_wage_bill(model_data, index):
    """Prepare female wage bill functions.

    See equations (B.4), and (C.18). The leisure bill is obtained by subtracting (C.32)
    from one.
    """
    If_ip = make_female_wage_bill(model_data, index)

    return lambda tw, sf, sm: 1 - If_ip(tw, sf, sm)


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
    """Find all calibrated relative productivities with left (sector) index."""
    return {
        k[4:]
        for k in model_data["calibrated"].keys()
        if k.startswith("Z_{}".format(left))
    }


def productivity_conjugate_left_indices(model_data, right):
    """Find all calibrated relative productivities with right (technology) index."""
    return {
        k[2:4]
        for k in model_data["calibrated"].keys()
        if k.startswith("Z_") and k.endswith(right)
    }


def productivity_conjugate_indices(model_data, index):
    """Find calibrated relative productivities with left (sector) or right (technology) index."""
    return productivity_conjugate_right_indices(
        model_data, index
    ) | productivity_conjugate_left_indices(model_data, index)


def make_relative_consumption_expenditure(model_data, over, under):
    """Prepare relative consumption (non leisure) expenditure function.

    Expects that both passed indices are of the form 'ip' where 'i' is a sector among agriculture
    ('a'), manufacturing ('m'), or services ('s'), and 'p' is a production type between modern
    ('m') and traditional ('t'). See equations (C.41), (C.48), and (C.49). Relative expenditures
    involving leisure are handled by make_relative_expenditure().
    """
    # trivial case
    if over == under:
        return lambda tw, sf, sm: 1

    # calculate indirectly if we don't have the relative productivity
    direct = has_relative_productivity(model_data, over, under)
    if direct <= 0:
        # check if inverting works
        if direct == -1:
            E_jqip = make_relative_consumption_expenditure(model_data, under, over)
            return lambda tw, sf, sm: 1 / E_jqip(tw, sf, sm)
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
            return lambda tw, sf, sm: E_ipkr(tw, sf, sm) * E_krjq(tw, sf, sm)
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
                lambda tw, sf, sm: E_ipkr(tw, sf, sm)
                * E_krny(tw, sf, sm)
                * E_nyjq(tw, sf, sm)
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
        return lambda tw, sf, sm: (
            E_ipkr(tw, sf, sm)
            * E_krny(tw, sf, sm)
            * E_nyow(tw, sf, sm)
            * E_owjq(tw, sf, sm)
        )

    # default case
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]
    eta = model_data["fixed"]["eta"]
    sigma = model_data["fixed"]["sigma"]
    xi_ip = model_data["fixed"]["xi_{}".format(over)]
    xi_jq = model_data["fixed"]["xi_{}".format(under)]
    Z_ipjq = model_data["calibrated"]["Z_{}{}".format(over, under)][0]
    I_ip = make_female_wage_bill(model_data, over)
    I_jq = make_female_wage_bill(model_data, under)

    if over[0] == under[0]:
        return lambda tw, sf, sm: m.pow(
            Z_ipjq
            * m.pow(xi_ip / xi_jq, eta / (eta - 1))
            * m.pow(I_jq(tw, sf, sm) / I_ip(tw, sf, sm), 1 / (eta - 1))
            * d(sf)
            * h(sf)
            / d(0),
            sigma - 1,
        )
    else:
        epsilon = model_data["fixed"]["epsilon"]
        ir = over[0] + ("h" if over[1] == "r" else "r")
        E_ipir = make_relative_consumption_expenditure(model_data, over, ir)
        jy = under[0] + ("h" if under[1] == "r" else "r")
        E_jqjy = make_relative_consumption_expenditure(model_data, under, jy)
        I_ip = make_female_wage_bill(model_data, over)
        I_jq = make_female_wage_bill(model_data, under)

        return lambda tw, sf, sm: (
            m.pow(Z_ipjq, epsilon - 1)
            * m.pow(
                m.pow(xi_ip / xi_jq, eta / (eta - 1))
                * m.pow(I_ip(tw, sf, sm) / I_jq(tw, sf, sm), 1 / (1 - eta)),
                epsilon - 1,
            )
            * m.pow(1 + 1 / E_jqjy(tw, sf, sm), (sigma - epsilon) / (sigma - 1))
            * m.pow(1 + 1 / E_ipir(tw, sf, sm), (epsilon - sigma) / (sigma - 1))
        )


def make_sectoral_expenditure_share_of_consumption(model_data, sector):
    """Prepare sectoral expenditure share unction.

    Returns a function that calculates the share of a sector's expenditure in total expenditure
    for commodities. Summing these functions over all sectors gives the constant unit function.
    See equation (C.52).
    """

    def E_j(tw, sf, sm):
        Eimihvs = [
            make_relative_consumption_expenditure(
                model_data, "{}r".format(s), "{}h".format(s)
            )(tw, sf, sm)
            for s in model_data["sectors"]
        ]
        Ejmihvs = [
            make_relative_consumption_expenditure(
                model_data, "{}r".format(sector), "{}h".format(s)
            )(tw, sf, sm)
            for s in model_data["sectors"]
        ]
        Ejmjhv = make_relative_consumption_expenditure(
            model_data, "{}r".format(sector), "{}h".format(sector)
        )(tw, sf, sm)
        A = Ejmjhv / (1 + Ejmjhv)
        return 1 / sum(
            [
                A * (1 + Eimihvs[i]) / Ejmihvs[i]
                for i in range(len(model_data["sectors"]))
            ]
        )

    return E_j


def make_female_labor_ratio(model_data, over, under):
    """Prepare female labor ratio function.

    Expects that both pass indices are as in make_relative_consumption_expenditure().
    See equation (D.9).
    """
    E_ipjq = make_relative_expenditure(model_data, over, under)
    I_ip = make_female_wage_bill(model_data, over)
    I_jq = make_female_wage_bill(model_data, under)
    d = make_discounter_fdf(model_data)["d"]
    delta = make_working_life(model_data)

    return lambda tw, sf, sm: (
        E_ipjq(tw, sf, sm)
        * I_ip(tw, sf, sm)
        / I_jq(tw, sf, sm)
        * m.pow(
            d(sf) / d(0) * delta(0) / delta(sf),
            over.endswith("r") - under.endswith("r"),
        )
    )


def make_male_labor_ratio(model_data, over, under):
    """Prepare male labor ratio function.

    Based on the female ratio calculation of make_female_labor_ratio(). See
    equation (D.14).
    """
    E_ipjq = make_relative_expenditure(model_data, over, under)
    I_ip = make_male_wage_bill(model_data, over)
    I_jq = make_male_wage_bill(model_data, under)
    d = make_discounter_fdf(model_data)["d"]
    delta = make_working_life(model_data)

    return lambda tw, sf, sm: (
        E_ipjq(tw, sf, sm)
        * I_ip(tw, sf, sm)
        / I_jq(tw, sf, sm)
        * m.pow(
            d(sf) / d(0) * delta(0) / delta(sf),
            over.endswith("r") - under.endswith("r"),
        )
    )


def make_aggregate_female_labor_ratio(model_data, index):
    """Prepare aggregate female labor ratio function.

    Sum of all non leisure female labor ratios for fixed right index.
    See appendix's equation (D.11).
    """

    def R(tw, sf, sm):
        Risjpsv = [
            make_female_labor_ratio(model_data, "{}{}".format(s, t), index)(tw, sf, sm)
            for s in model_data["sectors"]
            for t in model_data["technologies"]
        ]
        return sum(Risjpsv)

    return R


def make_implicit_female_traditional_technology_coefficient(model_data, sector):
    """Prepare implicit female traditional technology coefficient function.

    See appendix's equation (F.1).
    """

    def Pih(tw, sf, sm):
        ih = "{}h".format(sector)
        im = "{}r".format(sector)

        sigma = model_data["fixed"]["sigma"]
        epsilon = model_data["fixed"]["epsilon"]
        eta = model_data["fixed"]["eta"]
        Zim = model_data["fixed"]["Z_{}".format(im)]
        xiim = model_data["fixed"]["xi_{}".format(im)]
        delta = make_working_life(model_data)

        Eihim = make_relative_consumption_expenditure(model_data, im, ih)
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        Iim = make_female_wage_bill(model_data, im)
        h = make_hc_fdf(model_data)["h"]
        Rimih = make_female_labor_ratio(model_data, im, ih)

        return (
            m.pow(1 + Eihim(tw, sf, sm), sigma / (sigma - 1))
            * m.pow(Ei(tw, sf, sm), epsilon / (1 - epsilon))
            * Zim
            * m.pow(xiim / Iim(tw, sf, sm), eta / (eta - 1))
            * h(sf)
            * delta(sf)
            * Rimih(tw, sf, sm)
        )

    return Pih


def make_base_female_traditional_labor(model_data):
    """Prepare the base female traditional labor control function.

    The labor control calculation depends on the corresponding sector's traditional productivity
    level. The sector is picked from the model_data["fixed"] parameters. All remaining labor
    control functions are calculated based on this control. See appendix's equation (F.4).
    """
    sector = [p[2:3] for p in model_data["fixed"] if re.search("Z_[AMS]r", p)][0]

    def Lfih(tw, sf, sm):
        ih = "{}h".format(sector)
        im = "{}r".format(sector)

        varphi = model_data["calibrated"]["varphi"][0]
        hat_c = model_data["calibrated"]["hat_c"][0]
        Lf = model_data["fixed"]["Lf"]

        Eimih = make_relative_consumption_expenditure(model_data, im, ih)
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        Il = make_female_wage_bill(model_data, "l")
        Iih = make_female_wage_bill(model_data, ih)

        Rih = make_aggregate_female_labor_ratio(model_data, ih)

        alpha = (
            varphi
            * (1 + Eimih(tw, sf, sm))
            / Ei(tw, sf, sm)
            * Il(tw, sf, sm)
            / Iih(tw, sf, sm)
        )

        Pih = make_implicit_female_traditional_technology_coefficient(
            model_data, sector
        )
        return (Lf + (alpha * hat_c) / Pih(tw, sf, sm)) / (Rih(tw, sf, sm) + alpha)

    return Lfih


def make_subsistence_consumption_share(model_data):
    """Prepare subsistence consumption share function.

    The consumption share is sector independent. The numerical calculation is based on
    make_base_female_traditional_labor(). See appendix's equation (F.5).
    """
    sector = [p[2:3] for p in model_data["fixed"] if re.search("Z_[AMS]r", p)][0]

    def subsh(tw, sf, sm):
        hat_c = model_data["calibrated"]["hat_c"][0]
        Pih = make_implicit_female_traditional_technology_coefficient(
            model_data, sector
        )
        Lfih = make_base_female_traditional_labor(model_data)
        return hat_c / Pih(tw, sf, sm) / Lfih(tw, sf, sm)

    return subsh


def make_non_subsistence_consumption_share(model_data):
    """Prepare non subsistence consumption share function.

    See make_subsistence_consumption_share().
    """

    def nsubsh(tw, sf, sm):
        subssh = make_subsistence_consumption_share(model_data)
        return 1 - subssh(tw, sf, sm)

    return nsubsh


def make_relative_expenditure(model_data, over, under):
    """Prepare expenditure function.

    This ties up a loose end in the functionality of make_relative_consumption_expenditure().
    It can handle cases where any of the two indices is leisure ('l'). Leisure requires special
    treatment because its relative expenditure equations contain the non subsistence consumption
    share. See appendix's equation (C.54).
    """
    # trivial case
    if over == under:
        return lambda tw, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda tw, sf, sm: 1 / make_relative_expenditure(
            model_data, under, over
        )(tw, sf, sm)
    if over == "l" and under.endswith("r"):
        varphi = model_data["calibrated"]["varphi"][0]
        sector = under[0]
        other = under[0] + "h"

        def E_lj(tw, sf, sm):
            nsubsh = make_non_subsistence_consumption_share(model_data)
            Ej = make_sectoral_expenditure_share_of_consumption(model_data, sector)
            Eihim = make_relative_consumption_expenditure(model_data, other, under)

            return (
                varphi * nsubsh(tw, sf, sm) / Ej(tw, sf, sm) * (1 + Eihim(tw, sf, sm))
            )

        return E_lj
    if over == "l" and under.endswith("h"):
        E_lsm = make_relative_expenditure(model_data, "l", under[0] + "r")
        E_smsh = make_relative_expenditure(model_data, under[0] + "r", under)
        return lambda tw, sf, sm: E_lsm(tw, sf, sm) * E_smsh(tw, sf, sm)

    # non leisure case
    return make_relative_consumption_expenditure(model_data, over, under)


def make_female_flow_time_allocation_ratio(model_data, over, under):
    """Prepare female flow time allocation ratio function.

    Covers the cases not handled by make_female_labor_ratio(). It can handle
    cases where one of the indices is leisure ('l'). See appendix's equation (D.10).
    """
    # trivial case
    if over == under:
        return lambda tw, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda tw, sf, sm: (
            1
            / make_female_flow_time_allocation_ratio(model_data, under, over)(
                tw, sf, sm
            )
        )
    if over == "l":
        Elip = make_relative_expenditure(model_data, over, under)
        Il = make_female_wage_bill(model_data, over)
        Iip = make_female_wage_bill(model_data, under)
        d = make_discounter_fdf(model_data)["d"]
        delta = make_working_life(model_data)
        return lambda tw, sf, sm: (
            Elip(tw, sf, sm)
            * Il(tw, sf, sm)
            / Iip(tw, sf, sm)
            * m.pow(d(sf) / d(0) * delta(0) / delta(sf), -under.endswith("r"))
        )

    # non leisure case
    return make_female_labor_ratio(model_data, over, under)


def make_male_flow_time_allocation_ratio(model_data, over, under):
    """Prepare male flow time allocation ratio function.

    Covers the cases not handled by make_male_labor_ratio(). It can handle
    cases where one of the indices is leisure ('l'). See appendix's equation (D.15).
    """
    # trivial case
    if over == under:
        return lambda tw, sf, sm: 1

    # leisure case
    if under == "l":
        return lambda tw, sf, sm: (
            1
            / make_male_flow_time_allocation_ratio(model_data, under, over)(tw, sf, sm)
        )
    if over == "l":
        Elip = make_relative_expenditure(model_data, over, under)
        Il = make_male_wage_bill(model_data, over)
        Iip = make_male_wage_bill(model_data, under)
        d = make_discounter_fdf(model_data)["d"]
        delta = make_working_life(model_data)
        return lambda tw, sf, sm: (
            Elip(tw, sf, sm)
            * Il(tw, sf, sm)
            / Iip(tw, sf, sm)
            * m.pow(d(sf) / d(0) * delta(0) / delta(sf), -under.endswith("r"))
        )

    # non leisure case
    return make_male_labor_ratio(model_data, over, under)


def make_aggregate_male_labor_ratio(model_data, index):
    """Prepare aggregate male labor ratio function.

    Sum of all non leisure male labor ratios for fixed right index.
    See appendix's equation (D.16).
    """

    def R(tw, sf, sm):
        Risjpsv = [
            make_male_flow_time_allocation_ratio(
                model_data, "{}{}".format(s, t), index
            )(tw, sf, sm)
            for s in model_data["sectors"]
            for t in model_data["technologies"]
        ]
        return sum(Risjpsv)

    return R


def make_aggregate_female_flow_time_allocation_ratio(model_data, index):
    """Prepare aggregate female flow time allocation ratio function.

    Sum of all female time allocation ratios. In contrast to
    make_aggregate_female_labor_ratio(), the sum includes leisure. The sum over all
    production types and sectors should be equal to one. See
    appendix's equation (D.12).
    """

    def R(tw, sf, sm):
        R_it = make_aggregate_female_labor_ratio(model_data, index)
        R_lit = make_female_flow_time_allocation_ratio(model_data, "l", index)
        return R_it(tw, sf, sm) + R_lit(tw, sf, sm)

    return R


def make_aggregate_male_flow_time_allocation_ratio(model_data, index):
    """Prepare aggregate male flow time allocation ratio function.

    Sum of all male time allocation ratios. In contrast to
    make_aggregate_male_labor_ratio(), the sum includes leisure. The sum over all
    production types and sectors should be equal one. See appendix's equation (D.17).
    """

    def R(tw, sf, sm):
        R_it = make_aggregate_male_labor_ratio(model_data, index)
        R_lit = make_male_flow_time_allocation_ratio(model_data, "l", index)
        return R_it(tw, sf, sm) + R_lit(tw, sf, sm)

    return R


def make_female_time_allocation_control(model_data, index):
    """Prepare a female time allocation control function.

    The female time allocation controls' calculations depend on make_base_female_traditional_labor().
    The base control is directly calculated. The remaining calculations use this base control. See
    appendix's equation (D.12). 
    """
    Lf = model_data["fixed"]["Lf"]
    Rfip = make_aggregate_female_flow_time_allocation_ratio(model_data, index)
    return lambda tw, sf, sm: Lf / Rfip(tw, sf, sm)


def make_female_modern_production_allocation(model_data):
    """Prepare female modern production allocation function.

    The sum of female modern production labor controls. See equation (C.12).
    """

    def Mf(tw, sf, sm):
        return sum(
            [
                make_female_time_allocation_control(model_data, "{}r".format(s))(
                    tw, sf, sm
                )
                for s in model_data["sectors"]
            ]
        )

    return Mf


def make_female_total_time_allocation(model_data):
    """Prepare female total time allocation function.

    The sum of female time allocation controls.
    """

    def Lf(tw, sf, sm):
        return sum(
            [
                make_female_time_allocation_control(model_data, "{}{}".format(s, t))(
                    tw, sf, sm
                )
                for s in model_data["sectors"]
                for t in model_data["technologies"]
            ]
        ) + make_female_time_allocation_control(model_data, "l")(tw, sf, sm)

    return Lf


def make_male_time_allocation_control(model_data, index):
    """Prepare a male time allocation control function.

    The male time allocation controls' calculations are based on the corresponding female controls.
    See appendix's equation (D.18).
    """
    Lm = model_data["fixed"]["Lm"]
    Rmip = make_aggregate_male_flow_time_allocation_ratio(model_data, index)
    return lambda tw, sf, sm: Lm / Rmip(tw, sf, sm)


def make_male_modern_production_allocation(model_data):
    """Prepare male modern production allocation function.

    The sum of male modern production labor controls. See equation (C.12).
    """

    def Mm(tw, sf, sm):
        return sum(
            [
                make_male_time_allocation_control(model_data, "{}r".format(s))(
                    tw, sf, sm
                )
                for s in model_data["sectors"]
            ]
        )

    return Mm


def make_male_total_time_allocation(model_data):
    """Prepare male total time allocation function.

    The sum of male time allocation controls.
    """

    def Lm(tw, sf, sm):
        return sum(
            [
                make_male_time_allocation_control(model_data, "{}{}".format(s, t))(
                    tw, sf, sm
                )
                for s in model_data["sectors"]
                for t in model_data["technologies"]
            ]
        ) + make_male_time_allocation_control(model_data, "l")(tw, sf, sm)

    return Lm


def make_female_total_wage_bill(model_data):
    """Prepare female total time allocation wage bill functions.

    See appendix's equation (D.19).
    """
    h = make_hc_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]

    def If_L(tw, sf, sm):
        Lfv = make_female_total_time_allocation(model_data)(tw, sf, sm)
        Lmv = make_male_total_time_allocation(model_data)(tw, sf, sm)

        return 1 / (1 + Lmv / Lfv * d(sm) / d(sf) * h(sm) / h(sf) / tw)

    return If_L


def make_reduced_constraints(model_data, index):
    """Prepare reduced constraints function.

    See appendix's equation (D.23).
    """

    def constraints(tw, sf, sm):
        Rfip = make_aggregate_female_flow_time_allocation_ratio(model_data, index)
        SumEjqipv = sum(
            [
                make_relative_expenditure(model_data, "{}{}".format(s, t), index)(
                    tw, sf, sm
                )
                for s in model_data["sectors"]
                for t in model_data["technologies"]
            ]
        )
        Iipv = make_female_wage_bill(model_data, index)(tw, sf, sm)
        ILv = make_female_total_wage_bill(model_data)(tw, sf, sm)

        return Rfip(tw, sf, sm) - SumEjqipv * Iipv / ILv

    return constraints


def make_female_schooling_condition(model_data, index):
    """Prepare female schooling condition function.

    See appendix's equation (E.2).
    """

    def schooling(tw, sf, sm):
        hc_fdf = make_hc_fdf(model_data)
        d_fdf = make_discounter_fdf(model_data)
        delta = make_working_life(model_data)
        g = hc_fdf["dh"](sf) / hc_fdf["h"](sf) + d_fdf["dd"](sf) / d_fdf["d"](sf)
        nsubc = make_non_subsistence_consumption_share(model_data)
        Lfip = make_female_time_allocation_control(model_data, index)
        sector = index[0]
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        other = sector + ("r" if sector == "h" else "h")
        Eiqip = make_relative_consumption_expenditure(model_data, other, index)
        Iip = make_female_wage_bill(model_data, index)
        Mf = make_female_modern_production_allocation(model_data)
        dWf = make_female_lifetime_schooling_cost_fdf(model_data)["dW"]

        return dWf(sf) + (
            Mf(tw, sf, sm)
            / Lfip(tw, sf, sm)
            * g
            / nsubc(tw, sf, sm)
            * Ei(tw, sf, sm)
            / (1 + Eiqip(tw, sf, sm))
            * Iip(tw, sf, sm)
            * delta(0)
        )

    return schooling


def make_male_schooling_condition(model_data, index):
    """Prepare male schooling condition function.

    See appendix's equation (E.3).
    """

    def schooling(tw, sf, sm):
        hc_fdf = make_hc_fdf(model_data)
        d_fdf = make_discounter_fdf(model_data)
        delta = make_working_life(model_data)
        g = hc_fdf["dh"](sm) / hc_fdf["h"](sm) + d_fdf["dd"](sm) / d_fdf["d"](sm)
        nsubc = make_non_subsistence_consumption_share(model_data)
        Lmip = make_male_time_allocation_control(model_data, index)
        sector = index[0]
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        other = sector + ("r" if sector == "h" else "h")
        Eiqip = make_relative_consumption_expenditure(model_data, other, index)
        Im_ip = make_male_wage_bill(model_data, index)
        Mm = make_male_modern_production_allocation(model_data)
        dWm = make_male_lifetime_schooling_cost_fdf(model_data)["dW"]

        return dWm(sm) + (
            Mm(tw, sf, sm)
            / Lmip(tw, sf, sm)
            * g
            / nsubc(tw, sf, sm)
            * Ei(tw, sf, sm)
            / (1 + Eiqip(tw, sf, sm))
            * Im_ip(tw, sf, sm)
            * delta(0)
        )

    return schooling


def make_schooling_condition_ratio(model_data, index):
    """Prepare female to male schooling condition function.

    See appendix's equation (E.5).
    """

    def schooling(tw, sf, sm):
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

        return dWf(sf) / dWm(sm) - (
            Mf(tw, sf, sm) / Mm(tw, sf, sm) * tw * g(sf) / g(sm)
        )

    return schooling


def make_foc(model_data):
    """Prepare the model's first order condition vector function."""
    f1 = make_reduced_constraints(model_data, "Sh")
    f21 = make_female_schooling_condition(model_data, "Sh")
    f22 = make_male_schooling_condition(model_data, "Sh")

    def f2(tw, sf, sm):
        return f21(tw, sf, sm) + f22(tw, sf, sm)

    f3 = make_schooling_condition_ratio(model_data, "Sh")

    def F(y):
        Lf = make_female_total_time_allocation(model_data)(y[0], y[1], y[2])
        Lm = make_male_total_time_allocation(model_data)(y[0], y[1], y[2])
        gamma = make_subsistence_consumption_share(model_data)(y[0], y[1], y[2])
        if np.abs(Lf - 1) > 1e-2:
            print(f"Warning: Inaccurate total female time allocation, Lf = {Lf}")
        if np.abs(Lm - 1) > 1e-2:
            print(f"Warning: Inaccurate total male time allocation, Lm = {Lm}")
        if gamma < 0 or gamma > 1:
            print(f"Warning: Inaccurate subsistence share, gamma = {gamma}")

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

        J = None
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
                except ZeroDivisionError:
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

    F = make_foc(model_data)
    J = make_jacobian(model_data)

    Ftol = model_data["optimizer"]["Ftol"]
    htol = model_data["optimizer"]["htol"]
    lam = model_data["optimizer"]["lambda"]
    maxn = model_data["optimizer"]["maxn"]
    n = 0
    converged = False
    yn = y.copy()
    Fv = None
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
            except (ValueError, np.linalg.LinAlgError):
                pass
        if not stepped:
            raise ValueError(
                "Household optimization solver failed to step at n = {}".format(n)
            )

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
    print("Returning tw, sf, sm = {} with foc = {}".format(y, Fv))

    return y


def make_calibration(
    model_data,
    calibrated_parameters,
    adaptive_optimizer_initialization=False,
    verbose=False,
):
    """Prepare calibration function."""
    min_sae = 100

    def errors(y):
        nonlocal model_data, min_sae
        model_data = set_calibrated_data(
            model_data, dict(zip(calibrated_parameters, y)), verbose=verbose
        )

        print("Numerically approximating model's solution:")
        y = solve_foc(model_data, np.asarray(model_data["optimizer"]["x0"]))
        sae = sum(
            [
                np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
                for _, v in model_data["calibrator"]["targets"].items()
            ]
        )
        if sae < min_sae:
            min_sae = sae
            if adaptive_optimizer_initialization:
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
                        for _, v in model_data["calibrator"]["targets"].items()
                    ]
                )
            )
        )

        return [
            np.abs(v[0] - v[1](model_data, y[0], y[1], y[2]))
            for _, v in model_data["calibrator"]["targets"].items()
        ]

    return errors


def save_calibration_if_not_exists(filename, calibration_results):
    """Save Calibrated Model."""

    if not exists(filename):
        fh = open(filename, "wb")
        pickle.dump(calibration_results, fh)
        fh.close()
        return True
    return False


def load_calibration(filename):
    """Load Saved Calibrated Model."""

    fh = open(filename, "rb")
    calibration_results = pickle.load(fh)
    fh.close()
    return calibration_results


def calibrate_if_not_exists_and_save(
    calibration_mode,
    income_group,
    initializers,
    adaptive_optimizer_initialization=False,
    verbose=False,
):
    """Calibrate the Model and Save the Results."""

    model_data = make_model_data(income_group)
    model_data = set_calibrated_data(model_data, initializers, verbose=verbose)

    print(f"Calibrating Model with {income_group.capitalize()} Income Data")
    print_model_data(model_data)

    errors = make_calibration(
        model_data,
        initializers.keys(),
        adaptive_optimizer_initialization=adaptive_optimizer_initialization,
        verbose=verbose,
    )
    bounds = get_calibration_bounds(model_data, initializers.keys())
    calibration_results = {}

    filename = f"../data/out/{calibration_mode}/{income_group}-income-calibration.pkl"
    if not exists(filename):
        calibration_results = minimize(
            lambda x: sum(errors(x)),
            [v for v in initializers.values()],
            bounds=bounds,
            method="Nelder-Mead",
            options={"disp": True},
        )
        save_calibration_if_not_exists(filename, calibration_results)
    else:
        calibration_results = load_calibration(filename)

    return calibration_results


def get_calibrated_model_solution(income_group, filename, initializers):
    model_data = make_model_data(income_group)
    calibration_results = load_calibration(filename)
    calibrated_data = dict(zip(initializers, calibration_results["x"]))
    model_data = set_calibrated_data(model_data, calibrated_data)
    y = solve_foc(model_data, np.asarray(model_data["optimizer"]["x0"])).tolist()
    model_data["optimizer"]["x0"] = y

    return model_data
