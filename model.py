"""Model file.

This file contains the model functions and the model solver. The
model has two types of production technologies (traditional and modern),
three sectors (agriculture, manufacturing, and services), two genders (f and m),
and schooling. Modern production occurs only after schooling. Firms choose
effective labor units.
"""

import copy
import json
import math as m
import numpy as np
import re

import model_traits


def make_discounter_fdf(model_data):
    """Prepare working life discounter function and derivative.

    See section (A.1).
    """
    rho = model_data["fixed"]["rho"]
    T = model_data["fixed"]["T"]

    def d(s):
        return 1 / (-rho) * np.exp((-rho) * T) - 1 / (-rho) * np.exp((-rho) * s)

    return {"d": d, "dd": lambda s: -np.exp(-rho * s)}


def make_human_capital_fdf(model_data):
    """Prepare human capital function and derivative.

    See equation (C.6).
    """
    zeta = model_data["fixed"]["zeta"]
    nu = model_data["fixed"]["nu"]

    def H(s):
        return np.exp(zeta / (1 - nu) * np.power(s, 1 - nu))

    return {"h": H, "dh": lambda s: H(s) * zeta * np.power(s, -nu)}


def set_free_parameters(data, free_parameters):
    """Set new free parameters.

    Used to set free parameters from either a dictionary.

    Args:
        data (dict): Model data.
        free_parameters (dict): New parameter values to be used.
    """
    # this also checks if all parameters are set
    for k in data["free"].keys():
        data["free"][k][0] = free_parameters[k]
    if data["config"]["verbose"]:
        data["config"]["logger"].info(f"Free Parameter Values = {free_parameters}")

    return data


def make_model_data(invariant_config):
    """Prepare model data for an income group.

    The configuration dictionary is deeply copied to avoid side effects. The
    configuration input should contain data for a specific calibration mode
    and income group.
    Args:
        config_init (dict): Configuration dictionary.
    """
    config_init = copy.deepcopy(invariant_config)

    data = {
        "hooks": {"hat_c": None},
        "free": {
            "hat_c": [None, (0, None)],  # adjusted subsistence term
            "varphi": [None, (1e-3, None)],  # leisure preference scale
            "beta_f": [None, (1e-3, None)],  # female's schooling cost
            # productivities-preferences parameters
            "Z_ArAh": [None, (1e-3, None)],
            "Z_MrMh": [None, (1e-3, None)],
            "Z_SrSh": [None, (1e-3, None)],
            "Z_ArSr": [None, (1e-3, None)],
            "Z_MrSr": [None, (1e-3, None)],
        },
        "fixed": {
            "eta": 2.27,  # labor input gender substitutability
            "eta_l": 2.27,  # leisure gender substitutability
            "epsilon": 0.002,  # output sectoral  substitutability
            "sigma": 2.0,  # output technological substitutability
            "nu": 0.58,  # log human capital curvature
            "zeta": 0.32,  # log human capital scale
            "rho": 0.04,  # subjective discount factor
            "tbeta": config_init["parameters"]["tbeta"],  # schooling costs ratio
            "Lf": 1.0,  # female's time endowment
            "Lm": 1.0,  # male's time endowment
            "T": config_init["parameters"]["T"],  # life expectancy
            "Z_Sr": 1.0,  # modern services productivity
        },
        "optimizer": {
            "x0": [
                config_init["parameters"]["tw"],
                config_init["parameters"]["sf"],
                config_init["parameters"]["sm"],
            ],
            "step": 1e-10,
            "maxn": 35,
            "min_step": 1e-12,
            "lambda": 1e-0,
            "Ftol": 1e-8,
            "htol": 1e-8,
        },
    }

    data["hooks"]["hat_c"] = lambda x: x["free"]["hat_c"][0]

    def calculate_labor_share(index):
        d = make_discounter_fdf(data)["d"]
        td = d(config_init["parameters"]["sf"]) / d(config_init["parameters"]["sm"])
        H = make_human_capital_fdf(data)["h"]
        tH = H(config_init["parameters"]["sf"]) / H(config_init["parameters"]["sm"])
        tL = (
            config_init["parameters"][f"Lf_{index}"]
            / config_init["parameters"][f"Lm_{index}"]
        )
        eta = data["fixed"]["eta_l"] if index == "l" else data["fixed"]["eta"]
        txi = config_init["parameters"]["tw"] * td * tH * (tL ** (1 / eta))
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

    data["config"] = config_init

    if config_init["initializers"] is not None:
        data = set_free_parameters(data, config_init["initializers"])

    return data


