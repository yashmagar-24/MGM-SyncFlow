"""
LLGCA Flask API Server
Serves the dashboard HTML and provides REST endpoints for the LLGCA database.
"""

import hashlib
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId

# ── Config ──────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb+srv://user:user123@mgm.ywwu9cl.mongodb.net/?appName=mgm"
DB_NAME   = "llgca_db"
# ─────────────────────────────────────────────────────────────────────────────

# Aurangabad CCTV camera locations
CCTV_LOCATIONS = [
    { "id": "CCTV-01", "name": "MGM College Junction",      "lat": 19.8782, "lng": 75.3280 },
    { "id": "CCTV-02", "name": "CIDCO N-1 Junction",         "lat": 19.8830, "lng": 75.3420 },
    { "id": "CCTV-03", "name": "Railway Station Circle",     "lat": 19.8966, "lng": 75.3216 },
    { "id": "CCTV-04", "name": "Kranti Chowk",               "lat": 19.9012, "lng": 75.3356 },
    { "id": "CCTV-05", "name": "Airport Road Junction",       "lat": 19.8625, "lng": 75.3981 },
    { "id": "CCTV-06", "name": "Paithan Gate",               "lat": 19.8839, "lng": 75.3132 },
    { "id": "CCTV-07", "name": "Jalsa Chowk",                "lat": 19.8880, "lng": 75.3100 },
    { "id": "CCTV-08", "name": "N-8 CIDCO, Shalimar",       "lat": 19.8920, "lng": 75.3480 },
]

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ── DB Connection ─────────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def serialize(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    for key, val in doc.items():
        if isinstance(val, ObjectId):
            doc[key] = str(val)
        elif isinstance(val, datetime):
            doc[key] = val.isoformat()
    return doc


def serialize_list(docs):
    return [serialize(d) for d in docs]


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = db["users"].find_one({"username": username, "isActive": True})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if user["passwordHash"] != hash_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Update lastLogin
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"lastLogin": datetime.utcnow()}})

    # Audit log
    db["auditLogs"].insert_one({
        "userId":    user["_id"],
        "action":    "login",
        "details":   {"method": "password"},
        "ipAddress": request.remote_addr,
        "userAgent": request.headers.get("User-Agent", ""),
        "timestamp": datetime.utcnow(),
    })

    return jsonify({
        "token":  hashlib.sha256(f"{user['_id']}{datetime.utcnow()}".encode()).hexdigest(),
        "user": {
            "id":       str(user["_id"]),
            "username": user["username"],
            "name":     user["name"],
            "role":     user["role"],
        }
    })


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user_id = db["users"].find_one({"username": request.json.get("username")})["_id"] if request.get_json() else None
        if user_id:
            db["auditLogs"].insert_one({
                "userId":    user_id,
                "action":    "logout",
                "details":   {},
                "ipAddress": request.remote_addr,
                "userAgent": request.headers.get("User-Agent", ""),
                "timestamp": datetime.utcnow(),
            })
    return jsonify({"ok": True})


# ── Dashboard Stats ────────────────────────────────────────────────────────────
@app.route("/api/dashboard/stats")
def dashboard_stats():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    active_emergencies = db["emergencies"].count_documents({
        "status": {"$in": ["pending", "dispatched", "en_route"]}
    })
    en_route = db["emergencies"].count_documents({"status": "en_route"})
    corridors_active = db["greenCorridors"].count_documents({"status": "active"})
    total_today = db["emergencies"].count_documents({"createdAt": {"$gte": today_start}})

    # Fetch avg dispatch time from settings
    setting = db["systemSettings"].find_one({"key": "avgDispatchTimeMinutes"})
    avg_dispatch = setting["value"] if setting else 1.8

    return jsonify({
        "activeEmergencies": active_emergencies,
        "enRoute":           en_route,
        "corridorsActive":   corridors_active,
        "totalToday":        total_today,
        "avgDispatchTime":   avg_dispatch,
    })


# ── Hospitals ─────────────────────────────────────────────────────────────────
@app.route("/api/hospitals")
def get_hospitals():
    hospitals = serialize_list(db["hospitals"].find({"isActive": True}))
    return jsonify(hospitals)


