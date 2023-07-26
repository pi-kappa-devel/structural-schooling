"""Calibration traits file."""


import model


def make_time_allocation_target(data, gender, index):
    """Make time allocation data and prediction target functions."""

    def target():
        return data["model"]["config"]["parameters"][f"L{gender}_{index}"]

    if gender == "f":

        def prediction(d, tw, sf, sm):
            return model.make_female_time_allocation_control(d["model"], index)(
                tw, sf, sm
            )

    else:

        def prediction(d, tw, sf, sm):
            return model.make_male_time_allocation_control(d["model"], index)(
                tw, sf, sm
            )

    return [target, prediction]


def make_within_gender_time_allocation_ratio_target(data, gender, over, under):
    """Make time allocation ratios data and prediction target functions."""

    def target():
        return (
            data["model"]["config"]["parameters"][f"L{gender}_{over}"]
            / data["model"]["config"]["parameters"][f"L{gender}_{under}"]
        )

    if gender == "f":

        def prediction(d, tw, sf, sm):
            return model.make_female_time_allocation_control(d["model"], over)(
                tw, sf, sm
            ) / model.make_female_time_allocation_control(d["model"], under)(tw, sf, sm)

    else:

        def prediction(d, tw, sf, sm):
            return model.make_male_time_allocation_control(d["model"], over)(
                tw, sf, sm
            ) / model.make_male_time_allocation_control(d["model"], under)(tw, sf, sm)

    return [target, prediction]


def make_schooling_target(data, gender):
    """Make schooling data and prediction target functions."""

    def target():
        return (
            data["model"]["config"]["parameters"][f"s{gender}"]
            * data["calibrator"]["weights"][f"s{gender}"]
        )

    if gender == "f":

        def prediction(d, tw, sf, sm):
            return sf * data["calibrator"]["weights"]["sf"]

    else:

        def prediction(d, tw, sf, sm):
            return sm * data["calibrator"]["weights"]["sm"]

    return [target, prediction]


def make_wage_ratio_target(data):
    """Make schooling data and prediction target functions."""

    def target():
        return (
            data["model"]["config"]["parameters"]["tw"]
            * data["calibrator"]["weights"]["tw"]
        )

    def prediction(d, tw, sf, sm):
        return tw * data["calibrator"]["weights"]["tw"]

    return [target, prediction]


def make_subsistence_share_target(data):
    """Make subsistence share data and prediction target functions."""

    def target():
        return (
            data["model"]["config"]["parameters"]["gamma"]
            * data["calibrator"]["weights"]["gamma"]
        )

    def prediction(d, tw, sf, sm):
        return (
            model.make_subsistence_consumption_share(d["model"])(tw, sf, sm)
            * data["calibrator"]["weights"]["gamma"]
        )

    return [target, prediction]


def _remove_subsistence(data):
    del data["model"]["free"]["hat_c"]
    data["model"]["hooks"]["hat_c"] = lambda x: 0
    return data


def _remove_wages(data):
    del data["calibrator"]["targets"]["tw"]
    return data


def _set_subsistence_weight(data):
    data["calibrator"]["weights"]["gamma"] = 100
    return data


def _set_schooling_weight(data):
    data["calibrator"]["weights"]["sf"] = 1
    data["calibrator"]["weights"]["sm"] = 1
    return data


def _set_wages_weight(data):
    data["calibrator"]["weights"]["tw"] = 100
    return data


def _set_no_modern_service_share_heterogeneity(data):
    data["model"]["fixed"]["xi_Sr"] = 0.5
    return data


def _set_low_income_shares(data):
    data["model"]["fixed"]["xi_Ah"] = 0.4222009770484617
    data["model"]["fixed"]["xi_Mh"] = 0.41351920932976727
    data["model"]["fixed"]["xi_Sh"] = 0.5251019307659601
    data["model"]["fixed"]["xi_Ar"] = 0.35886350218684315
    data["model"]["fixed"]["xi_Mr"] = 0.35599394768067955
    data["model"]["fixed"]["xi_Sr"] = 0.3487734856125632
    data["model"]["fixed"]["xi_l"] = 0.4185418363758875
    return data


def _prepare_abs_schooling(data):
    return _set_schooling_weight(data)


def _prepare_abs_schooling_no_modern_service_share_heterogeneity(data):
    data = _prepare_abs_schooling(data)
    return _set_no_modern_service_share_heterogeneity(data)


def _prepare_abs_schooling_no_subsistence(data):
    data = _prepare_abs_schooling(data)
    return _remove_subsistence(data)


def _prepare_abs_schooling_no_subsistence_no_wages(data):
    data = _prepare_abs_schooling_no_subsistence(data)
    return _remove_wages(data)


def _prepare_abs_schooling_no_subsistence_scl_wages(data):
    data = _prepare_abs_schooling_no_subsistence(data)
    return _set_wages_weight(data)


def _prepare_abs_schooling_no_wages(data):
    data = _prepare_abs_schooling(data)
    return _remove_wages(data)


def _prepare_abs_schooling_scl_wages(data):
    data = _prepare_abs_schooling(data)
    return _set_wages_weight(data)


def _prepare_abs_schooling_scl_subsistence_scl_wages(data):
    data = _prepare_abs_schooling_scl_wages(data)
    return _set_subsistence_weight(data)


