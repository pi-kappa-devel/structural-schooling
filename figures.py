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
    xpoint = data["fixed"]["xi_Sr"]
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
    filename = "../text/manuscript/fig/production_share.png"
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
    x = np.linspace(np.max((1.2 * xpoint, 0.3)), 35.0 * xpoint, 50, endpoint=True)
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
    filename = "../text/manuscript/fig/productivity.png"
    plt.savefig(filename, dpi=600, transparent=True)
    plt.close()


income_group = "all"
initializers = {
    "hat_c": 5.748493884,
    "varphi": 3.391829732,
    "beta_f": 0.177428715,
    "Z_ArAh": 0.135479539,
    "Z_MrMh": 2.175251708,
    "Z_SrSh": 0.166055022,
    "Z_ArSr": 0.173499618,
    "Z_MrSr": 2.337050273,
}
make_production_share_figure(income_group, initializers)

initial_productivities = {
    "Z_AhSr": 35.49054302,
    "Z_MhSr": 7.461197725,
    "Z_ShSr": 6.734016572,
    "Z_ArSr": 4.299917852,
    "Z_MrSr": 14.51415889,
}
make_production_scale_figure(income_group, initializers, initial_productivities)

# g = np.zeros((6, 6))
# g[0, 3] = g[3, 0] = 1
# g[1, 4] = g[4, 1] = 1
# g[2, 5] = g[5, 2] = 1
# g[3, 5] = g[5, 3] = 1
# g[4, 5] = g[5, 4] = 1
# print(f"g = \n{g}")

# v0 = np.zeros(6)
# v0[0] = 1
# print(f"v0 = {v0}")
# v = v0.copy()
# print(f"v = {v}")

# v1 = np.inner(g, v0)
# print(f"v1 = {v1}")
# v = (v == 1) | (v1 == 1)
# print(f"v = {v}")

# v2 = np.inner(g, v1)
# print(f"v2 = {v2}")
# v = (v == 1) | (v2 == 1)
# print(f"v = {v}")

# v3 = np.inner(g, v2)
# print(f"v3 = {v3}")
# v = (v == 1) | (v3 == 1)
# print(f"v = {v}")

# v4 = np.inner(g, v3)
# print(f"v4 = {v4}")
# v = (v == 1) | (v4 == 1)
# print(f"v = {v}")