@app.route("/api/hospitals/<hospital_id>/beds", methods=["PUT"])
def update_hospital_beds(hospital_id):
    data = request.get_json()
    beds = data.get("beds", [])

    # Recompute status for each bed category
    for bed in beds:
        ratio = bed["available"] / bed["total"] if bed["total"] > 0 else 0
        if ratio == 0:
            bed["status"] = "full"
        elif ratio <= 0.2:
            bed["status"] = "low"
        else:
            bed["status"] = "ok"

    db["hospitals"].update_one(
        {"_id": ObjectId(hospital_id)},
        {"$set": {"beds": beds, "updatedAt": datetime.utcnow()}}
    )
    hospital = db["hospitals"].find_one({"_id": ObjectId(hospital_id)})
    return jsonify(serialize(hospital))


# ── Emergencies ───────────────────────────────────────────────────────────────
@app.route("/api/emergencies")
def get_emergencies():
    status_filter = request.args.get("status")
    query = {}
    if status_filter:
        query["status"] = status_filter

    emergencies = serialize_list(
        db["emergencies"].find(query).sort("createdAt", -1).limit(50)
    )
    return jsonify(emergencies)


@app.route("/api/emergencies/active")
def get_active_emergencies():
    """Emergencies with their patient data for the overview table."""
    emergencies = db["emergencies"].find({
        "status": {"$in": ["pending", "dispatched", "en_route"]}
    }).sort("createdAt", -1)

    result = []
    for e in emergencies:
        raw_id = e["_id"]
        e_data = serialize(e)
        patient = db["patients"].find_one({"emergencyId": raw_id})
        hospital = db["hospitals"].find_one({"_id": e.get("assignedHospitalId")}) if e.get("assignedHospitalId") else None
        ambulance = db["ambulances"].find_one({"_id": e.get("assignedAmbulanceId")}) if e.get("assignedAmbulanceId") else None
        corridor = db["greenCorridors"].find_one({"emergencyId": raw_id, "status": "active"}) if e.get("status") == "en_route" else None

        eta = corridor["etaMinutes"] if corridor else None
        e_data["patient"] = serialize(patient) if patient else None
        e_data["hospital"] = {"name": hospital["name"]} if hospital else None
        e_data["ambulance"] = {"callSign": ambulance["callSign"]} if ambulance else None
        e_data["eta"] = eta
        result.append(e_data)

    return jsonify(result)


@app.route("/api/emergencies", methods=["POST"])
def create_emergency():
    data = request.get_json()
    creator_username = data.pop("createdBy", "admin")
    creator = db["users"].find_one({"username": creator_username})

    # Generate case number
    year = datetime.utcnow().year
    count = db["emergencies"].count_documents({}) + 1
    case_number = f"LLGCA-{year}-{count:04d}"

    emergency = {
        "caseNumber":        case_number,
        "status":            "pending",
        "emergencyType":     data.get("emergencyType", "Other"),
        "pickupLocation":    data.get("pickupLocation", ""),
        "pickupCoordinates":  data.get("pickupCoordinates", {}),
        "assignedAmbulanceId": None,
        "assignedHospitalId":  None,
        "dispatchedAt":       None,
        "arrivedAt":          None,
        "completedAt":        None,
        "notes":              data.get("notes", ""),
        "createdBy":          creator["_id"] if creator else None,
        "createdAt":          datetime.utcnow(),
        "updatedAt":          datetime.utcnow(),
    }
    emerg_id = db["emergencies"].insert_one(emergency).inserted_id

    # Create patient record
    patient = {
        "emergencyId":    emerg_id,
        "name":           data.get("patientName", ""),
        "age":            data.get("age", 0),
        "gender":         data.get("gender", ""),
        "contactNumber":  data.get("contactNumber", ""),
        "vitals": {
            "conscious":         data.get("vitals", {}).get("conscious", True),
            "breathingNormally": data.get("vitals", {}).get("breathingNormally", True),
            "severeBleeding":    data.get("vitals", {}).get("severeBleeding", False),
        },
        "pcsScore":   0,
        "aiAssessment": None,
        "status":     "awaiting_assessment",
    }
    patient_id = db["patients"].insert_one(patient).inserted_id

    # Audit log
    if creator:
        db["auditLogs"].insert_one({
            "userId":    creator["_id"],
            "action":    "create_emergency",
            "details":   {"caseNumber": case_number, "emergencyType": emergency["emergencyType"]},
            "ipAddress": request.remote_addr,
            "userAgent": request.headers.get("User-Agent", ""),
            "timestamp": datetime.utcnow(),
        })

    return jsonify({
        "emergency": serialize(db["emergencies"].find_one({"_id": emerg_id})),
        "patient":   serialize(db["patients"].find_one({"_id": patient_id})),
    }), 201


