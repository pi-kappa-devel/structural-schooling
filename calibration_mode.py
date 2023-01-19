def prepare_abs_schooling_scl_wages_scl_income(model_data):
    model_data["calibrator"]["weights"]["sf"] = 1
    model_data["calibrator"]["weights"]["sm"] = 1
    model_data["calibrator"]["weights"]["tw"] = 100
    model_data["calibrator"]["weights"]["gamma"] = 100
    return model_data


def prepare_abs_schooling_scl_wages(model_data):
    model_data["calibrator"]["weights"]["sf"] = 1
    model_data["calibrator"]["weights"]["sm"] = 1
    model_data["calibrator"]["weights"]["tw"] = 100
    return model_data


def prepare_abs_schooling(model_data):
    model_data["calibrator"]["weights"]["sf"] = 1
    model_data["calibrator"]["weights"]["sm"] = 1
    return model_data


def prepare_abs_schooling_no_wages(model_data):
    model_data["calibrator"]["weights"]["sf"] = 1
    model_data["calibrator"]["weights"]["sm"] = 1
    del model_data["calibrator"]["targets"]["tw"]
    return model_data


def prepare_no_schooling(model_data):
    del model_data["calibrator"]["targets"]["sf"]
    del model_data["calibrator"]["targets"]["sm"]
    return model_data


def prepare_no_schooling_scl_wages(model_data):
    del model_data["calibrator"]["targets"]["sf"]
    del model_data["calibrator"]["targets"]["sm"]
    model_data["calibrator"]["weights"]["tw"] = 100
    return model_data


def prepare_no_wages(model_data):
    del model_data["calibrator"]["targets"]["tw"]
    return model_data


def prepare_no_income_no_wages(model_data):
    del model_data["calibrated"]["hat_c"]
    model_data["hooks"]["hat_c"] = lambda x: 0
    del model_data["calibrator"]["targets"]["tw"]
    return model_data


def prepare_no_income_no_schooling(model_data):
    del model_data["calibrated"]["hat_c"]
    model_data["hooks"]["hat_c"] = lambda x: 0
    del model_data["calibrator"]["targets"]["sf"]
    del model_data["calibrator"]["targets"]["sm"]
    return model_data


def prepare_no_income_no_schooling_scl_wages(model_data):
    del model_data["calibrated"]["hat_c"]
    model_data["hooks"]["hat_c"] = lambda x: 0
    del model_data["calibrator"]["targets"]["sf"]
    del model_data["calibrator"]["targets"]["sm"]
    model_data["calibrator"]["weights"]["tw"] = 100
    return model_data


def mapping():
    return {
        "abs-schooling-scl-wages-scl-income": prepare_abs_schooling_scl_wages_scl_income,
        "abs-schooling-scl-wages": prepare_abs_schooling_scl_wages,
        "abs-schooling": prepare_abs_schooling,  # started here
        "abs-schooling-no-wages": prepare_abs_schooling_no_wages,
        "base": None,
        "no-schooling": prepare_no_schooling,
        "no-schooling-scl-wages": prepare_no_schooling_scl_wages,
        "no-wages": prepare_no_wages,
        "no-income-no-wages": prepare_no_income_no_wages,
        "no-income-no-schooling": prepare_no_income_no_schooling,
        "no-income-no-schooling-scl-wages": prepare_no_income_no_schooling_scl_wages,
    }