def get_calibration_bounds(model_data):
    """Get the calibration parameter bounds.

    Returns a list of tuples with lower and upper bounds for the calibrated variables.

    Args:
        data (dict): Model data.
        keys (list): List of calibrated parameter names.
    """
    bounds = [model_data["free"][k][1] for k in model_data["free"].keys()]

    return bounds


def json_model_data(model_data):
    """Indented model data string."""
    logger = model_data["config"]["logger"]
    del model_data["config"]["logger"]

    class encoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    dump = json.dumps(model_data, indent=2, cls=encoder)
    model_data["config"]["logger"] = logger

    return dump


def make_working_life(model_data):
    """Prepare working life function.

    See section (A.1).
    """
    T = model_data["fixed"]["T"]

    def delta(s):
        return T - s

    return delta


def make_female_lifetime_schooling_cost_fdf(model_data):
    """Prepare female lifetime cost of schooling function.

    See equation (C.1). The expression is part of the objective.
    """
    rho = model_data["fixed"]["rho"]
    beta_f = model_data["free"]["beta_f"][0]

    def dW(s):
        return -beta_f * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_f / rho, "dW": dW}


def make_male_lifetime_schooling_cost_fdf(model_data):
    """Prepare male lifetime cost of schooling function.

    See equation (C.1). The expression is part of the objective.
    """
    rho = model_data["fixed"]["rho"]
    beta_m = model_data["free"]["beta_f"][0] / model_data["fixed"]["tbeta"]

    def dW(s):
        return -beta_m * np.exp(-rho * s)

    return {"W": lambda s: -dW(s) / rho - beta_m / rho, "dW": dW}


def make_female_wage_bill(model_data, indices):
    """Prepare female wage bill functions.

    See equations (B.4), (C.18), and (C.32).
    """
    h = make_human_capital_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]

    if indices == "l":
        eta = model_data["fixed"]["eta_l"]
        xi_i = model_data["fixed"][f"xi_{indices}"]
    else:
        eta = model_data["fixed"]["eta"]
        xi_i = model_data["fixed"][f"xi_{indices}"]

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
    """Check if a relative productivity among the set parameters."""
    keys = model_data["free"].keys()
    return 1 if f"Z_{over}{under}" in keys else -1 if f"Z_{under}{over}" in keys else 0


def productivity_conjugate_right_indices(model_data, left):
    """Find all set relative productivities with left (sector) index."""
    return {k[4:] for k in model_data["free"].keys() if k.startswith(f"Z_{left}")}


def productivity_conjugate_left_indices(model_data, right):
    """Find all set relative productivities with right (technology) index."""
    return {
        k[2:4]
        for k in model_data["free"].keys()
        if k.startswith("Z_") and k.endswith(right)
    }


def productivity_conjugate_indices(model_data, index):
    """Find set relative productivities with left (sector) or right (technology) index."""
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
    h = make_human_capital_fdf(model_data)["h"]
    d = make_discounter_fdf(model_data)["d"]
    eta = model_data["fixed"]["eta"]
    sigma = model_data["fixed"]["sigma"]
    xi_ip = model_data["fixed"][f"xi_{over}"]
    xi_jq = model_data["fixed"][f"xi_{under}"]
    Z_ipjq = model_data["free"][f"Z_{over}{under}"][0]
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
            make_relative_consumption_expenditure(model_data, f"{s}r", f"{s}h")(
                tw, sf, sm
            )
            for s in model_traits.sector_indices()
        ]
        Ejmihvs = [
            make_relative_consumption_expenditure(model_data, f"{sector}r", f"{s}h")(
                tw, sf, sm
            )
            for s in model_traits.sector_indices()
        ]
        Ejmjhv = make_relative_consumption_expenditure(
            model_data, f"{sector}r", f"{sector}h"
        )(tw, sf, sm)
        A = Ejmjhv / (1 + Ejmjhv)
        return 1 / sum(
            [
                A * (1 + Eimihvs[i]) / Ejmihvs[i]
                for i in range(len(model_traits.sector_indices()))
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
            make_female_labor_ratio(model_data, f"{s}{t}", index)(tw, sf, sm)
            for s in model_traits.sector_indices()
            for t in model_traits.technology_indices()
        ]
        return sum(Risjpsv)

    return R


def make_implicit_female_traditional_technology_coefficient(model_data, sector):
    """Prepare implicit female traditional technology coefficient function.

    See appendix's equation (F.1).
    """

    def Pih(tw, sf, sm):
        ih = f"{sector}h"
        im = f"{sector}r"

        sigma = model_data["fixed"]["sigma"]
        epsilon = model_data["fixed"]["epsilon"]
        eta = model_data["fixed"]["eta"]
        Zim = model_data["fixed"][f"Z_{im}"]
        xiim = model_data["fixed"][f"xi_{im}"]
        delta = make_working_life(model_data)

        Eihim = make_relative_consumption_expenditure(model_data, im, ih)
        Ei = make_sectoral_expenditure_share_of_consumption(model_data, sector)
        Iim = make_female_wage_bill(model_data, im)
        h = make_human_capital_fdf(model_data)["h"]
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
        ih = f"{sector}h"
        im = f"{sector}r"

        varphi = model_data["free"]["varphi"][0]
        hat_c = model_data["hooks"]["hat_c"](model_data)
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
        hat_c = model_data["hooks"]["hat_c"](model_data)
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
        varphi = model_data["free"]["varphi"][0]
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
            make_male_flow_time_allocation_ratio(model_data, f"{s}{t}", index)(
                tw, sf, sm
            )
            for s in model_traits.sector_indices()
            for t in model_traits.technology_indices()
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

    The female time allocation controls' calculations depend on
    make_base_female_traditional_labor(). The base control is directly calculated. The
    remaining calculations use this base control. See appendix's equation (D.12).
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
                make_female_time_allocation_control(model_data, f"{s}r")(tw, sf, sm)
                for s in model_traits.sector_indices()
            ]
        )

    return Mf