@app.route("/api/emergencies/<emerg_id>", methods=["PUT"])
def update_emergency(emerg_id):
    data = request.get_json()
    update_fields = {k: v for k, v in data.items() if k not in ("_id",)}
    update_fields["updatedAt"] = datetime.utcnow()
    db["emergencies"].update_one({"_id": ObjectId(emerg_id)}, {"$set": update_fields})
    return jsonify(serialize(db["emergencies"].find_one({"_id": ObjectId(emerg_id)})))


@app.route("/api/emergencies/<emerg_id>/dispatch", methods=["POST"])
def dispatch_emergency(emerg_id):
    """Assign ambulance and hospital to an emergency and log dispatch events."""
    data = request.get_json()
    ambulance_id = data.get("ambulanceId")
    hospital_id  = data.get("hospitalId")
    actor_username = data.get("actor", "admin")

    actor = db["users"].find_one({"username": actor_username})

    ambulance = db["ambulances"].find_one({"_id": ObjectId(ambulance_id)})
    hospital  = db["hospitals"].find_one({"_id": ObjectId(hospital_id)})

    now = datetime.utcnow()

    # Update emergency
    db["emergencies"].update_one({"_id": ObjectId(emerg_id)}, {"$set": {
        "assignedAmbulanceId": ambulance["_id"],
        "assignedHospitalId":  hospital["_id"],
        "status":             "dispatched",
        "dispatchedAt":       now,
        "updatedAt":          now,
    }})

    # Update ambulance status
    db["ambulances"].update_one({"_id": ObjectId(ambulance_id)}, {"$set": {
        "status":             "dispatched",
        "currentEmergencyId": ObjectId(emerg_id),
    }})

    # Insert dispatch event
    db["dispatches"].insert_one({
        "emergencyId": ObjectId(emerg_id),
        "ambulanceId":  ambulance["_id"],
        "hospitalId":   hospital["_id"],
        "action":       "dispatched",
        "timestamp":    now,
        "location":     ambulance.get("currentLocation", {}),
        "actor":        actor["_id"] if actor else None,
        "notes":        f"Dispatched {ambulance['callSign']} to {hospital['shortName']}",
    })

    # Log audit
    if actor:
        db["auditLogs"].insert_one({
            "userId":    actor["_id"],
            "action":    "dispatch",
            "details":   {"caseNumber": emerg_id, "ambulance": ambulance["callSign"], "hospital": hospital["shortName"]},
            "ipAddress": request.remote_addr,
            "userAgent": request.headers.get("User-Agent", ""),
            "timestamp": now,
        })

    return jsonify(serialize(db["emergencies"].find_one({"_id": ObjectId(emerg_id)})))


# ── Ambulances ────────────────────────────────────────────────────────────────
@app.route("/api/ambulances")
def get_ambulances():
    status_filter = request.args.get("status")
    query = {} if not status_filter else {"status": status_filter}
    ambulances = serialize_list(db["ambulances"].find(query))
    return jsonify(ambulances)


@app.route("/api/ambulances/available")
def available_ambulances():
    """Return only available ambulances."""
    ambulances = serialize_list(db["ambulances"].find({"status": "available"}))
    return jsonify(ambulances)


