from datetime import date, datetime
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from aceest_app.db import get_db
from aceest_app.logic import (
    calculate_bmi,
    estimate_calories,
    generate_program,
    membership_status,
    parse_iso_date,
    program_factor,
)


api_bp = Blueprint("api", __name__)


def _error(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


def _get_client(name: str):
    conn = get_db()
    cur = conn.execute("SELECT * FROM clients WHERE name = ?", (name,))
    return cur.fetchone()


def _require_json(expected_keys: set[str]) -> Optional[Dict[str, Any]]:
    if not request.is_json:
        return None
    payload = request.get_json(silent=True) or {}
    missing = [k for k in expected_keys if k not in payload]
    if missing:
        raise KeyError(f"Missing keys: {', '.join(missing)}")
    return payload


@api_bp.get("/healthz")
@api_bp.get("/health")
def healthz():
    return jsonify({"status": "ok"})


@api_bp.post("/api/v1/login")
def login():
    if not request.is_json:
        return _error("Expected JSON body", 400)

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not username or not password:
        return _error("username and password are required", 400)

    return jsonify(
        {
            "message": "Login successful",
            "username": username,
            "role": "member",
            "api_version": "v1",
        }
    )


@api_bp.post("/api/clients")
def create_client():
    try:
        payload = _require_json(
            {"name", "age", "height_cm", "weight_kg", "program", "membership_end"}
        )
    except KeyError as e:
        return _error(str(e), 400)

    if payload is None:
        return _error("Expected JSON body", 400)

    name = str(payload["name"]).strip()
    if not name:
        return _error("name must be non-empty", 400)

    try:
        age = int(payload["age"])
        height_cm = float(payload["height_cm"])
        weight_kg = float(payload["weight_kg"])
        program = str(payload["program"]).strip()
        membership_end = str(payload["membership_end"]).strip()
        if membership_end.lower() in {"", "none", "null"}:
            membership_end = None
    except Exception:
        return _error("Invalid types in request payload", 400)

    if age < 0:
        return _error("age must be >= 0", 400)

    try:
        calories = estimate_calories(weight_kg, program_factor(program))
    except ValueError as e:
        return _error(str(e), 400)

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO clients (name, age, height_cm, weight_kg, program, calories, membership_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, age, height_cm, weight_kg, program, calories, membership_end),
        )
        conn.commit()
    except Exception:
        # sqlite3.OperationalError/IntegrityError etc.
        return _error("Client already exists or DB error", 409)

    return (
        jsonify(
            {
                "name": name,
                "age": age,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "program": program,
                "calories": calories,
                "membership_status": membership_status(membership_end),
            }
        ),
        201,
    )


@api_bp.get("/api/clients/<string:name>")
def get_client(name: str):
    client = _get_client(name)
    if client is None:
        return _error("Client not found", 404)

    height_cm = client["height_cm"]
    weight_kg = client["weight_kg"]
    bmi = None

    if height_cm and weight_kg:
        bmi_val = calculate_bmi(float(weight_kg), float(height_cm))
        bmi = bmi_val
        # category computed in analytics endpoint; keep simple here.
    return jsonify(
        {
            "id": client["id"],
            "name": client["name"],
            "age": client["age"],
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "program": client["program"],
            "calories": client["calories"],
            "membership_end": client["membership_end"],
            "membership_status": membership_status(client["membership_end"]),
            "bmi": bmi,
        }
    )


@api_bp.post("/api/clients/<string:name>/progress")
def add_progress(name: str):
    if not request.is_json:
        return _error("Expected JSON body", 400)
    payload = request.get_json(silent=True) or {}

    week = payload.get("week") or datetime.now().strftime("%Y-W%U")
    adherence = payload.get("adherence")
    if adherence is None:
        return _error("Missing adherence", 400)
    try:
        adherence = int(adherence)
    except Exception:
        return _error("adherence must be an integer", 400)

    if adherence < 0 or adherence > 100:
        return _error("adherence must be between 0 and 100", 400)

    conn = get_db()
    client = _get_client(name)
    if client is None:
        return _error("Client not found", 404)

    try:
        conn.execute(
            """
            INSERT INTO progress (client_name, week, adherence)
            VALUES (?, ?, ?)
            """,
            (name, week, adherence),
        )
        conn.commit()
    except Exception:
        return _error("Progress already exists for this week", 409)

    return jsonify({"client_name": name, "week": week, "adherence": adherence}), 201