def make_female_traditional_production_allocation(model_data):
    """Prepare female traditional production allocation function.

    The sum of female traditional production labor controls.
    """

    def Mf(tw, sf, sm):
        return sum(
            [
                make_female_time_allocation_control(model_data, f"{s}h")(tw, sf, sm)
                for s in model_traits.sector_indices()
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
                make_female_time_allocation_control(model_data, f"{s}{t}")(tw, sf, sm)
                for s in model_traits.sector_indices()
                for t in model_traits.technology_indices()
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
                make_male_time_allocation_control(model_data, f"{s}r")(tw, sf, sm)
                for s in model_traits.sector_indices()
            ]
        )

    return Mm


def make_male_traditional_production_allocation(model_data):
    """Prepare male traditional production allocation function.

    The sum of male traditional production labor controls.
    """

    def Mm(tw, sf, sm):
        return sum(
            [
                make_male_time_allocation_control(model_data, f"{s}h")(tw, sf, sm)
                for s in model_traits.sector_indices()
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
                make_male_time_allocation_control(model_data, f"{s}{t}")(tw, sf, sm)
                for s in model_traits.sector_indices()
                for t in model_traits.technology_indices()
            ]
        ) + make_male_time_allocation_control(model_data, "l")(tw, sf, sm)

    return Lm


def make_female_total_wage_bill(model_data):
    """Prepare female total time allocation wage bill functions.

    See appendix's equation (D.19).
    """
    h = make_human_capital_fdf(model_data)["h"]
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
                make_relative_expenditure(model_data, f"{s}{t}", index)(tw, sf, sm)
                for s in model_traits.sector_indices()
                for t in model_traits.technology_indices()
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
        hc_fdf = make_human_capital_fdf(model_data)
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
        hc_fdf = make_human_capital_fdf(model_data)
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
        hc_fdf = make_human_capital_fdf(model_data)
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
            model_data["logger"].warning(
                f"Inaccurate total female time allocation, Lf = {Lf}"
            )
        if np.abs(Lm - 1) > 1e-2:
            model_data["logger"].warning(
                f"Inaccurate total male time allocation, Lm = {Lm}"
            )
        if gamma < 0 or gamma > 1:
            model_data["logger"].warning(
                f"Inaccurate subsistence share, gamma = {gamma}"
            )

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
                yl = copy.deepcopy(y)
                yl[i] = yl[i] - half_step
                yr = copy.deepcopy(y)
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
    yn = copy.deepcopy(y)
    Fv = None
    while n <= maxn and not converged:
        y = copy.deepcopy(yn)
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
            if np.any(yn < 0):
                continue
            try:
                Fvn = F(yn)
                Jvn = J(yn)
                np.linalg.inv(Jvn)
                if np.linalg.norm(Fvn) < Flen:
                    stepped = not np.isnan(Jvn).any()
            except (ValueError, np.linalg.LinAlgError):
                pass
        if not stepped:
            raise ValueError(f"Household optimization solver failed to step at n = {n}")

        n = n + 1
        hlen = np.linalg.norm(yn - y)
        converged = Flen <= Ftol or hlen <= htol
        model_data["config"]["logger"].info(
            f"n = {n: >2} |F| = {Flen:4.4f} |h| = {hlen:4.4f} "
            + f"y = {y[0]:4.2f} {y[1]:4.2f} {y[2]:4.2f}]"
        )
    if not converged:
        model_data["config"]["logger"].warning(
            "Household optimization solver did not converge"
        )
    model_data["config"]["logger"].info(f"Returning tw, sf, sm = {y} with foc = {Fv}")

    return y
