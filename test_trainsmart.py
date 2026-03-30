import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from coach import calculate_target_mileage, calculate_pace_zones, handle_tool_call
from main import app

client = TestClient(app)


# --- Unit tests: calculate_target_mileage ---

def test_target_mileage_caps_at_race_target():
    result = calculate_target_mileage(40, 12, "half marathon")
    assert result["recommended_peak_mileage"] <= 45

def test_target_mileage_respects_10_percent_rule():
    result = calculate_target_mileage(10, 4, "marathon")
    max_possible = 10 * (1.10 ** 4)
    assert result["recommended_peak_mileage"] <= round(max_possible, 1)

def test_target_mileage_taper_is_60_percent_of_peak():
    result = calculate_target_mileage(30, 12, "marathon")
    expected_taper = round(result["recommended_peak_mileage"] * 0.6, 1)
    assert result["taper_week_mileage"] == expected_taper

def test_target_mileage_unknown_race_defaults_to_30():
    result = calculate_target_mileage(20, 8, "obstacle course")
    assert result["recommended_peak_mileage"] <= 30


# --- Unit tests: calculate_pace_zones ---

def test_pace_zones_returns_all_three_zones():
    result = calculate_pace_zones(20, "intermediate")
    assert "easy" in result["pace_zones_per_mile"]
    assert "tempo" in result["pace_zones_per_mile"]
    assert "interval" in result["pace_zones_per_mile"]

def test_pace_zones_beginner():
    result = calculate_pace_zones(10, "beginner")
    assert result["pace_zones_per_mile"]["easy"] == "11:00-12:30"

def test_pace_zones_advanced():
    result = calculate_pace_zones(50, "advanced")
    assert result["pace_zones_per_mile"]["easy"] == "7:30-9:00"

def test_pace_zones_unknown_level_defaults_to_intermediate():
    result = calculate_pace_zones(20, "expert")
    assert result["pace_zones_per_mile"] == calculate_pace_zones(20, "intermediate")["pace_zones_per_mile"]


# --- Unit tests: handle_tool_call ---

def test_handle_tool_call_target_mileage():
    result = handle_tool_call("calculate_target_mileage", {
        "current_mileage": 20,
        "weeks_until_race": 12,
        "goal_race": "half marathon"
    })
    assert "recommended_peak_mileage" in result

def test_handle_tool_call_pace_zones():
    result = handle_tool_call("calculate_pace_zones", {
        "weekly_mileage": 20,
        "experience_level": "intermediate"
    })
    assert "pace_zones_per_mile" in result

def test_handle_tool_call_unknown_tool():
    result = handle_tool_call("nonexistent_tool", {})
    assert "error" in result


# --- Integration test: POST /plan ---

@pytest.mark.asyncio
async def test_plan_endpoint_returns_plan():
    mock_plan = "Here is your training plan for the week: Monday - rest, Tuesday - easy 4 miles..."

    with patch("main.generate_plan", new=AsyncMock(return_value=mock_plan)):
        response = client.post("/plan", json={
            "weekly_mileage": 20,
            "goal_race": "half marathon",
            "weeks_until_race": 12,
            "experience_level": "intermediate"
        })

    assert response.status_code == 200
    assert response.json()["plan"] == mock_plan

def test_plan_endpoint_rejects_invalid_input():
    response = client.post("/plan", json={
        "weekly_mileage": "not a number",
        "goal_race": "half marathon",
        "weeks_until_race": 12,
        "experience_level": "intermediate"
    })
    assert response.status_code == 422

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
