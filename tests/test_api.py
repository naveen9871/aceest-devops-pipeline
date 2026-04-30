import pytest

from aceest_app.factory import create_app


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "aceest_test.db"
    return create_app({"TESTING": True, "DB_PATH": str(db_path)})


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_and_get_client(client):
    payload = {
        "name": "Rahul",
        "age": 28,
        "height_cm": 175,
        "weight_kg": 80,
        "program": "Fat Loss",
        "membership_end": "2099-01-01",
    }

    res = client.post("/api/clients", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Rahul"
    assert data["membership_status"] == "Active"
    assert data["calories"] > 0

    res2 = client.get("/api/clients/Rahul")
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["name"] == "Rahul"
    assert data2["program"] == "Fat Loss"


def test_progress_happy_path_and_validation(client):
    payload = {
        "name": "Meera",
        "age": 25,
        "height_cm": 165,
        "weight_kg": 60,
        "program": "Beginner",
        "membership_end": "2099-01-01",
    }
    client.post("/api/clients", json=payload).status_code

    res = client.post(
        "/api/clients/Meera/progress",
        json={"week": "2026-W01", "adherence": 87},
    )
    assert res.status_code == 201
    assert res.get_json()["adherence"] == 87

    res_bad = client.post(
        "/api/clients/Meera/progress",
        json={"week": "2026-W02", "adherence": 120},
    )
    assert res_bad.status_code == 400

    res_list = client.get("/api/clients/Meera/progress")
    assert res_list.status_code == 200
    data = res_list.get_json()
    assert len(data["progress"]) == 1
    assert data["progress"][0]["week"] == "2026-W01"


def test_program_endpoint_returns_deterministic_plan(client):
    client.post(
        "/api/clients",
        json={
            "name": "Arjun",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 85,
            "program": "Muscle Gain",
            "membership_end": "2099-01-01",
        },
    )

    res1 = client.post(
        "/api/clients/Arjun/program",
        json={"experience": "beginner", "seed": 42},
    )
    res2 = client.post(
        "/api/clients/Arjun/program",
        json={"experience": "beginner", "seed": 42},
    )

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.get_json()["program_plan"] == res2.get_json()["program_plan"]


def test_versioned_login_membership_and_booking_flow(client):
    create_res = client.post(
        "/api/clients",
        json={
            "name": "Kiran",
            "age": 27,
            "height_cm": 172,
            "weight_kg": 74,
            "program": "Beginner",
            "membership_end": "2099-01-01",
        },
    )
    assert create_res.status_code == 201

    login_res = client.post(
        "/api/v1/login",
        json={"username": "kiran", "password": "securepass"},
    )
    assert login_res.status_code == 200
    assert login_res.get_json()["api_version"] == "v1"

    membership_res = client.post(
        "/api/v2/membership",
        json={
            "client_name": "Kiran",
            "plan_name": "Premium Strength",
            "membership_end": "2099-06-30",
        },
    )
    assert membership_res.status_code == 200
    assert membership_res.get_json()["plan_name"] == "Premium Strength"

    booking_res = client.post(
        "/api/v3/bookings",
        json={
            "client_name": "Kiran",
            "session_name": "Morning HIIT",
            "booking_date": "2026-05-10",
            "trainer": "Asha",
        },
    )
    assert booking_res.status_code == 201
    assert booking_res.get_json()["api_version"] == "v3"

    list_res = client.get("/api/v3/bookings/Kiran")
    assert list_res.status_code == 200
    data = list_res.get_json()
    assert len(data["bookings"]) == 1
    assert data["bookings"][0]["session_name"] == "Morning HIIT"

