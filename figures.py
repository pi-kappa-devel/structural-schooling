"""
Solver file for Why does the Schooling Gap Close when the Wage Gap Remains Constant?

@authors: Pantelis Karapanagiotis and Paul Reimers
   Version of Model with two types of production technologies (traditional and modern),
   three sectors (agriculture, manufacturing, and services), genders , and schooling.
   Each household consist of a female and a male. Modern production occurs only after
   schooling. Firms choose effective labor units.
"""

import numpy as np
import matplotlib.pyplot as plt
import model
from math import pi
import functools

from importlib import reload

model = reload(model)

hlinestyle = ":"
flinestyle = "-"
mlinestyle = "--"
hcolor = "black"
fcolor = "blue"
mcolor = "orange"
format_strings = ["c-", "g--", "r-.", "k:", "m.-"]
markersize = 4.0

main_income_group = "all"
main_calibration_mode = "abs-schooling-no-wages"

# fmt: off
income_groups = ["low", "middle", "high", "all"]
calibration_modes = [
    "abs-schooling", "abs-schooling-no-wages", "abs-schooling-scl-wages",
    "base",
    "no-schooling", "no-schooling-scl-wages",
    "no-wages", # "no-income-no-wages",
]

initializer_names = [
    "hat_c", "varphi",
    "beta_f",
    "Z_ArAh", "Z_MrMh", "Z_SrSh", "Z_ArSr", "Z_MrSr",
]

data_female_labor_shares = {
  "low": [0.0815877, 0.0062807, 0.2938025, 0.0215187, 0.0126192, 0.0363058, 0.5478855],
  "middle": [0.0281231, 0.0037166, 0.2975294, 0.0047409, 0.0191781, 0.0787491, 0.5679629],
  "high": [0.0042724, 0.0009837, 0.2389524, 0.0023376, 0.0223466, 0.1015646, 0.6295427],
  "all": [0.0379944, 0.003660333, 0.276761433, 0.0095324, 0.018047967, 0.0722065, 0.581797033]
}
data_male_labor_shares = {
    "low": [0.0899835, 0.0075116, 0.1265374, 0.0434648, 0.0262223, 0.0810602, 0.6252202],
    "middle": [0.0446018, 0.0058335, 0.1007717, 0.0289257, 0.0493341, 0.1208478, 0.6496854],
    "high": [0.0076562, 0.0060439, 0.0976458, 0.0078905, 0.0785629, 0.1149185, 0.6872821],
    "all": [0.047413833, 0.006463, 0.1083183, 0.026760333, 0.0513731, 0.105608833, 0.654062567]
}
data_subsistence_shares = { "low": 0.23, "middle": 0.06, "high": 0.02, "all": 0.1033 }
# fmt: on


def make_relative_expenditure_of_share(income_group, initializers, gender, over, under):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    def relative_expenditure_of_female(xif_under):
        data["fixed"][f"xi_{under}"] = xif_under
        return model.make_relative_consumption_expenditure(data, over, under)(
            *data["optimizer"]["x0"]
        )

    def relative_expenditure_of_male(xim_under):
        data["fixed"][f"xi_{under}"] = 1 - xim_under
        return model.make_relative_consumption_expenditure(data, over, under)(
            *data["optimizer"]["x0"]
        )

    return (
        relative_expenditure_of_female
        if gender == "f"
        else relative_expenditure_of_male
    )


