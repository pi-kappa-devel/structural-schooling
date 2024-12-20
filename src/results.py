"""Figure creation file.

Creates the figures for the manuscript and the appendix. Not all created figures
are used in the manuscript.

@see "Why does the Schooling Gap Close while the Wage Gap Persists across Country
Income Comparisons?".
"""

import copy
import functools
import json
from math import pi
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fminbound

import calibration
import calibration_traits
import config
import model_traits
import model

hlinestyle = ":"
flinestyle = "-"
mlinestyle = "--"
hcolors = ["#006400", "#008000", "#3CB371", "#90EE90", "#00FF00", "#ADFF2F"]
fcolors = ["#A52A2A", "#8B4513", "#D2691E", "	#B8860B", "#F4A460", "#BC8F8F"]
mcolors = ["#191970", "#0000FF", "#4169E1", "#1E90FF", "#00BFFF", "#B0C4DE"]
glinestyles = {"f": "solid", "m": "dashed"}
slinestyles = {"S": "-", "M": "--", "A": "-.", "l": ":"}
tmarkers = {"r": "", "h": "v", "l": "+"}
markersize = 4.0
markevery = 5

main_timestamp = "20230725203501"
main_income_group = "all"
main_calibration_setup = "no-schooling"

# fmt: off
income_groups = ["low", "middle", "high", "all"]
calibration_setups = calibration_traits.setups()

initializer_names = [
    "hat_c", "varphi",
    "beta_f",  # "beta_m",
    "Z_ArAh", "Z_MrMh", "Z_SrSh", "Z_ArSr", "Z_MrSr",
]

data_female_labor_shares = {
  "low": [0.0815877, 0.0062807, 0.2938025, 0.0215187, 0.0126192, 0.0363058, 0.5478855],
  "middle": [0.0281231, 0.0037166, 0.2975294, 0.0047409, 0.0191781, 0.0787491, 0.5679629],
  "high": [0.0042724, 0.0009837, 0.2389524, 0.0023376, 0.0223466, 0.1015646, 0.6295427],
  "all": [0.0379944, 0.0036603, 0.2767614, 0.0095324, 0.0180480, 0.0722065, 0.5817970]
}
data_male_labor_shares = {
    "low": [0.0899835, 0.0075116, 0.1265374, 0.0434648, 0.0262223, 0.0810602, 0.6252202],
    "middle": [0.0446018, 0.0058335, 0.1007717, 0.0289257, 0.0493341, 0.1208478, 0.6496854],
    "high": [0.0076562, 0.0060439, 0.0976458, 0.0078905, 0.0785629, 0.1149185, 0.6872821],
    "all": [0.0474138, 0.0064630, 0.1083183, 0.0267603, 0.0513731, 0.1056088, 0.6540626]
}
data_subsistence_shares = {"low": 0.23, "middle": 0.06, "high": 0.02, "all": 0.1033}
# fmt: on


def update_data_from_productivity(data, productivity_index, scale):
    """Update model data for a given  productivity factor."""
    for Z_parameter in data["free"].keys():
        if Z_parameter.endswith(productivity_index):
            data["free"][Z_parameter][0] /= scale
        elif productivity_index in Z_parameter:
            data["free"][Z_parameter][0] *= scale
    return data