@app.route("/api/ambulances/<amb_id>/location", methods=["PUT"])
def update_ambulance_location(amb_id):
    data = request.get_json()
    db["ambulances"].update_one({"_id": ObjectId(amb_id)}, {"$set": {
        "currentLocation": data.get("location", {}),
        "lastUpdated":     datetime.utcnow(),
    }})
    return jsonify({"ok": True})


# ── AI Assessment ─────────────────────────────────────────────────────────────
@app.route("/api/emergencies/<emerg_id>/assess", methods=["POST"])
def run_ai_assessment(emerg_id):
    """
    Placeholder AI assessment.
    In production, this calls Cerebras LLaMA-3.1-70b.
    Returns a computed PCS score and summary based on vitals.
    """
    patient = db["patients"].find_one({"emergencyId": ObjectId(emerg_id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    vitals = patient.get("vitals", {})
    conscious = vitals.get("conscious", True)
    breathing = vitals.get("breathingNormally", True)
    bleeding = vitals.get("severeBleeding", False)

    # Simple heuristic PCS (0-10)
    score = 0
    if not conscious: score += 4
    if not breathing: score += 3
    if bleeding: score += 3

    summary = (
        "Patient is conscious and breathing normally. Minor assessment needed."
        if score < 4 else
        "Patient requires immediate medical attention. Prepare for critical arrival."
        if score < 7 else
        "Critical patient. Immediate ICU transfer required. High priority corridor activated."
    )

    ai_assessment = {
        "summary":                  summary,
        "recommendedHospitalType":  "Trauma" if bleeding else ("Cardiac" if not breathing else "General"),
        "symptomScores": {
            "heartRate":       random.randint(3, 9) if not breathing else random.randint(4, 7),
            "bloodPressure":    random.randint(2, 6),
            "respRate":         1 if not breathing else random.randint(4, 7),
            "consciousness":    0 if not conscious else random.randint(6, 9),
            "bleeding":         2 if bleeding else 7,
        },
        "assessedAt": datetime.utcnow(),
    }

    db["patients"].update_one({"_id": patient["_id"]}, {"$set": {
        "pcsScore":       score,
        "aiAssessment":   ai_assessment,
        "status":         "assessed",
    }})

    return jsonify(serialize(db["patients"].find_one({"_id": patient["_id"]})))


# ── Green Corridor ────────────────────────────────────────────────────────────
@app.route("/api/emergencies/<emerg_id>/corridor", methods=["POST"])
def activate_corridor(emerg_id):
    """Activate a green corridor for an en-route emergency."""
    data = request.get_json()
    hospital_id = data.get("hospitalId")

    hospital = db["hospitals"].find_one({"_id": ObjectId(hospital_id)})
    emergency = db["emergencies"].find_one({"_id": ObjectId(emerg_id)})

    # Simple ETA based on distance
    eta_minutes = int(hospital.get("avgResponseTime", 15)) if hospital else 15

    corridor = {
        "emergencyId":          ObjectId(emerg_id),
        "status":               "active",
        "route":                data.get("route", []),
        "distanceKm":           data.get("distanceKm", 0),
        "signalsCleared":       0,
        "activationTime":       datetime.utcnow(),
        "clearedTime":          None,
        "timeSavedPercent":     45,
        "originLocation":       emergency.get("pickupCoordinates", {}),
        "destinationHospitalId": ObjectId(hospital_id),
        "etaMinutes":           eta_minutes,
    }
    corridor_id = db["greenCorridors"].insert_one(corridor).inserted_id

    # Update emergency status
    db["emergencies"].update_one({"_id": ObjectId(emerg_id)}, {"$set": {
        "status":    "en_route",
        "updatedAt": datetime.utcnow(),
    }})

    # Update ambulance status
    if emergency.get("assignedAmbulanceId"):
        db["ambulances"].update_one({"_id": emergency["assignedAmbulanceId"]}, {"$set": {
            "status": "en_route",
        }})

    return jsonify(serialize(db["greenCorridors"].find_one({"_id": corridor_id})))


@app.route("/api/corridors/active")
def get_active_corridors():
    corridors = serialize_list(db["greenCorridors"].find({"status": "active"}))
    return jsonify(corridors)


# ── CCTV Locations ─────────────────────────────────────────────────────────────
@app.route("/api/cctv-locations")
def get_cctv_locations():
    """Return list of CCTV camera positions in Aurangabad."""
    return jsonify(CCTV_LOCATIONS)


# ── Live Tracking ─────────────────────────────────────────────────────────────
@app.route("/api/tracking/<emerg_id>")
def get_tracking(emerg_id):
    """
    Return current ambulance position, nearest CCTV, and progress
    for an active emergency.
    """
    try:
        emergency = db["emergencies"].find_one({"_id": ObjectId(emerg_id)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400

    if not emergency:
        return jsonify({"error": "Emergency not found"}), 404

    ambulance = None
    if emergency.get("assignedAmbulanceId"):
        ambulance = db["ambulances"].find_one({"_id": emergency["assignedAmbulanceId"]})

    corridor = db["greenCorridors"].find_one({
        "emergencyId": ObjectId(emerg_id),
        "status": {"$in": ["active", "cleared"]},
    })

    # Determine nearest CCTV to ambulance
    nearest_cctv = None
    if ambulance and ambulance.get("currentLocation"):
        amb_loc = ambulance["currentLocation"]
        min_dist = float("inf")
        for cctv in CCTV_LOCATIONS:
            d = ((amb_loc["lat"] - cctv["lat"]) ** 2 + (amb_loc["lng"] - cctv["lng"]) ** 2) ** 0.5
            if d < min_dist:
                min_dist = d
                nearest_cctv = cctv

    # Progress: how many CCTV checkpoints passed out of total route
    progress = 0
    if corridor and ambulance and ambulance.get("currentLocation"):
        route = corridor.get("route", [])
        amb_loc = ambulance["currentLocation"]
        passed = 0
        for waypoint in route:
            w_lat = waypoint.get("lat", 0)
            w_lng = waypoint.get("lng", 0)
            d = ((amb_loc["lat"] - w_lat) ** 2 + (amb_loc["lng"] - w_lng) ** 2) ** 0.5
            if d < 0.005:  # within ~500m
                passed += 1
        if route:
            progress = min(int(passed / len(route) * 100), 100)

    return jsonify({
        "emergency":     serialize(emergency),
        "ambulance":     serialize(ambulance) if ambulance else None,
        "corridor":      serialize(corridor) if corridor else None,
        "nearestCCTV":   nearest_cctv,
        "progress":      progress,
    })


# ── Update Ambulance Location (called by tracking simulation) ──────────────────
@app.route("/api/tracking/<emerg_id>/move", methods=["POST"])
def move_ambulance(emerg_id):
    """
    Advance ambulance position along the CCTV route.
    Called periodically by the frontend tracking simulation.
    """
    emergency = db["emergencies"].find_one({"_id": ObjectId(emerg_id)})
    if not emergency:
        return jsonify({"error": "Emergency not found"}), 404

    corridor = db["greenCorridors"].find_one({
        "emergencyId": ObjectId(emerg_id),
        "status": "active",
    })
    if not corridor:
        return jsonify({"error": "No active corridor"}), 400

    ambulance = None
    if emergency.get("assignedAmbulanceId"):
        ambulance = db["ambulances"].find_one({"_id": emergency["assignedAmbulanceId"]})
    if not ambulance:
        return jsonify({"error": "No ambulance assigned"}), 400

    route = corridor.get("route", [])
    if not route:
        return jsonify({"error": "No route defined"}), 400

    current = ambulance.get("currentLocation", route[0] if route else {})
    current_idx = 0
    for i, wp in enumerate(route):
        if abs(wp["lat"] - current["lat"]) < 0.001 and abs(wp["lng"] - current["lng"]) < 0.001:
            current_idx = i
            break

    # Move to next waypoint
    if current_idx < len(route) - 1:
        next_wp = route[current_idx + 1]
        new_loc = {"lat": next_wp["lat"], "lng": next_wp["lng"]}
        signals = corridor.get("signalsCleared", 0) + 1
    else:
        # Reached destination
        new_loc = {"lat": route[-1]["lat"], "lng": route[-1]["lng"]}
        signals = corridor.get("signalsCleared", 0)

        # Mark corridor cleared
        db["greenCorridors"].update_one({"_id": corridor["_id"]}, {"$set": {
            "status":       "cleared",
            "clearedTime":  datetime.utcnow(),
        }})

        # Mark emergency arrived
        db["emergencies"].update_one({"_id": ObjectId(emerg_id)}, {"$set": {
            "status":     "arrived",
            "arrivedAt":  datetime.utcnow(),
            "updatedAt":  datetime.utcnow(),
        }})

        # Free up ambulance
        db["ambulances"].update_one({"_id": ambulance["_id"]}, {"$set": {
            "status":             "at_hospital",
            "currentEmergencyId": None,
        }})

        return jsonify({
            "arrived":    True,
            "location":   new_loc,
            "signals":    signals,
            "ambulance":  serialize(db["ambulances"].find_one({"_id": ambulance["_id"]})),
        })

    # Update ambulance position
    db["ambulances"].update_one({"_id": ambulance["_id"]}, {"$set": {
        "currentLocation": new_loc,
        "lastUpdated":    datetime.utcnow(),
    }})

    # Update corridor signals cleared
    db["greenCorridors"].update_one({"_id": corridor["_id"]}, {"$set": {
        "signalsCleared": signals,
    }})

    # Log en_route dispatch event if this is the first move
    existing = db["dispatches"].find_one({"emergencyId": ObjectId(emerg_id), "action": "en_route"})
    if not existing:
        db["dispatches"].insert_one({
            "emergencyId": ObjectId(emerg_id),
            "ambulanceId":  ambulance["_id"],
            "hospitalId":   emergency.get("assignedHospitalId"),
            "action":       "en_route",
            "timestamp":    datetime.utcnow(),
            "location":     new_loc,
            "actor":        None,
            "notes":        "Ambulance en route to hospital",
        })

    return jsonify({
        "arrived":  False,
        "location": new_loc,
        "signals":  signals,
        "nearestCCTV": _nearest_cctv(new_loc),
    })


def _nearest_cctv(location):
    min_dist = float("inf")
    nearest = None
    for cctv in CCTV_LOCATIONS:
        d = ((location["lat"] - cctv["lat"]) ** 2 + (location["lng"] - cctv["lng"]) ** 2) ** 0.5
        if d < min_dist:
            min_dist = d
            nearest = cctv
    return nearest


# ── System Settings ──────────────────────────────────────────────────────────
@app.route("/api/settings")
def get_settings():
    settings = {s["key"]: s["value"] for s in db["systemSettings"].find()}
    return jsonify(settings)


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    data = request.get_json()
    for key, value in data.items():
        db["systemSettings"].update_one(
            {"key": key},
            {"$set": {"value": value, "updatedAt": datetime.utcnow()}},
            upsert=True,
        )
    return jsonify({"ok": True})


# ── Notifications ─────────────────────────────────────────────────────────────
@app.route("/api/notifications")
def get_notifications():
    notifications = serialize_list(
        db["notifications"].find().sort("sentAt", -1).limit(50)
    )
    return jsonify(notifications)


@app.route("/api/notifications", methods=["POST"])
def create_notification():
    data = request.get_json()
    notification = {
        "emergencyId":   ObjectId(data["emergencyId"]) if data.get("emergencyId") else None,
        "type":          data.get("type", "dispatcher"),
        "channel":       data.get("channel", "email"),
        "recipient":     data.get("recipient", ""),
        "subject":       data.get("subject", ""),
        "body":          data.get("body", ""),
        "status":        "queued",
        "sentAt":        None,
        "errorMessage":  None,
    }
    nid = db["notifications"].insert_one(notification).inserted_id
    return jsonify(serialize(db["notifications"].find_one({"_id": nid}))), 201


# ── Serve HTML ────────────────────────────────────────────────────────────────
@app.route("/")
def serve_login():
    return send_from_directory(".", "login.html")


@app.route("/dashboard")
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting LLGCA API server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