def make_relative_expenditure_of_productivity(
    income_group, initializers, gender, over, under, initial_productivities
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    for k, v in initial_productivities.items():
        data["calibrated"][k] = [v, (1e-3, None)]

    def update_data(data, Z_under):
        for sector in data["sectors"]:
            for technology in data["technologies"]:
                if f"{sector}{technology}" != under:
                    data["calibrated"][f"Z_{sector}{technology}{under}"] = [
                        initial_productivities[f"Z_{sector}{technology}{under}"]
                        / Z_under,
                        (1e-3, None),
                    ]
                    data["calibrated"][f"Z_{under}{sector}{technology}"] = [
                        1 / data["calibrated"][f"Z_{sector}{technology}{under}"][0],
                        (1e-3, None),
                    ]
        return data

    def relative_expenditure_of_female(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_relative_consumption_expenditure(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    def relative_expenditure_of_male(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_relative_consumption_expenditure(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    return (
        relative_expenditure_of_female
        if gender == "f"
        else relative_expenditure_of_male
    )


def make_wage_bill_of_share(
    income_group, initializers, bill_gender, share_gender, indices
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    def female_wage_bill_of_female(xif_indices):
        data["fixed"][f"xi_{indices}"] = xif_indices
        return model.make_female_wage_bill(data, indices)(*data["optimizer"]["x0"])

    def female_wage_bill_of_male(xim_indices):
        data["fixed"][f"xi_{indices}"] = 1 - xim_indices
        return model.make_female_wage_bill(data, indices)(*data["optimizer"]["x0"])

    def male_wage_bill_of_female(xif_indices):
        data["fixed"][f"xi_{indices}"] = xif_indices
        return model.make_male_wage_bill(data, indices)(*data["optimizer"]["x0"])

    def male_wage_bill_of_male(xim_indices):
        data["fixed"][f"xi_{indices}"] = 1 - xim_indices
        return model.make_male_wage_bill(data, indices)(*data["optimizer"]["x0"])

    if bill_gender == "f" and share_gender == "f":
        return female_wage_bill_of_female
    elif bill_gender == "f" and share_gender == "m":
        return female_wage_bill_of_male
    elif bill_gender == "m" and share_gender == "f":
        return male_wage_bill_of_female
    return male_wage_bill_of_male


def make_wage_bill_of_productivity(income_group, initializers, bill_gender, indices):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    def female_wage_bill(_):
        return model.make_female_wage_bill(data, indices)(*data["optimizer"]["x0"])

    def male_wage_bill(_):
        return model.make_male_wage_bill(data, indices)(*data["optimizer"]["x0"])

    if bill_gender == "f":
        return female_wage_bill
    return male_wage_bill


def make_time_allocation_ratio_of_share(
    income_group, initializers, bill_gender, share_gender, over, under
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    def female_flow_time_allocation_ratio_of_female(xif_under):
        data["fixed"][f"xi_{under}"] = xif_under
        return model.make_female_flow_time_allocation_ratio(data, over, under)(
            *data["optimizer"]["x0"]
        )

    def female_flow_time_allocation_ratio_of_male(xim_under):
        data["fixed"][f"xi_{under}"] = 1 - xim_under
        return model.make_female_flow_time_allocation_ratio(data, over, under)(
            *data["optimizer"]["x0"]
        )

    def male_flow_time_allocation_ratio_of_female(xif_under):
        data["fixed"][f"xi_{under}"] = xif_under
        return model.make_male_flow_time_allocation_ratio(data, over, under)(
            *data["optimizer"]["x0"]
        )

    def male_flow_time_allocation_ratio_of_male(xim_under):
        data["fixed"][f"xi_{under}"] = 1 - xim_under
        return model.make_male_flow_time_allocation_ratio(data, over, under)(
            *data["optimizer"]["x0"]
        )

    if bill_gender == "f" and share_gender == "f":
        return female_flow_time_allocation_ratio_of_female
    elif bill_gender == "f" and share_gender == "m":
        return female_flow_time_allocation_ratio_of_male
    elif bill_gender == "m" and share_gender == "f":
        return male_flow_time_allocation_ratio_of_female
    return male_flow_time_allocation_ratio_of_male


def make_time_allocation_ratio_of_productivity(
    income_group,
    initializers,
    bill_gender,
    share_gender,
    over,
    under,
    initial_productivities,
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    for k, v in initial_productivities.items():
        data["calibrated"][k] = [v, (1e-3, None)]

    def update_data(data, Z_under):
        for sector in data["sectors"]:
            for technology in data["technologies"]:
                if f"{sector}{technology}" != under:
                    data["calibrated"][f"Z_{sector}{technology}{under}"] = [
                        initial_productivities[f"Z_{sector}{technology}{under}"]
                        / Z_under,
                        (1e-3, None),
                    ]
                    data["calibrated"][f"Z_{under}{sector}{technology}"] = [
                        1 / data["calibrated"][f"Z_{sector}{technology}{under}"][0],
                        (1e-3, None),
                    ]
        return data

    def female_flow_time_allocation_ratio_of_female(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_female_flow_time_allocation_ratio(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    def female_flow_time_allocation_ratio_of_male(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_female_flow_time_allocation_ratio(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    def male_flow_time_allocation_ratio_of_female(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_male_flow_time_allocation_ratio(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    def male_flow_time_allocation_ratio_of_male(Z_under):
        updated_data = update_data(data, Z_under)
        return model.make_male_flow_time_allocation_ratio(updated_data, over, under)(
            *data["optimizer"]["x0"]
        )

    if bill_gender == "f" and share_gender == "f":
        return female_flow_time_allocation_ratio_of_female
    elif bill_gender == "f" and share_gender == "m":
        return female_flow_time_allocation_ratio_of_male
    elif bill_gender == "m" and share_gender == "f":
        return male_flow_time_allocation_ratio_of_female
    return male_flow_time_allocation_ratio_of_male


def make_time_allocation_share_of_share(
    income_group, initializers, bill_gender, share_gender, indices
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    def female_time_allocation_share_of_female(xif_indices):
        data["fixed"][f"xi_{indices}"] = xif_indices
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            data, indices
        )(*data["optimizer"]["x0"])

    def female_time_allocation_share_of_male(xim_indices):
        data["fixed"][f"xi_{indices}"] = 1 - xim_indices
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            data, indices
        )(*data["optimizer"]["x0"])

    def male_time_allocation_share_of_female(xif_indices):
        data["fixed"][f"xi_{indices}"] = xif_indices
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(data, indices)(
            *data["optimizer"]["x0"]
        )

    def male_time_allocation_share_of_male(xim_indices):
        data["fixed"][f"xi_{indices}"] = 1 - xim_indices
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(data, indices)(
            *data["optimizer"]["x0"]
        )

    if bill_gender == "f" and share_gender == "f":
        return female_time_allocation_share_of_female
    elif bill_gender == "f" and share_gender == "m":
        return female_time_allocation_share_of_male
    elif bill_gender == "m" and share_gender == "f":
        return male_time_allocation_share_of_female
    return male_time_allocation_share_of_male


def make_time_allocation_share_of_productivity(
    income_group, initializers, bill_gender, share_gender, under, initial_productivities
):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)

    for k, v in initial_productivities.items():
        data["calibrated"][k] = [v, (1e-3, None)]

    def update_data(data, Z_under):
        for sector in data["sectors"]:
            for technology in data["technologies"]:
                if f"{sector}{technology}" != under:
                    data["calibrated"][f"Z_{sector}{technology}{under}"] = [
                        initial_productivities[f"Z_{sector}{technology}{under}"]
                        / Z_under,
                        (1e-3, None),
                    ]
                    data["calibrated"][f"Z_{under}{sector}{technology}"] = [
                        1 / data["calibrated"][f"Z_{sector}{technology}{under}"][0],
                        (1e-3, None),
                    ]
        return data

    def female_time_allocation_share_of_female(Z_under):
        updated_data = update_data(data, Z_under)
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            updated_data, under
        )(*data["optimizer"]["x0"])

    def female_time_allocation_share_of_male(Z_under):
        updated_data = update_data(data, Z_under)
        return 1 / model.make_aggregate_female_flow_time_allocation_ratio(
            updated_data, under
        )(*data["optimizer"]["x0"])

    def male_time_allocation_share_of_female(Z_under):
        updated_data = update_data(data, Z_under)
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(
            updated_data, under
        )(*data["optimizer"]["x0"])

    def male_time_allocation_share_of_male(Z_under):
        updated_data = update_data(data, Z_under)
        return 1 / model.make_aggregate_male_flow_time_allocation_ratio(
            updated_data, under
        )(*data["optimizer"]["x0"])

    if bill_gender == "f" and share_gender == "f":
        return female_time_allocation_share_of_female
    elif bill_gender == "f" and share_gender == "m":
        return female_time_allocation_share_of_male
    elif bill_gender == "m" and share_gender == "f":
        return male_time_allocation_share_of_female
    return male_time_allocation_share_of_male


def add_point(fnc, xpoint, xshift=-0.05, yshift=0.2):
    plt.plot(xpoint, fnc(xpoint), color="black", marker=".")
    x0, x1 = plt.gca().get_xlim()
    y0, y1 = plt.gca().get_ylim()
    xscale = 1 + xshift * np.abs(x0 - x1)
    ypoint = fnc(xpoint)
    yscale = 1 + yshift * np.abs(y0 - y1)
    plt.plot(xpoint, ypoint, color="black", marker=".")
    plt.text(xpoint * xscale, ypoint * yscale, "$\\mathrm{E}^{\\ast}$")


def make_share_subplot(
    x,
    female_fnc,
    male_fnc,
    line_label_mask,
    xlabel,
    ylabel,
    xpoint=None,
    xshift=-0.05,
    yshift=0.2,
):
    plt.plot(
        x,
        [female_fnc(v) for v in x],
        label=line_label_mask.format(g="f"),
        color=fcolor,
        linestyle=flinestyle,
    )
    plt.plot(
        x,
        [male_fnc(v) for v in x],
        label=line_label_mask.format(g="m"),
        color=mcolor,
        linestyle=mlinestyle,
    )
    if xpoint:
        add_point(female_fnc, xpoint, xshift, yshift)
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)


def make_production_share_figure(income_group, initializers):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)
    x = data["optimizer"]["x0"]

    data["fixed"]["xi_Ah"] = 0.419419992
    data["fixed"]["xi_Mh"] = 0.382713516
    data["fixed"]["xi_Sh"] = 0.546282935
    data["fixed"]["xi_Ar"] = 0.335745272
    data["fixed"]["xi_Mr"] = 0.334385185
    data["fixed"]["xi_Sr"] = 0.402494299
    data["fixed"]["xi_l"] = 0.430658171

    relative_expenditures = {
        f"{sector}{technology}": make_relative_expenditure_of_share(
            income_group, initializers, "f", f"{sector}{technology}", "Sr"
        )
        for sector in data["sectors"]
        for technology in data["technologies"]
        if f"{sector}{technology}" not in ["Sr"]
    }
    female_bill = make_wage_bill_of_share(income_group, initializers, "f", "f", "Sr")
    male_bill = make_wage_bill_of_share(income_group, initializers, "m", "f", "Sr")
    female_allocation_ratio = make_time_allocation_ratio_of_share(
        income_group, initializers, "f", "f", "Ar", "Sr"
    )
    male_allocation_ratio = make_time_allocation_ratio_of_share(
        income_group, initializers, "m", "f", "Ar", "Sr"
    )
    female_allocation_share = make_time_allocation_share_of_share(
        income_group, initializers, "f", "f", "Sr"
    )
    male_allocation_share = make_time_allocation_share_of_share(
        income_group, initializers, "m", "f", "Sr"
    )

    x = np.linspace(0.15, 0.8, 50, endpoint=True)
    xlabel = "$\\xi^{f}_{Sr}$"
    plt.figure()
    linestyles = dict(zip(relative_expenditures.keys(), format_strings))

    plt.subplot(2, 2, 1)
    for key, fnc in relative_expenditures.items():
        plt.plot(
            x,
            [fnc(v) for v in x],
            linestyles[key],
            markersize=markersize,
            label=f"$E_{{{key}Sr}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Relative Expenditure")

    plt.subplot(2, 2, 2)
    make_share_subplot(
        x, female_bill, male_bill, "$I^{{{g}}}_{{Sr}}$", xlabel, "Wage Bill Share"
    )

    plt.subplot(2, 2, 3)
    make_share_subplot(
        x,
        female_allocation_ratio,
        male_allocation_ratio,
        "$R^{{{g}}}_{{ArSr}}$",
        xlabel,
        "Allocation Ratio",
    )

    plt.subplot(2, 2, 4)
    make_share_subplot(
        x,
        female_allocation_share,
        male_allocation_share,
        "$L^{{{g}}}_{{Sr}}/L^{{{g}}}$",
        xlabel,
        "Labor Share",
        xshift=0.1,
        yshift=-0.05,
    )

    plt.tight_layout()
    filename = "../tmp/production-share.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_production_scale_figure(income_group, initializers, initial_productivities):
    data = model.make_model_data(income_group)
    data = model.set_calibrated_data(data, initializers)
    x = data["optimizer"]["x0"]

    relative_expenditures = {
        f"{sector}{technology}": make_relative_expenditure_of_productivity(
            income_group,
            initializers,
            "f",
            f"{sector}{technology}",
            "Sr",
            initial_productivities,
        )
        for sector in data["sectors"]
        for technology in data["technologies"]
        if f"{sector}{technology}" not in ["Sr"]
    }
    female_bill = make_wage_bill_of_productivity(income_group, initializers, "f", "Sr")
    male_bill = make_wage_bill_of_productivity(income_group, initializers, "m", "Sr")
    female_allocation_ratios = {
        f"{sector}{technology}": make_time_allocation_ratio_of_productivity(
            income_group,
            initializers,
            "f",
            "f",
            f"{sector}{technology}",
            "Sr",
            initial_productivities,
        )
        for sector in data["sectors"]
        for technology in data["technologies"]
        if f"{sector}{technology}" not in ["Sr"]
    }
    female_allocation_share = make_time_allocation_share_of_productivity(
        income_group, initializers, "f", "f", "Sr", initial_productivities
    )
    male_allocation_share = make_time_allocation_share_of_productivity(
        income_group, initializers, "m", "f", "Sr", initial_productivities
    )

    xlabel = "$Z_{Sr}$"
    xpoint = np.max(
        [
            data["calibrated"][f"Z_{index}Sr"][0]
            for index in relative_expenditures.keys()
            if f"Z_{index}Sr" in data["calibrated"].keys()
        ]
    )
    x = np.linspace(np.max((0.9 * xpoint, 0.3)), 5.0 * xpoint, 50, endpoint=True)
    plt.figure()
    linestyles = dict(zip(relative_expenditures.keys(), format_strings))

    plt.subplot(2, 2, 1)
    for key, fnc in relative_expenditures.items():
        plt.plot(
            x,
            [fnc(v) for v in x],
            linestyles[key],
            markersize=markersize,
            label=f"$E_{{{key}Sr}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Relative Expenditure")

    plt.subplot(2, 2, 2)
    make_share_subplot(
        x, female_bill, male_bill, "$I^{{{g}}}_{{Sr}}$", xlabel, "Wage Bill Share"
    )

    plt.subplot(2, 2, 3)
    for key, fnc in female_allocation_ratios.items():
        plt.plot(
            x,
            [fnc(v) for v in x],
            linestyles[key],
            markersize=markersize,
            label=f"$R^{{f}}_{{{key}Sr}}$",
        )
    plt.legend().get_frame().set_alpha(0.0)
    plt.xlabel(xlabel)
    plt.ylabel("Allocation Ratio")

    plt.subplot(2, 2, 4)
    make_share_subplot(
        x,
        female_allocation_share,
        male_allocation_share,
        "$L^{{{g}}}_{{Sr}}/L^{{{g}}}$",
        xlabel,
        "Labor Share",
        xshift=0.1,
        yshift=-0.05,
    )

    plt.tight_layout()
    filename = "../tmp/productivity.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_labor_radar_figure(calibration_mode, income_group, initializers):
    filename = f"../data/out/{calibration_mode}/{income_group}-income-calibration.pkl"
    solution = model.get_calibrated_model_solution(
        income_group, filename, initializers.keys()
    )

    controls = {}
    for technology in solution["technologies"]:
        for sector in solution["sectors"]:
            index = f"{sector}{technology}"
            Lis = model.make_female_time_allocation_control(solution, index)(
                *solution["optimizer"]["x0"]
            )
            controls[f"$L_{{{index}}}$"] = Lis
    controls["$\\ell$"] = model.make_female_time_allocation_control(solution, "l")(
        *solution["optimizer"]["x0"]
    )

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

    values = data_female_labor_shares[income_group].copy()
    values += values[:1]
    ax.plot(angles, values, linewidth=1, linestyle="solid", label="Data")
    ax.fill(angles, values, "r", alpha=0.1)

    plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1)).get_frame().set_alpha(0.0)
    filename = f"../tmp/radar-{calibration_mode}-{income_group}.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def load_income_and_labor_controls(calibration_mode, initializers):
    controls = {}
    for income_group in income_groups:
        controls[income_group] = {}
        filename = (
            f"../data/out/{calibration_mode}/{income_group}-income-calibration.pkl"
        )
        solution = model.get_calibrated_model_solution(
            income_group, filename, initializers.keys()
        )

        controls[income_group]["$\\gamma$"] = model.make_subsistence_consumption_share(
            solution
        )(*solution["optimizer"]["x0"])
        controls[income_group][
            "$M^{{f}}$"
        ] = 1 - model.make_female_time_allocation_control(solution, "l")(
            *solution["optimizer"]["x0"]
        )
        controls[income_group][
            "$\\ell^{{f}}$"
        ] = model.make_female_time_allocation_control(solution, "l")(
            *solution["optimizer"]["x0"]
        )
        controls[income_group][
            "$M^{{m}}$"
        ] = 1 - model.make_male_time_allocation_control(solution, "l")(
            *solution["optimizer"]["x0"]
        )
        controls[income_group][
            "$\\ell^{{m}}$"
        ] = model.make_male_time_allocation_control(solution, "l")(
            *solution["optimizer"]["x0"]
        )

    return controls


def make_income_and_labor_lollipop_figure(calibration_mode, initializers):
    controls = load_income_and_labor_controls(calibration_mode, initializers)

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
                data_subsistence_shares[k],
                sum(v[:-1]),
                *v[-1:],
                sum(data_male_labor_shares[k][:-1]),
                data_male_labor_shares[k][-1],
            ]
            for k, v in data_female_labor_shares.items()
        ],
    )

    plt.figure()
    markerline, stemlines, baseline = plt.stem(
        range(len(labels)), model_values, markerfmt="bo", label="Model"
    )
    plt.setp(baseline, visible=False)

    markerline, stemlines, baseline = plt.stem(
        range(len(labels)), data_values, markerfmt="rx", label="Data"
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

    filename = f"../tmp/lollipop-{calibration_mode}.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


def make_income_and_labor_errors_table(calibration_mode, initializers):
    controls = load_income_and_labor_controls(calibration_mode, initializers)

    output = f"calibration_mode = {calibration_mode}\n"
    names = list(controls["all"].keys())
    output = output + f"| group  | {' | '.join([f'{key:7}' for key in names])} | abs. sum |\n"
    for income_group, model_values in controls.items():
        data_values = np.asarray(
            [
                data_subsistence_shares[income_group],
                sum(data_female_labor_shares[income_group][:-1]),
                data_female_labor_shares[income_group][-1],
                sum(data_male_labor_shares[income_group][:-1]),
                data_male_labor_shares[income_group][-1],
            ]
        )
        errors = np.asarray([v for v in model_values.values()]) - data_values
        mask = f"{{:>7.4f}}"
        values = [*[mask.format(v) for v in errors], mask.format(sum(np.abs(errors)))]
        output = output + f"| {income_group:6} | {' | '.join(values)} |\n"

    print(output)
    with open(f"../tmp/labor_errors_{calibration_mode}.org", 'w') as f:
        f.write(output)


filename = (
    f"../data/out/{main_calibration_mode}/{main_income_group}-income-calibration.pkl"
)
solution = model.get_calibrated_model_solution(
    main_income_group, filename, initializer_names
)
initializers = {k: v[0] for k, v in solution["calibrated"].items()}


for calibration_mode in calibration_modes:
    print(f"calibration_mode = {calibration_mode}")
    for income_group in income_groups:
        print(f"income_group = {income_group}")
        make_labor_radar_figure(calibration_mode, income_group, initializers)
    make_income_and_labor_errors_table(calibration_mode, initializers)
    make_income_and_labor_lollipop_figure(calibration_mode, initializers)

make_production_share_figure(main_income_group, initializers)

initial_productivities = {
    "Z_AhSr": 35.49054302,
    "Z_MhSr": 7.461197725,
    "Z_ShSr": 6.734016572,
    "Z_ArSr": 4.299917852,
    "Z_MrSr": 14.51415889,
}
make_production_scale_figure(main_income_group, initializers, initial_productivities)
