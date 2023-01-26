"""Calibration mode setup hooks."""


def _remove_income(model_data):
    del model_data["calibrated"]["hat_c"]
    model_data["hooks"]["hat_c"] = lambda x: 0
    return model_data


def _remove_wages(model_data):
    del model_data["calibrator"]["targets"]["tw"]
    return model_data


def _set_income_weight(model_data):
    model_data["calibrator"]["weights"]["gamma"] = 100
    return model_data


def _set_schooling_weight(model_data):
    model_data["calibrator"]["weights"]["sf"] = 1
    model_data["calibrator"]["weights"]["sm"] = 1
    return model_data


def _set_wages_weight(model_data):
    model_data["calibrator"]["weights"]["tw"] = 100
    return model_data


def _prepare_abs_schooling(model_data):
    return _set_schooling_weight(model_data)


def _prepare_abs_schooling_no_subsistence(model_data):
    return _remove_income(model_data)


def _prepare_abs_schooling_no_subsistence_no_wages(model_data):
    model_data = _prepare_abs_schooling_no_subsistence(model_data)
    return _remove_wages(model_data)


def _prepare_abs_schooling_no_subsistence_scl_wages(model_data):
    model_data = _prepare_abs_schooling_no_subsistence(model_data)
    return _set_wages_weight(model_data)


def _prepare_abs_schooling_no_wages(model_data):
    model_data = _prepare_abs_schooling(model_data)
    return _remove_wages(model_data)


def _prepare_abs_schooling_scl_wages(model_data):
    model_data = _prepare_abs_schooling(model_data)
    return _set_wages_weight(model_data)


def _prepare_abs_schooling_scl_wages_scl_income(model_data):
    model_data = _prepare_abs_schooling_scl_wages(model_data)
    return _set_income_weight(model_data)


def _prepare_no_schooling(model_data):
    del model_data["calibrator"]["targets"]["sf"]
    del model_data["calibrator"]["targets"]["sm"]
    return model_data


def _prepare_no_schooling_no_subsistence(model_data):
    model_data = _prepare_no_schooling(model_data)
    return _remove_income(model_data)


def _prepare_no_schooling_no_subsistence_no_wages(model_data):
    model_data = _prepare_no_schooling_no_subsistence(model_data)
    return _remove_wages(model_data)


def _prepare_no_schooling_no_subsistence_scl_wages(model_data):
    model_data = _prepare_no_schooling_no_subsistence(model_data)
    return _set_wages_weight(model_data)


def _prepare_no_schooling_no_wages(model_data):
    model_data = _prepare_no_schooling(model_data)
    return _remove_wages(model_data)


def _prepare_no_schooling_scl_wages(model_data):
    model_data = _prepare_no_schooling(model_data)
    return _set_wages_weight(model_data)


def _prepare_no_schooling_scl_wages_scl_income(model_data):
    model_data = _prepare_no_schooling_scl_wages(model_data)
    return _set_income_weight(model_data)


def _prepare_rel_schooling_no_subsistence(model_data):
    return _remove_income(model_data)


def _prepare_rel_schooling_no_subsistence_no_wages(model_data):
    model_data = _prepare_rel_schooling_no_subsistence(model_data)
    return _remove_wages(model_data)


def _prepare_rel_schooling_no_subsistence_scl_wages(model_data):
    model_data = _prepare_rel_schooling_no_subsistence(model_data)
    return _set_wages_weight(model_data)


def _prepare_rel_schooling_no_wages(model_data):
    return _remove_wages(model_data)


def _prepare_rel_schooling_scl_wages(model_data):
    return _set_wages_weight(model_data)


def _prepare_rel_schooling_scl_wages_scl_income(model_data):
    model_data = _prepare_rel_schooling_scl_wages(model_data)
    return _set_income_weight(model_data)


def mapping():
    """Calibration mode to setup hook mapping."""
    return {
        "abs-schooling": _prepare_abs_schooling,
        "abs-schooling-no-subsistence": _prepare_abs_schooling_no_subsistence,
        "abs-schooling-no-subsistence-no-wages": _prepare_abs_schooling_no_subsistence_no_wages,
        "abs-schooling-no-subsistence-scl-wages": _prepare_abs_schooling_no_subsistence_scl_wages,
        "abs-schooling-no-wages": _prepare_abs_schooling_no_wages,
        "abs-schooling-scl-wages": _prepare_abs_schooling_scl_wages,
        "abs-schooling-scl-wages-scl-income": _prepare_abs_schooling_scl_wages_scl_income,
        "no-schooling": _prepare_no_schooling,
        "no-schooling-no-subsistence": _prepare_no_schooling_no_subsistence,
        "no-schooling-no-subsistence-no-wages": _prepare_no_schooling_no_subsistence_no_wages,
        "no-schooling-no-subsistence-scl-wages": _prepare_no_schooling_no_subsistence_scl_wages,
        "no-schooling-no-wages": _prepare_no_schooling_no_wages,
        "no-schooling-scl-wages": _prepare_no_schooling_scl_wages,
        "no-schooling-scl-wages-scl-income": _prepare_no_schooling_scl_wages_scl_income,
        "rel-schooling": None,
        "rel-schooling-no-subsistence": _prepare_rel_schooling_no_subsistence,
        "rel-schooling-no-subsistence-no-wages": _prepare_rel_schooling_no_subsistence_no_wages,
        "rel-schooling-no-subsistence-scl-wages": _prepare_rel_schooling_no_subsistence_scl_wages,
        "rel-schooling-no-wages": _prepare_rel_schooling_no_wages,
        "rel-schooling-scl-wages": _prepare_rel_schooling_scl_wages,
        "rel-schooling-scl-wages-scl-income": _prepare_rel_schooling_scl_wages_scl_income,
    }