@api_bp.get("/api/clients/<string:name>/progress")
def list_progress(name: str):
    conn = get_db()
    client = _get_client(name)
    if client is None:
        return _error("Client not found", 404)

    cur = conn.execute(
        """
        SELECT week, adherence
        FROM progress
        WHERE client_name = ?
        ORDER BY id ASC
        """,
        (name,),
    )
    rows = cur.fetchall()
    return jsonify(
        {
            "client_name": name,
            "progress": [{"week": r["week"], "adherence": r["adherence"]} for r in rows],
        }
    )


@api_bp.post("/api/clients/<string:name>/workouts")
def add_workout(name: str):
    if not request.is_json:
        return _error("Expected JSON body", 400)
    payload = request.get_json(silent=True) or {}

    date_value = payload.get("date") or date.today().isoformat()
    workout_type = payload.get("workout_type")
    duration_min = payload.get("duration_min")
    notes = payload.get("notes")

    if not workout_type:
        return _error("Missing workout_type", 400)
    try:
        duration_min = int(duration_min)
    except Exception:
        return _error("duration_min must be an integer", 400)
    if duration_min <= 0:
        return _error("duration_min must be > 0", 400)

    try:
        parse_iso_date(date_value)
    except Exception:
        return _error("date must be in YYYY-MM-DD format", 400)

    conn = get_db()
    if _get_client(name) is None:
        return _error("Client not found", 404)

    conn.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, date_value, str(workout_type).strip(), duration_min, notes),
    )
    conn.commit()
    return jsonify({"client_name": name, "date": date_value, "workout_type": workout_type}), 201