def _prepare_abs_schooling_with_low_income_shares(data):
    data = _prepare_abs_schooling(data)
    return _set_low_income_shares(data)


def _prepare_no_schooling(data):
    del data["calibrator"]["targets"]["sf"]
    del data["calibrator"]["targets"]["sm"]
    return data


def _prepare_no_schooling_no_modern_service_share_heterogeneity(data):
    data = _prepare_no_schooling(data)
    return _set_no_modern_service_share_heterogeneity(data)


def _prepare_no_schooling_no_subsistence(data):
    data = _prepare_no_schooling(data)
    return _remove_subsistence(data)


def _prepare_no_schooling_no_subsistence_no_wages(data):
    data = _prepare_no_schooling_no_subsistence(data)
    return _remove_wages(data)


def _prepare_no_schooling_no_subsistence_scl_wages(data):
    data = _prepare_no_schooling_no_subsistence(data)
    return _set_wages_weight(data)


def _prepare_no_schooling_no_wages(data):
    data = _prepare_no_schooling(data)
    return _remove_wages(data)


def _prepare_no_schooling_scl_wages(data):
    data = _prepare_no_schooling(data)
    return _set_wages_weight(data)


def _prepare_no_schooling_scl_subsistence_scl_wages(data):
    data = _prepare_no_schooling_scl_wages(data)
    return _set_subsistence_weight(data)


def _prepare_no_schooling_with_low_income_shares(data):
    data = _prepare_no_schooling(data)
    return _set_low_income_shares(data)


def _prepare_rel_schooling_no_modern_service_share_heterogeneity(data):
    return _set_no_modern_service_share_heterogeneity(data)


def _prepare_rel_schooling_no_subsistence(data):
    return _remove_subsistence(data)


def _prepare_rel_schooling_no_subsistence_no_wages(data):
    data = _prepare_rel_schooling_no_subsistence(data)
    return _remove_wages(data)


def _prepare_rel_schooling_no_subsistence_scl_wages(data):
    data = _prepare_rel_schooling_no_subsistence(data)
    return _set_wages_weight(data)


def _prepare_rel_schooling_no_wages(data):
    return _remove_wages(data)


def _prepare_rel_schooling_scl_wages(data):
    return _set_wages_weight(data)


def _prepare_rel_schooling_scl_subsistence_scl_wages(data):
    data = _prepare_rel_schooling_scl_wages(data)
    return _set_subsistence_weight(data)


def _prepare_rel_schooling_with_low_income_shares(data):
    return _set_low_income_shares(data)


def setups():
    """Calibration setup hook mapping."""
    return {
        "abs-schooling": _prepare_abs_schooling,
        "abs-schooling-no-modern-service-share-heterogeneity": _prepare_abs_schooling_no_modern_service_share_heterogeneity,
        "abs-schooling-no-subsistence": _prepare_abs_schooling_no_subsistence,
        "abs-schooling-no-subsistence-no-wages": _prepare_abs_schooling_no_subsistence_no_wages,
        "abs-schooling-no-subsistence-scl-wages": _prepare_abs_schooling_no_subsistence_scl_wages,
        "abs-schooling-no-wages": _prepare_abs_schooling_no_wages,
        "abs-schooling-scl-subsistence-scl-wages": _prepare_abs_schooling_scl_subsistence_scl_wages,
        "abs-schooling-scl-wages": _prepare_abs_schooling_scl_wages,
        "abs-schooling-with-low-income-shares": _prepare_abs_schooling_with_low_income_shares,
        "no-schooling": _prepare_no_schooling,
        "no-schooling-no-modern-service-share-heterogeneity": _prepare_no_schooling_no_modern_service_share_heterogeneity,
        "no-schooling-no-subsistence": _prepare_no_schooling_no_subsistence,
        "no-schooling-no-subsistence-no-wages": _prepare_no_schooling_no_subsistence_no_wages,
        "no-schooling-no-subsistence-scl-wages": _prepare_no_schooling_no_subsistence_scl_wages,
        "no-schooling-no-wages": _prepare_no_schooling_no_wages,
        "no-schooling-scl-subsistence-scl-wages": _prepare_no_schooling_scl_subsistence_scl_wages,
        "no-schooling-scl-wages": _prepare_no_schooling_scl_wages,
        "no-schooling-with-low-income-shares": _prepare_no_schooling_with_low_income_shares,
        "rel-schooling": lambda x: x,
        "rel-schooling-no-modern-service-share-heterogeneity": _prepare_rel_schooling_no_modern_service_share_heterogeneity,
        "rel-schooling-no-subsistence": _prepare_rel_schooling_no_subsistence,
        "rel-schooling-no-subsistence-no-wages": _prepare_rel_schooling_no_subsistence_no_wages,
        "rel-schooling-no-subsistence-scl-wages": _prepare_rel_schooling_no_subsistence_scl_wages,
        "rel-schooling-no-wages": _prepare_rel_schooling_no_wages,
        "rel-schooling-scl-subsistence-scl-wages": _prepare_rel_schooling_scl_subsistence_scl_wages,
        "rel-schooling-scl-wages": _prepare_rel_schooling_scl_wages,
        "rel-schooling-with-low-income-shares": _prepare_rel_schooling_with_low_income_shares,
    }
