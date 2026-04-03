from datetime import date

import pytest

from aceest_app.logic import (
    bmi_category,
    calculate_bmi,
    estimate_calories,
    generate_program,
    membership_status,
)


def test_estimate_calories_basic():
    assert estimate_calories(70, 24.0) == 1680


def test_calculate_bmi_rounding_and_category():
    bmi = calculate_bmi(weight_kg=65, height_cm=170)
    # 65 / (1.70^2) ~= 22.5
    assert bmi == 22.5
    cat, _ = bmi_category(bmi)
    assert cat == "Normal"


def test_membership_status_active_and_expired():
    assert membership_status("2099-01-01", today=date(2026, 1, 1)) == "Active"
    assert membership_status("2000-01-01", today=date(2026, 1, 1)) == "Expired"
    assert membership_status(None) == "Unknown"


def test_generate_program_deterministic_with_seed():
    plan1 = generate_program("beginner", seed=12345)
    plan2 = generate_program("beginner", seed=12345)
    assert plan1 == plan2
    assert len(plan1["days"]) == 3
    for day in plan1["days"]:
        assert "day" in day
        assert len(day["items"]) == 3  # beginner uses 3 items per day (days < 4)