@api_bp.post("/api/clients/<string:name>/metrics")
def add_metrics(name: str):
    if not request.is_json:
        return _error("Expected JSON body", 400)
    payload = request.get_json(silent=True) or {}

    date_value = payload.get("date") or date.today().isoformat()
    weight_kg = payload.get("weight_kg")
    waist_cm = payload.get("waist_cm")
    bodyfat_pct = payload.get("bodyfat_pct")

    try:
        parse_iso_date(date_value)
    except Exception:
        return _error("date must be in YYYY-MM-DD format", 400)

    for key in ["weight_kg", "waist_cm", "bodyfat_pct"]:
        if payload.get(key) is None:
            return _error(f"Missing {key}", 400)
    try:
        weight_kg = float(weight_kg)
        waist_cm = float(waist_cm)
        bodyfat_pct = float(bodyfat_pct)
    except Exception:
        return _error("Invalid numeric types for metrics", 400)

    conn = get_db()
    if _get_client(name) is None:
        return _error("Client not found", 404)

    conn.execute(
        """
        INSERT INTO metrics (client_name, date, weight_kg, waist_cm, bodyfat_pct)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, date_value, weight_kg, waist_cm, bodyfat_pct),
    )
    conn.commit()
    return jsonify({"client_name": name, "date": date_value}), 201


@api_bp.post("/api/v2/membership")
def upsert_membership():
    if not request.is_json:
        return _error("Expected JSON body", 400)

    payload = request.get_json(silent=True) or {}
    client_name = str(payload.get("client_name", "")).strip()
    plan_name = str(payload.get("plan_name", "")).strip()
    membership_end = str(payload.get("membership_end", "")).strip()

    if not client_name or not plan_name or not membership_end:
        return _error("client_name, plan_name and membership_end are required", 400)

    try:
        parse_iso_date(membership_end)
    except Exception:
        return _error("membership_end must be in YYYY-MM-DD format", 400)

    conn = get_db()
    if _get_client(client_name) is None:
        return _error("Client not found", 404)

    conn.execute(
        """
        UPDATE clients
        SET program = ?, membership_end = ?
        WHERE name = ?
        """,
        (plan_name, membership_end, client_name),
    )
    conn.commit()

    return jsonify(
        {
            "client_name": client_name,
            "plan_name": plan_name,
            "membership_end": membership_end,
            "membership_status": membership_status(membership_end),
            "api_version": "v2",
        }
    )


@api_bp.get("/api/clients/<string:name>/analytics")
def analytics(name: str):
    conn = get_db()
    client = _get_client(name)
    if client is None:
        return _error("Client not found", 404)

    height_cm = client["height_cm"]
    weight_kg = client["weight_kg"]
    bmi = None
    bmi_cat = None
    risk = None
    if height_cm and weight_kg:
        bmi = calculate_bmi(float(weight_kg), float(height_cm))
        from aceest_app.logic import bmi_category

        bmi_cat, risk = bmi_category(bmi)

    cur = conn.execute(
        """
        SELECT date, weight_kg, waist_cm, bodyfat_pct
        FROM metrics
        WHERE client_name = ?
        ORDER BY date DESC, id DESC
        LIMIT 1
        """,
        (name,),
    )
    latest = cur.fetchone()

    return jsonify(
        {
            "client_name": name,
            "membership_status": membership_status(client["membership_end"]),
            "bmi": bmi,
            "bmi_category": bmi_cat,
            "bmi_risk_note": risk,
            "latest_metrics": (
                {
                    "date": latest["date"],
                    "weight_kg": latest["weight_kg"],
                    "waist_cm": latest["waist_cm"],
                    "bodyfat_pct": latest["bodyfat_pct"],
                }
                if latest
                else None
            ),
        }
    )


@api_bp.post("/api/clients/<string:name>/program")
def program_endpoint(name: str):
    if not request.is_json:
        return _error("Expected JSON body", 400)
    payload = request.get_json(silent=True) or {}

    experience = payload.get("experience")
    if not experience:
        return _error("Missing experience", 400)

    seed = payload.get("seed")
    seed_value = None
    if seed is not None:
        try:
            seed_value = int(seed)
        except Exception:
            return _error("seed must be an integer", 400)

    get_db()
    if _get_client(name) is None:
        return _error("Client not found", 404)

    client_seed = seed_value
    if client_seed is None:
        from aceest_app.logic import stable_seed

        client_seed = stable_seed(name, str(experience))

    try:
        plan = generate_program(str(experience), seed=client_seed)
    except Exception as e:
        return _error(str(e), 400)

    return jsonify({"client_name": name, "program_plan": plan}), 201


@api_bp.post("/api/v3/bookings")
def create_booking():
    if not request.is_json:
        return _error("Expected JSON body", 400)

    payload = request.get_json(silent=True) or {}
    client_name = str(payload.get("client_name", "")).strip()
    session_name = str(payload.get("session_name", "")).strip()
    booking_date = str(payload.get("booking_date", "")).strip()
    trainer = str(payload.get("trainer", "")).strip() or None

    if not client_name or not session_name or not booking_date:
        return _error("client_name, session_name and booking_date are required", 400)

    try:
        parse_iso_date(booking_date)
    except Exception:
        return _error("booking_date must be in YYYY-MM-DD format", 400)

    conn = get_db()
    if _get_client(client_name) is None:
        return _error("Client not found", 404)

    conn.execute(
        """
        INSERT INTO bookings (client_name, session_name, booking_date, trainer)
        VALUES (?, ?, ?, ?)
        """,
        (client_name, session_name, booking_date, trainer),
    )
    conn.commit()

    return jsonify(
        {
            "client_name": client_name,
            "session_name": session_name,
            "booking_date": booking_date,
            "trainer": trainer,
            "api_version": "v3",
        }
    ), 201


@api_bp.get("/api/v3/bookings/<string:name>")
def list_bookings(name: str):
    conn = get_db()
    if _get_client(name) is None:
        return _error("Client not found", 404)

    cur = conn.execute(
        """
        SELECT session_name, booking_date, trainer
        FROM bookings
        WHERE client_name = ?
        ORDER BY booking_date ASC, id ASC
        """,
        (name,),
    )
    rows = cur.fetchall()
    return jsonify(
        {
            "client_name": name,
            "bookings": [
                {
                    "session_name": row["session_name"],
                    "booking_date": row["booking_date"],
                    "trainer": row["trainer"],
                }
                for row in rows
            ],
        }
    )