def make_relative_expenditure_of_production_share(
    invariant_solution,
    expenditure_over,
    expenditure_under,
    production_share_gender,
    production_share_index,
):
    """Make a function returning relative expenditures for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def relative_expenditure_of_female(xif_under):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_under
        return model.make_relative_consumption_expenditure(
            data["model"], expenditure_over, expenditure_under
        )(*data["model"]["optimizer"]["xstar"])

    def relative_expenditure_of_male(xim_under):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_under
        return model.make_relative_consumption_expenditure(
            data["model"], expenditure_over, expenditure_under
        )(*data["model"]["optimizer"]["xstar"])

    return (
        relative_expenditure_of_female
        if production_share_gender == "f"
        else relative_expenditure_of_male
    )


def make_relative_expenditure_of_productivity(
    invariant_solution, expenditure_over, expenditure_under, productivity_index
):
    """Make a function returning relative expenditures for a given productivity factor."""

    def relative_expenditure(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_relative_consumption_expenditure(
            updated_data, expenditure_over, expenditure_under
        )(*data["model"]["optimizer"]["xstar"])

    return relative_expenditure


def make_expenditure_share_of_production_share(
    invariant_solution,
    expenditure_sector,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the expenditure share for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def expenditure_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_sectoral_expenditure_share_of_consumption(
            data["model"], expenditure_sector
        )(*data["model"]["optimizer"]["xstar"])

    def expenditure_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_sectoral_expenditure_share_of_consumption(
            data["model"], expenditure_sector
        )(*data["model"]["optimizer"]["xstar"])

    return (
        expenditure_share_of_female
        if production_share_gender == "f"
        else expenditure_share_of_male
    )


def make_expenditure_share_of_productivity(
    invariant_solution, expenditure_sector, productivity_index
):
    """Make a function returning the expenditure share for a given productivity factor."""

    def expenditure_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_sectoral_expenditure_share_of_consumption(
            updated_data, expenditure_sector
        )(*data["model"]["optimizer"]["xstar"])

    return expenditure_share


def make_wage_bill_of_production_share(
    invariant_solution,
    bill_gender,
    bill_index,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the wage bill ratio for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def female_wage_bill_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_female_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    def female_wage_bill_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_female_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_wage_bill_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_male_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_wage_bill_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_male_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    if bill_gender == "f" and production_share_gender == "f":
        return female_wage_bill_of_female
    elif bill_gender == "f" and production_share_gender == "m":
        return female_wage_bill_of_male
    elif bill_gender == "m" and production_share_gender == "f":
        return male_wage_bill_of_female
    return male_wage_bill_of_male


def make_wage_bill_of_productivity(
    invariant_solution, bill_gender, bill_index, productivity_index
):
    """Make a function returning the wage bill ratio for a given productivity factor."""
    data = copy.deepcopy(invariant_solution)

    def female_wage_bill(_):
        return model.make_female_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_wage_bill(_):
        return model.make_male_wage_bill(data["model"], bill_index)(
            *data["model"]["optimizer"]["xstar"]
        )

    if bill_gender == "f":
        return female_wage_bill
    return male_wage_bill


def make_time_allocation_ratio_of_production_share(
    invariant_solution,
    allocation_gender,
    allocation_over,
    allocation_under,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the time allocation ratio for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def female_flow_time_allocation_ratio_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_female_flow_time_allocation_ratio(
            data["model"], allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    def female_flow_time_allocation_ratio_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_female_flow_time_allocation_ratio(
            data["model"], allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    def male_flow_time_allocation_ratio_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_male_flow_time_allocation_ratio(
            data["model"], allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    def male_flow_time_allocation_ratio_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_male_flow_time_allocation_ratio(
            data["model"], allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    if allocation_gender == "f" and production_share_gender == "f":
        return female_flow_time_allocation_ratio_of_female
    elif allocation_gender == "f" and production_share_gender == "m":
        return female_flow_time_allocation_ratio_of_male
    elif allocation_gender == "m" and production_share_gender == "f":
        return male_flow_time_allocation_ratio_of_female
    return male_flow_time_allocation_ratio_of_male


def make_time_allocation_ratio_of_productivity(
    invariant_solution,
    allocation_gender,
    allocation_over,
    allocation_under,
    productivity_index,
):
    """Make a function returning the time allocation ratio for a given productivity factor."""

    def female_flow_time_allocation_ratio(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_female_flow_time_allocation_ratio(
            updated_data, allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    def male_flow_time_allocation_ratio(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_male_flow_time_allocation_ratio(
            updated_data, allocation_over, allocation_under
        )(*data["model"]["optimizer"]["xstar"])

    if allocation_gender == "f":
        return female_flow_time_allocation_ratio
    return male_flow_time_allocation_ratio


def make_time_allocation_share_of_production_share(
    invariant_solution,
    allocation_gender,
    allocation_index,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the time allocation share for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def female_time_allocation_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            data["model"], allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    def female_time_allocation_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            data["model"], allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    def male_time_allocation_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(
            data["model"], allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    def male_time_allocation_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(
            data["model"], allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    if allocation_gender == "f" and production_share_gender == "f":
        return female_time_allocation_share_of_female
    elif allocation_gender == "f" and production_share_gender == "m":
        return female_time_allocation_share_of_male
    elif allocation_gender == "m" and production_share_gender == "f":
        return male_time_allocation_share_of_female
    return male_time_allocation_share_of_male


def make_time_allocation_share_of_productivity(
    invariant_solution, allocation_gender, allocation_index, productivity_index
):
    """Make a function returning the time allocation share for a given productivity factor."""

    def female_time_allocation_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            updated_data, allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    def male_time_allocation_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(
            updated_data, allocation_index
        )(*data["model"]["optimizer"]["xstar"])

    if allocation_gender == "f":
        return female_time_allocation_share
    return male_time_allocation_share


def make_modern_share_of_production_share(
    invariant_solution, modern_gender, production_share_gender, production_share_index
):
    """Make a function returning the modern share for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def female_modern_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_female_modern_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def female_modern_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_female_modern_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_modern_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_male_modern_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_modern_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_male_modern_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    if modern_gender == "f" and production_share_gender == "f":
        return female_modern_share_of_female
    elif modern_gender == "f" and production_share_gender == "m":
        return female_modern_share_of_male
    elif modern_gender == "m" and production_share_gender == "f":
        return male_modern_share_of_female
    return male_modern_share_of_male


def make_modern_share_of_productivity(
    invariant_solution, modern_gender, productivity_index
):
    """Make a function returning the modern share for a given productivity factor."""

    def female_modern_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_female_modern_production_allocation(updated_data)(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_modern_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_male_modern_production_allocation(updated_data)(
            *data["model"]["optimizer"]["xstar"]
        )

    if modern_gender == "f":
        return female_modern_share
    return male_modern_share


def make_traditional_share_of_production_share(
    invariant_solution,
    traditional_gender,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the traditional share for a given production share."""
    data = copy.deepcopy(invariant_solution)

    def female_traditional_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_female_traditional_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def female_traditional_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_female_traditional_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_traditional_share_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return model.make_male_traditional_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_traditional_share_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return model.make_male_traditional_production_allocation(data["model"])(
            *data["model"]["optimizer"]["xstar"]
        )

    if traditional_gender == "f" and production_share_gender == "f":
        return female_traditional_share_of_female
    elif traditional_gender == "f" and production_share_gender == "m":
        return female_traditional_share_of_male
    elif traditional_gender == "m" and production_share_gender == "f":
        return male_traditional_share_of_female
    return male_traditional_share_of_male


def make_traditional_share_of_productivity(
    invariant_solution, traditional_gender, productivity_index
):
    """Make a function returning the traditional share for a given productivity factor."""

    def female_traditional_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_female_traditional_production_allocation(updated_data)(
            *data["model"]["optimizer"]["xstar"]
        )

    def male_traditional_share(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return model.make_male_traditional_production_allocation(updated_data)(
            *data["model"]["optimizer"]["xstar"]
        )

    if traditional_gender == "f":
        return female_traditional_share
    return male_traditional_share


def make_schooling_of_production_share(
    invariant_solution,
    schooling_gender,
    production_share_gender,
    production_share_index,
):
    """Make a function returning the schooling years for a given production share."""
    data = copy.deepcopy(invariant_solution)
    xtol = 1e-4
    female_eq_cond = model.make_female_schooling_condition(
        data["model"], production_share_index
    )(*data["model"]["optimizer"]["xstar"])
    male_eq_cond = model.make_male_schooling_condition(
        data["model"], production_share_index
    )(*data["model"]["optimizer"]["xstar"])

    def female_schooling_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return fminbound(
            lambda sf: np.abs(
                model.make_female_schooling_condition(
                    data["model"], production_share_index
                )(
                    data["model"]["optimizer"]["xstar"][0],
                    sf,
                    data["model"]["optimizer"]["xstar"][2],
                )
                - female_eq_cond
            ),
            1e-3,
            data["model"]["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    def female_schooling_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return fminbound(
            lambda sf: np.abs(
                model.make_female_schooling_condition(
                    data["model"], production_share_index
                )(
                    data["model"]["optimizer"]["xstar"][0],
                    sf,
                    data["model"]["optimizer"]["xstar"][2],
                )
                - female_eq_cond
            ),
            1e-3,
            data["model"]["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    def male_schooling_of_female(xif_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = xif_ip
        return fminbound(
            lambda sm: np.abs(
                model.make_male_schooling_condition(
                    data["model"], production_share_index
                )(
                    data["model"]["optimizer"]["xstar"][0],
                    data["model"]["optimizer"]["xstar"][1],
                    sm,
                )
                - male_eq_cond
            ),
            1e-3,
            data["model"]["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    def male_schooling_of_male(xim_ip):
        data["model"]["fixed"][f"xi_{production_share_index}"] = 1 - xim_ip
        return fminbound(
            lambda sm: np.abs(
                model.make_male_schooling_condition(
                    data["model"], production_share_index
                )(
                    data["model"]["optimizer"]["xstar"][0],
                    data["model"]["optimizer"]["xstar"][1],
                    sm,
                )
                - male_eq_cond
            ),
            1e-3,
            data["model"]["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    if schooling_gender == "f" and production_share_gender == "f":
        return female_schooling_of_female
    elif schooling_gender == "f" and production_share_gender == "m":
        return female_schooling_of_male
    elif schooling_gender == "m" and production_share_gender == "f":
        return male_schooling_of_female
    return male_schooling_of_male


def make_schooling_of_productivity(
    invariant_solution, schooling_gender, productivity_index
):
    """Make a function returning the schooling years for a given productivity factor."""
    xtol = 1e-4
    female_eq_cond = model.make_female_schooling_condition(
        invariant_solution["model"], productivity_index
    )(*invariant_solution["model"]["optimizer"]["xstar"])
    male_eq_cond = model.make_male_schooling_condition(
        invariant_solution["model"], productivity_index
    )(*invariant_solution["model"]["optimizer"]["xstar"])

    def female_schooling(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return fminbound(
            lambda sf: np.abs(
                model.make_female_schooling_condition(updated_data, productivity_index)(
                    updated_data["optimizer"]["xstar"][0],
                    sf,
                    updated_data["optimizer"]["xstar"][2],
                )
                - female_eq_cond
            ),
            1e-3,
            updated_data["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    def male_schooling(Z_scale):
        data = copy.deepcopy(invariant_solution)
        updated_data = update_data_from_productivity(
            data["model"], productivity_index, Z_scale
        )
        return fminbound(
            lambda sm: np.abs(
                model.make_male_schooling_condition(updated_data, productivity_index)(
                    updated_data["optimizer"]["xstar"][0],
                    updated_data["optimizer"]["xstar"][1],
                    sm,
                )
                - male_eq_cond
            ),
            1e-3,
            updated_data["fixed"]["T"] - 1e-3,
            xtol=xtol,
        )

    if schooling_gender == "f":
        return female_schooling
    return male_schooling


def make_subplot(x, female_fnc, male_fnc, line_label_mask, xlabel, ylabel):
    """Make a subplot from female and male functions."""
    plt.plot(
        x,
        [female_fnc(v) for v in x],
        label=line_label_mask.format(g="f"),
        color=fcolors[0],
        linestyle=flinestyle,
    )
    plt.plot(
        x,
        [male_fnc(v) for v in x],
        label=line_label_mask.format(g="m"),
        color=mcolors[0],
        linestyle=mlinestyle,
    )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)


def make_production_share_figure(invariant_solution):
    """Create partial equilibrium production share figure."""
    data = copy.deepcopy(invariant_solution)
    xi_Sr = data["model"]["fixed"]["xi_Sr"]

    def make_vline():
        plt.axvline(xi_Sr, color="k", linestyle="dashed", alpha=0.5, linewidth=0.5)

    modern_technology_shares = {
        f"{gender}r": make_modern_share_of_production_share(data, gender, "f", "Sr")
        for gender in ["f", "m"]
    }
    traditional_technology_shares = {
        f"{gender}r": make_traditional_share_of_production_share(
            data, gender, "f", "Sr"
        )
        for gender in ["f", "m"]
    }
    female_bill = make_wage_bill_of_production_share(data, "f", "Sr", "f", "Sr")
    male_bill = make_wage_bill_of_production_share(data, "m", "Sr", "f", "Sr")
    leisure_shares = {
        f"{gender}l": make_time_allocation_share_of_production_share(
            data, gender, "l", "f", "Sr"
        )
        for gender in ["f", "m"]
    }
    female_allocation_share = make_time_allocation_share_of_production_share(
        data, "f", "Sr", "f", "Sr"
    )
    male_allocation_share = make_time_allocation_share_of_production_share(
        data, "m", "Sr", "f", "Sr"
    )
    female_schooling = make_schooling_of_production_share(data, "f", "f", "Sr")
    male_schooling = make_schooling_of_production_share(data, "m", "f", "Sr")

    x = np.linspace(0.25, 0.75, 50, endpoint=True)
    xlabel = "$\\xi^{f}_{Sr}$"
    plt.figure()

    plt.subplot(3, 2, 1)
    counter = -1
    for key, fnc in modern_technology_shares.items():
        counter += 1
        gender = key[0]
        variable = "M" if key[1] == "r" else "N"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"${variable}^{{{gender}}}$",
        )
    make_vline()
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Paid Hours Share")

    plt.subplot(3, 2, 2)
    make_vline()
    make_subplot(
        x, female_schooling, male_schooling, "$s^{{{g}}}$", xlabel, "Schooling Years"
    )
    plt.subplot(3, 2, 3)
    counter = -1
    for key, fnc in leisure_shares.items():
        counter += 1
        gender = key[0]
        variable = "M"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"$\\ell^{{{gender}}}$",
        )
    make_vline()
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Leisure Share")

    plt.subplot(3, 2, 4)
    make_vline()
    counter = -1
    for key, fnc in traditional_technology_shares.items():
        counter += 1
        gender = key[0]
        variable = "N"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"${variable}^{{{gender}}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Traditional Hours Share")

    plt.subplot(3, 2, 5)
    make_vline()
    make_subplot(
        x,
        female_allocation_share,
        male_allocation_share,
        "$L^{{{g}}}_{{Sr}}/L^{{{g}}}$",
        xlabel,
        "Labor Share",
    )

    plt.subplot(3, 2, 6)
    make_vline()
    make_subplot(
        x,
        female_bill,
        male_bill,
        "$I^{{{g}}}_{{Sr}}$",
        xlabel,
        "Wage Bill",
    )

    plt.tight_layout()
    results_path = invariant_solution["model"]["config"]["paths"]["results"]
    filename = f"{results_path}/production-share.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_productivity_figure(invariant_solution):
    """Create partial equilibrium productivity figure."""
    data = copy.deepcopy(invariant_solution)

    def make_vline():
        plt.axvline(0.0, color="k", linestyle="dashed", alpha=0.5, linewidth=0.5)

    modern_technology_shares = {
        f"{gender}r": make_modern_share_of_productivity(data, gender, "Sr")
        for gender in ["f", "m"]
    }
    traditional_technology_shares = {
        f"{gender}r": make_traditional_share_of_productivity(data, gender, "Sr")
        for gender in ["f", "m"]
    }
    female_bill = make_wage_bill_of_productivity(data, "f", "Sr", "Sr")
    male_bill = make_wage_bill_of_productivity(data, "m", "Sr", "Sr")
    leisure_shares = {
        f"{gender}l": make_time_allocation_share_of_productivity(
            data, gender, "l", "Sr"
        )
        for gender in ["f", "m"]
    }
    female_allocation_share = make_time_allocation_share_of_productivity(
        data, "f", "Sr", "Sr"
    )
    male_allocation_share = make_time_allocation_share_of_productivity(
        data, "m", "Sr", "Sr"
    )
    female_schooling = make_schooling_of_productivity(data, "f", "Sr")
    male_schooling = make_schooling_of_productivity(data, "m", "Sr")

    xlabel = "$\\Delta Z_{Sr}/Z_{Sr}$"
    x = np.linspace(-0.1, 0.1, 20, endpoint=True)
    plt.figure()

    plt.subplot(3, 2, 1)
    make_vline()
    counter = -1
    for key, fnc in modern_technology_shares.items():
        counter += 1
        gender = key[0]
        variable = "M"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in 1 + x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"${variable}^{{{gender}}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Paid Hours Share")

    plt.subplot(3, 2, 2)
    make_vline()
    make_subplot(
        x,
        lambda v: female_schooling(1 + v),
        lambda v: male_schooling(1 + v),
        "$s^{{{g}}}$",
        xlabel,
        "Schooling Years",
    )

    plt.subplot(3, 2, 3)
    make_vline()
    counter = -1
    for key, fnc in leisure_shares.items():
        counter += 1
        gender = key[0]
        variable = "M" if key[1] == "r" else "N"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in 1 + x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"$\\ell^{{{gender}}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Leisure Share")

    plt.subplot(3, 2, 4)
    make_vline()
    counter = -1
    for key, fnc in traditional_technology_shares.items():
        counter += 1
        gender = key[0]
        variable = "N"
        color = fcolors[0] if gender == "f" else mcolors[0]
        plt.plot(
            x,
            [fnc(v) for v in 1 + x],
            color=color,
            linestyle=glinestyles[gender],
            label=f"${variable}^{{{gender}}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Traditional Hours Share")

    plt.subplot(3, 2, 5)
    make_vline()
    make_subplot(
        x,
        lambda v: female_allocation_share(1 + v),
        lambda v: male_allocation_share(1 + v),
        "$L^{{{g}}}_{{Sr}}/L^{{{g}}}$",
        xlabel,
        "Labor Share",
    )

    plt.subplot(3, 2, 6)
    make_vline()
    make_subplot(
        x,
        lambda v: female_bill(1 + v),
        lambda v: male_bill(1 + v),
        "$I^{{{g}}}_{{Sr}}$",
        xlabel,
        "Wage Bill",
    )

    plt.tight_layout()
    results_path = invariant_solution["model"]["config"]["paths"]["results"]
    filename = f"{results_path}/productivity.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_schooling_figure(invariant_solutions, gender_index):
    """Make a figure comparing schooling predictions with data."""
    solutions = copy.deepcopy(invariant_solutions)
    gender = "female" if gender_index == "f" else "male"
    solver_index = 1 if gender_index == "f" else 2

    plt.figure()
    x = [7.6, 9.1, 10.4]
    data = [
        solution["model"]["config"]["parameters"][f"s{gender_index}"]
        for income_group, solution in solutions.items()
        if income_group != "all"
    ]
    preds = [
        solution["model"]["optimizer"]["xstar"][solver_index]
        for income_group, solution in solutions.items()
        if income_group != "all"
    ]
    plt.plot(x, data, label="Data averages", color=fcolors[0], linestyle=flinestyle)
    plt.plot(
        x, preds, label="Model predictions", color=fcolors[1], linestyle=flinestyle
    )

    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel("log(GDP per capita)")
    plt.ylabel("Years of schooling")

    plt.tight_layout()
    results_path = invariant_solutions["all"]["model"]["config"]["paths"]["results"]
    filename = f"{results_path}/schooling-{gender}-model-vs-data.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_labor_radar_figure(invariant_solution):
    """Make a radar plot of the labor shares."""
    solution = copy.deepcopy(invariant_solution)
    controls = {}
    for technology in model_traits.technology_indices():
        for sector in model_traits.sector_indices():
            index = f"{sector}{technology}"
            Lis = model.make_female_time_allocation_control(solution["model"], index)(
                *solution["model"]["optimizer"]["xstar"]
            )
            controls[f"$L_{{{index}}}$"] = Lis
    controls["$\\ell$"] = model.make_female_time_allocation_control(
        solution["model"], "l"
    )(*solution["model"]["optimizer"]["xstar"])

    income_group = solution["model"]["config"]["group"]
    M = np.max(list(controls.values()) + data_female_labor_shares[income_group])

    plt.figure()
    N = len(controls)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], controls.keys())
    ax.set_rlabel_position(0)
    yticks = [0.25 * M, 0.5 * M, 0.75 * M, M]
    plt.yticks(yticks, [f"{tick:.2}" for tick in yticks], color="grey", size=7)
    plt.ylim(0, M)
    values = list(controls.values())
    values += values[:1]
    ax.plot(angles, values, linewidth=1, linestyle="solid", label="Model")
    ax.fill(angles, values, "b", alpha=0.1)

    values = copy.deepcopy(data_female_labor_shares[income_group])
    values += values[:1]
    ax.plot(angles, values, linewidth=1, linestyle="solid", label="Data")
    ax.fill(angles, values, "r", alpha=0.1)

    plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1)).get_frame().set_alpha(0.0)
    results_path = solution["model"]["config"]["paths"]["results"]
    setup = solution["model"]["config"]["setup"]
    group = solution["model"]["config"]["group"]
    filename = f"{results_path}/radar-{setup}-{group}.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def load_controls(invariant_solution):
    """Calculate Labor controls of the invariant solution and return a copy."""
    solution = copy.deepcopy(invariant_solution)

    controls = {}
    controls["$\\gamma$"] = model.make_subsistence_consumption_share(solution["model"])(
        *solution["model"]["optimizer"]["xstar"]
    )
    controls["$N^{f}$"] = model.make_female_traditional_production_allocation(
        solution["model"]
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$M^{f}$"] = model.make_female_modern_production_allocation(
        solution["model"]
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$\\ell^{f}$"] = model.make_female_time_allocation_control(
        solution["model"], "l"
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$N^{m}$"] = model.make_male_traditional_production_allocation(
        solution["model"]
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$M^{m}$"] = model.make_male_modern_production_allocation(
        solution["model"]
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$\\ell^{m}$"] = model.make_male_time_allocation_control(
        solution["model"], "l"
    )(*solution["model"]["optimizer"]["xstar"])
    controls["$\\tilde w$"] = solution["model"]["optimizer"]["xstar"][0]
    controls["$\\tilde s$"] = (
        solution["model"]["optimizer"]["xstar"][1]
        / solution["model"]["optimizer"]["xstar"][2]
    )
    controls["$\\tilde M$"] = controls["$M^{f}$"] / controls["$M^{m}$"]

    print(f"Controls = {controls}")
    solution["controls"] = controls

    return solution


def make_labor_lollipop_figure(solutions):
    """Make a lollipop plot of the labor and income shares."""
    variables = [
        "$N^{f}$",
        "$M^{f}$",
        "$\\ell^{f}$",
        "$N^{m}$",
        "$M^{m}$",
        "$\\ell^{m}$",
    ]
    controls = {
        group: {control: solution["controls"][control] for control in variables}
        for group, solution in solutions.items()
    }

    labels = functools.reduce(
        lambda l, r: l + [""] + r,
        [list(controls[income_group].keys()) for income_group in income_groups],
    )
    model_values = functools.reduce(
        lambda l, r: l + [None] + r,
        [list(controls[income_group].values()) for income_group in income_groups],
    )
    data_values = functools.reduce(
        lambda l, r: l + [None] + r,
        [
            [
                sum(v[:3]),
                sum(v[3:-1]),
                *v[-1:],
                sum(data_male_labor_shares[k][:3]),
                sum(data_male_labor_shares[k][3:-1]),
                data_male_labor_shares[k][-1],
            ]
            for k, v in data_female_labor_shares.items()
        ],
    )

    plt.figure()
    markerline, stemlines, baseline = plt.stem(
        range(len(labels)),
        model_values,
        markerfmt="bo",
        label="Model",
        use_line_collection=True,
    )
    plt.setp(baseline, visible=False)

    markerline, stemlines, baseline = plt.stem(
        range(len(labels)),
        data_values,
        markerfmt="rx",
        label="Data",
        use_line_collection=True,
    )
    plt.setp(baseline, visible=False)
    plt.setp(stemlines, "color", plt.getp(markerline, "color"))
    plt.setp(stemlines, "linestyle", "dotted")

    plt.xticks(range(len(labels)), labels, rotation="vertical", fontsize=12)
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(
        functools.reduce(
            lambda l, r: l + " " * 25 + r, [ig.capitalize() for ig in income_groups]
        )
    )

    results_path = solutions["all"]["model"]["config"]["paths"]["results"]
    setup = solutions["all"]["model"]["config"]["setup"]
    filename = f"{results_path}/lollipop-{setup}.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_income_and_labor_errors_table(solutions):
    """Make a table of calibration errors between model and the data."""
    variables = ["$\\gamma$", "$M^{f}$", "$\\ell^{f}$", "$M^{m}$", "$\\ell^{m}$"]
    controls = {
        group: {control: solution["controls"][control] for control in variables}
        for group, solution in solutions.items()
    }

    calibration_setup = solutions["all"]["model"]["config"]["setup"]
    output = f"calibration_setup = {calibration_setup}\n"
    names = list(controls["all"].keys())
    output = (
        output
        + f"| {' | '.join([f'{key:10}' for key in ['group', *names, 'abs.sum.']])} |\n"
    )
    for income_group, model_values in controls.items():
        data_values = np.asarray(
            [
                data_subsistence_shares[income_group],
                sum(data_female_labor_shares[income_group][3:-4]),
                data_female_labor_shares[income_group][-4],
                sum(data_male_labor_shares[income_group][3:-4]),
                data_male_labor_shares[income_group][-4],
            ]
        )
        errors = np.asarray([v for v in model_values.values()]) - data_values
        mask = "{:>10.4f}"
        values = [*[mask.format(v) for v in errors], mask.format(sum(np.abs(errors)))]
        output = output + f"| {income_group:10} | {' | '.join(values)} |\n"

    print(output)
    results_path = solutions["all"]["model"]["config"]["paths"]["results"]
    with open(f"{results_path}/labor-errors-{calibration_setup}.org", "w") as f:
        f.write(output)


def make_counterfactual_table(solutions):
    """Make a table of used in counterfactual analysis."""

    def get_income_group_variables(model_data):
        sf = model_data["optimizer"]["xstar"][1]
        sm = model_data["optimizer"]["xstar"][2]
        tw = model_data["optimizer"]["xstar"][0]
        mf = model.make_female_modern_production_allocation(model_data)(
            *model_data["optimizer"]["xstar"]
        )
        mm = model.make_male_modern_production_allocation(model_data)(
            *model_data["optimizer"]["xstar"]
        )
        ts = sf / sm
        tm = mf / mm
        return [sf, sm, ts, tw, tm]

    def relative_difference(x1, x0):
        return ((np.asarray(x1) - np.asarray(x0)) / np.asarray(x0)).tolist()

    income_variables = {
        income_group: get_income_group_variables(solutions[income_group]["model"])
        for income_group in income_groups
        if income_group != "all"
    }
    difference_variables = {
        "middle": relative_difference(
            income_variables["middle"][-3:], income_variables["low"][-3:]
        ),
        "high": relative_difference(
            income_variables["high"][-3:], income_variables["middle"][-3:]
        ),
    }

    ncol = len(income_variables["low"]) + len(difference_variables["middle"]) + 1
    calibration_setup = solutions["all"]["model"]["config"]["setup"]
    output = (
        "\\\\ \\midrule\n\\multicolumn{"
        + str(ncol)
        + "}{c}{\\textbf{\\Cref{calib:"
        + calibration_setup
        + "}: "
        + calibration_setup
        + "}} \\\\ \\midrule\n"
    )

    for row, variables in income_variables.items():
        output = (
            output
            + f"\\textbf{{{row}}} & "
            + " & ".join(["{:>7.4f}".format(value) for value in variables])
        )
        if row == "low":
            output = output + " & & & "
        else:
            output = (
                output
                + " & "
                + " & ".join(
                    ["{:>7.4f}".format(value) for value in difference_variables[row]]
                )
            )
        if row != "high":
            output = output + " \\\\"
        output = output + "\n"

    print(output)
    results_path = solutions["all"]["model"]["config"]["paths"]["results"]
    with open(f"{results_path}/counterfactual-{calibration_setup}.tex", "w") as f:
        f.write(output)


def make_control_income_differences_table(solutions):
    """Make a table of income differences for model controls."""
    variables = ["$\\tilde w$", "$\\tilde M$", "$\\tilde s$"]
    controls = {
        group: {control: solution["controls"][control] for control in variables}
        for group, solution in solutions.items()
    }

    def prc(left, right):
        return "{:>7.2f}\\%".format(100 * (right - left) / left)

    calibration_setup = solutions["all"]["model"]["config"]["setup"]
    output = (
        "\\\\ \\midrule\n\\multicolumn{6}{c}{\\textbf{\\Cref{calib:"
        + calibration_setup
        + "}: "
        + calibration_setup
        + "}} \\\\ \\midrule\n"
    )
    model_values = [
        [
            model_values[variable]
            for income_group, model_values in controls.items()
            if income_group != "all"
        ]
        for variable in variables
    ]
    model_values = [
        [*row, prc(row[0], row[1]), prc(row[1], row[2])] for row in model_values
    ]
    for row, variable in enumerate(variables):
        output = (
            output
            + f"\\textbf{{{variable}}} & "
            + " & ".join(
                [
                    "{:>7.4f}".format(value)
                    for value in model_values[row]
                    if type(value) != str
                ]
            )
            + " & "
            + " & ".join([value for value in model_values[row] if type(value) == str])
        )
        if row != len(variables) - 1:
            output = output + " \\\\"
        output = output + "\n"

    print(output)
    results_path = solutions["all"]["model"]["config"]["paths"]["results"]
    with open(
        f"{results_path}/prediction-differences-{calibration_setup}.tex", "w"
    ) as f:
        f.write(output)


def make_calibration_table(solutions):
    """Make a table of calibration results."""
    calibration_setup = solutions["all"]["model"]["config"]["setup"]
    initializers = {k: v[0] for k, v in solutions["all"]["model"]["free"].items()}
    output = (
        "\\\\ \\midrule\n\\multicolumn{"
        + str(len(initializers) + 4)
        + "}{c}{\\textbf{\\Cref{calib:"
        + calibration_setup
        + "}: "
        + calibration_setup
        + "}} \\\\ \\midrule\n"
    )
    adjusted_initializers = {k: v for k, v in initializers.items() if k != "beta_f"}
    adjusted_initializers["beta_f"] = initializers["beta_f"]

    for income_group, solution in solutions.items():
        mask = "{:>7.4f}"
        values = [
            *[
                mask.format(solution["model"]["free"][key][0])
                for key in adjusted_initializers
            ],
            mask.format(
                solution["model"]["free"]["beta_f"][0]
                / solution["model"]["fixed"]["tbeta"]
            ),
            *[mask.format(x) for x in solution["model"]["optimizer"]["xstar"]],
        ]

        output = output + f"\\textbf{{{income_group}}} & {' & '.join(values)}"
        if income_group != "all":
            output = output + " \\\\"
        output = output + "\n"

    print(output)
    results_path = solutions["all"]["model"]["config"]["paths"]["results"]
    with open(f"{results_path}/calibration-{calibration_setup}.tex", "w") as f:
        f.write(output)


def make_calibration_summary_table(solutions):
    """Print calibration results."""
    table = ""
    for setup, solution in solutions.items():
        variables = [
            *solution["all"]["model"]["free"].keys(),
            "tw",
            "sf",
            "sm",
            "ts",
            "error",
            "status",
        ]
        if "no-subsistence" in setup:
            variables = ["hat_c", *variables]

        table = table + f"calibration_setup = {setup}\n"
        table += f"| group  | {' | '.join([f'{var:7}' for var in variables])} |\n"
        masks = ["{:>7.4f}" for _ in variables]
        for group, data in solution.items():
            values = [
                *data["calibrator"]["results"]["x"],
                *data["model"]["optimizer"]["xstar"],
                data["model"]["optimizer"]["xstar"][1]
                / data["model"]["optimizer"]["xstar"][2],
                data["calibrator"]["results"]["fun"],
                data["calibrator"]["results"]["status"],
            ]
            if "no-subsistence" in setup:
                values = [0, *values]
            values = [masks[k].format(v) for k, v in enumerate(values)]
            table = table + f"| {group:6} | {' | '.join(values)} |\n"

    print(table)
    model_data = list(solutions.values())[0]["all"]["model"]
    results_path = model_data["config"]["paths"]["results"]
    with open(f"{results_path}/calibration-summary.org", "w") as f:
        f.write(table)


def make_calibration_json_file(solutions):
    """Export calibration results to JSON."""
    results = {}
    for setup, solution in solutions.items():
        results[setup] = {}
        for income_group, model_data in solution.items():
            results[setup][income_group] = dict(
                zip(
                    list(model_data["model"]["free"].keys()),
                    model_data["calibrator"]["results"]["x"],
                )
            )

    results_path = list(solutions.values())[0]["all"]["model"]["config"]["paths"][
        "results"
    ]
    with open(f"{results_path}/calibration.json", "w") as fh:
        fh.write(json.dumps(results, indent=2))


def prepare_config(setup, group, timestamp):
    """Prepare a configuration dictionary for the model."""
    print(f"Configuring {setup} from {timestamp}")
    preconfig = config.preconfigure()
    preconfig["setup"] = setup
    preconfig["group"] = group
    preconfig["paths"] = config.replace_path_timestamps(preconfig["paths"], timestamp)
    preconfig["log_path"] = None
    print(preconfig)
    return config.make_config(
        setup=setup,
        group=group,
        parameter_filename=preconfig["parameters"],
        initializers_filename=preconfig["initializers"],
        output_path=preconfig["paths"]["output"],
        results_path=preconfig["paths"]["results"],
        log_path=None,
        adaptive_optimizer_initialization=preconfig[
            "adaptive_optimizer_initialization"
        ],
        verbose=preconfig["verbose"],
    )


if __name__ == "__main__":
    main_solution = {}
    for income_group in income_groups:
        current_config = prepare_config(
            main_calibration_setup, income_group, main_timestamp
        )
        main_solution[income_group] = calibration.calibrate_and_save_or_load(
            current_config
        )
    make_production_share_figure(main_solution[main_income_group])
    make_productivity_figure(main_solution[main_income_group])
    make_schooling_figure(main_solution, "f")
    make_schooling_figure(main_solution, "m")

    calibration_setups = calibration_traits.setups()
    solutions = {}
    for setup, preparation_callback in calibration_setups.items():
        print(f"Loading setup {setup}")
        solutions[setup] = {}
        for income_group in income_groups:
            current_config = prepare_config(setup, income_group, main_timestamp)
            solutions[setup][income_group] = calibration.calibrate_and_save_or_load(
                current_config
            )
            solutions[setup][income_group] = load_controls(
                solutions[setup][income_group]
            )
            make_labor_radar_figure(solutions[setup][income_group])
        make_income_and_labor_errors_table(solutions[setup])
        make_control_income_differences_table(solutions[setup])
        make_calibration_table(solutions[setup])
        make_labor_lollipop_figure(solutions[setup])
        make_counterfactual_table(solutions[setup])
    make_calibration_summary_table(solutions)
    make_calibration_json_file(solutions)
