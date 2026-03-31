"""
LLGCA Database Setup Script
Run once to create the llgca_db database, collections, and dummy data.

Usage:
    pip install pymongo
    python setup_db.py
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
import random
import hashlib

# ── Config ──────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb+srv://user:user123@mgm.ywwu9cl.mongodb.net/?appName=mgm"
DB_NAME   = "llgca_db"
# ─────────────────────────────────────────────────────────────────────────────


def get_client():
    return MongoClient(MONGO_URI)


def create_collections(db):
    """Create all collections with validation where applicable."""
    existing = db.list_collection_names()

    collections = [
        "users",
        "emergencies",
        "patients",
        "ambulances",
        "hospitals",
        "greenCorridors",
        "dispatches",
        "notifications",
        "systemSettings",
        "auditLogs",
    ]

    for name in collections:
        if name not in existing:
            db.create_collection(name)
            print(f"  Created collection: {name}")
        else:
            print(f"  Collection already exists: {name}")


def create_indexes(db):
    """Create recommended indexes."""
    indexes = [
        ("emergencies",        [("status", ASCENDING)]),
        ("emergencies",        [("caseNumber", ASCENDING)]),
        ("emergencies",        [("createdAt", DESCENDING)]),
        ("patients",           [("emergencyId", ASCENDING)]),
        ("ambulances",         [("status", ASCENDING)]),
        ("hospitals",          [("beds.category", ASCENDING), ("beds.available", ASCENDING)]),
        ("greenCorridors",     [("status", ASCENDING)]),
        ("dispatches",         [("emergencyId", ASCENDING), ("timestamp", DESCENDING)]),
        ("auditLogs",          [("userId", ASCENDING), ("timestamp", DESCENDING)]),
    ]

    for coll_name, keys in indexes:
        coll = db[coll_name]
        for key, direction in keys:
            try:
                coll.create_index([(key, direction)])
                print(f"  Indexed {coll_name}.{key}")
            except Exception as e:
                print(f"  Index already exists: {coll_name}.{key}")


def hash_password(password: str) -> str:
    """Simple SHA-256 hash for dummy passwords (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_users(db):
    """Seed operators / admins."""
    coll = db["users"]
    if coll.count_documents({}) > 0:
        print("  users — already seeded, skipping")
        return

    now = datetime.utcnow()
    docs = [
        {
            "username":    "admin",
            "passwordHash": hash_password("admin123"),
            "role":        "admin",
            "name":        "Rahul Sharma",
            "email":       "rahul.sharma@llgca.gov.in",
            "isActive":    True,
            "lastLogin":   None,
            "createdAt":   now,
        },
        {
            "username":    "dispatcher1",
            "passwordHash": hash_password("dispatch123"),
            "role":        "operator",
            "name":        "Priya Verma",
            "email":       "priya.verma@llgca.gov.in",
            "isActive":    True,
            "lastLogin":   None,
            "createdAt":   now,
        },
        {
            "username":    "viewer",
            "passwordHash": hash_password("viewer123"),
            "role":        "viewer",
            "name":        "Amit Kumar",
            "email":       "amit.kumar@llgca.gov.in",
            "isActive":    True,
            "lastLogin":   None,
            "createdAt":   now,
        },
    ]
    coll.insert_many(docs)
    print("  Seeded 3 users")


def seed_hospitals(db):
    """Seed hospital network."""
    coll = db["hospitals"]
    if coll.count_documents({}) > 0:
        print("  hospitals — already seeded, skipping")
        return

    now = datetime.utcnow()
    docs = [
        {
            "name":           "MGM Medical College, Aurangabad",
            "shortName":      "MGM Hospital",
            "type":           "Government",
            "level":          "Level 1 Trauma",
            "address":        "MGM Campus, Aurangabad, Maharashtra 431003",
            "coordinates":    { "lat": 19.8782, "lng": 75.3280 },
            "phone":          "+91-240-2371234",
            "beds": [
                { "category": "ICU",        "total": 20, "available": 6,  "status": "ok"   },
                { "category": "Cardiology",  "total": 12, "available": 3,  "status": "ok"   },
                { "category": "Emergency",   "total": 10, "available": 2,  "status": "low"  },
                { "category": "General",     "total": 60, "available": 18, "status": "ok"   },
            ],
            "isActive":         True,
            "avgResponseTime":  5.2,
            "createdAt":        now,
            "updatedAt":        now,
        },
        {
            "name":           "Aurangabad Civil Hospital",
            "shortName":      "Civil Hospital",
            "type":           "Government",
            "level":          "Level 1",
            "address":        "City Chowk, Aurangabad, Maharashtra 431001",
            "coordinates":    { "lat": 19.8966, "lng": 75.3216 },
            "phone":          "+91-240-2331245",
            "beds": [
                { "category": "ICU",        "total": 15, "available": 2,  "status": "low"  },
                { "category": "Emergency",   "total": 12, "available": 0,  "status": "full" },
                { "category": "General",     "total": 50, "available": 10, "status": "ok"   },
            ],
            "isActive":         True,
            "avgResponseTime":  3.1,
            "createdAt":        now,
            "updatedAt":        now,
        },
        {
            "name":           "Oak Multispeciality Hospital, Aurangabad",
            "shortName":      "Oak Hospital",
            "type":           "Private",
            "level":          "Multispeciality",
            "address":        "Opp. Railway Station, Aurangabad, Maharashtra 431005",
            "coordinates":    { "lat": 19.8947, "lng": 75.3230 },
            "phone":          "+91-240-2470001",
            "beds": [
                { "category": "ICU",        "total": 18, "available": 7,  "status": "ok"   },
                { "category": "Cardiology",  "total": 8,  "available": 3,  "status": "ok"   },
                { "category": "Emergency",   "total": 6,  "available": 4,  "status": "ok"   },
            ],
            "isActive":         True,
            "avgResponseTime":  6.8,
            "createdAt":        now,
            "updatedAt":        now,
        },
    ]
    coll.insert_many(docs)
    print("  Seeded 3 Aurangabad hospitals")


def seed_ambulances(db):
    """Seed ambulance fleet."""
    coll = db["ambulances"]
    if coll.count_documents({}) > 0:
        print("  ambulances — already seeded, skipping")
        return

    docs = [
        {
            "vehicleNumber":     "MH-20-AA-0001",
            "callSign":          "AMB-01",
            "type":              "ICU",
            "status":            "available",
            "currentLocation":   { "lat": 19.8782, "lng": 75.3280 },
            "currentEmergencyId": None,
            "driverName":        "Ramesh Singh",
            "driverContact":     "+91-9876543210",
            "lastUpdated":       datetime.utcnow(),
        },
        {
            "vehicleNumber":     "MH-20-AA-0002",
            "callSign":          "AMB-02",
            "type":              "ALS",
            "status":            "available",
            "currentLocation":   { "lat": 19.8947, "lng": 75.3230 },
            "currentEmergencyId": None,
            "driverName":        "Suresh Yadav",
            "driverContact":     "+91-9876543211",
            "lastUpdated":       datetime.utcnow(),
        },
        {
            "vehicleNumber":     "MH-20-BB-0003",
            "callSign":          "AMB-03",
            "type":              "BLS",
            "status":            "available",
            "currentLocation":   { "lat": 19.8966, "lng": 75.3216 },
            "currentEmergencyId": None,
            "driverName":        "Vijay Kumar",
            "driverContact":     "+91-9876543212",
            "lastUpdated":       datetime.utcnow(),
        },
    ]
    coll.insert_many(docs)
    print("  Seeded 3 ambulances")


def seed_emergencies_patients(db):
    """Seed 2 completed emergencies with patients (historical)."""
    emergencies_coll = db["emergencies"]
    patients_coll    = db["patients"]
    dispatches_coll  = db["dispatches"]

    if emergencies_coll.count_documents({}) > 0:
        print("  emergencies / patients — already seeded, skipping")
        return

    admin    = db["users"].find_one({"username": "admin"})
    admin_id = admin["_id"]

    # ── Emergency 1 ──────────────────────────────────────────────────────────
    emerg1 = {
        "caseNumber":        "LLGCA-2026-0001",
        "status":            "completed",
        "emergencyType":     "Cardiac Arrest",
        "pickupLocation":    "Garkheda Parisar, Aurangabad",
        "pickupCoordinates": { "lat": 19.8735, "lng": 75.3340 },
        "assignedAmbulanceId": None,
        "assignedHospitalId":  None,
        "dispatchedAt":       None,
        "arrivedAt":           None,
        "completedAt":         None,
        "notes":              "Patient collapsed at home. CPR administered by family member.",
        "createdBy":          admin_id,
        "createdAt":          datetime.utcnow() - timedelta(hours=6),
        "updatedAt":          datetime.utcnow() - timedelta(hours=5),
    }
    emerg1_id = emergencies_coll.insert_one(emerg1).inserted_id

    hosp1 = db["hospitals"].find_one({"shortName": "MGM Hospital"})
    amb1  = db["ambulances"].find_one({"callSign": "AMB-01"})

    patient1 = {
        "emergencyId":    emerg1_id,
        "name":          "Vijay Malhotra",
        "age":           58,
        "gender":        "M",
        "contactNumber": "+91-9812345670",
        "vitals": {
            "conscious":         False,
            "breathingNormally": False,
            "severeBleeding":    False,
        },
        "pcsScore":  9,
        "aiAssessment": {
            "summary":                   "Critical cardiac event. Immediate ICU transfer required. High arrhythmia risk.",
            "recommendedHospitalType":    "Cardiac",
            "symptomScores": {
                "heartRate":       0,
                "bloodPressure":   0,
                "respRate":        3,
                "consciousness":   0,
                "bleeding":        7,
            },
            "assessedAt": datetime.utcnow() - timedelta(hours=5, minutes=55),
        },
        "status": "triaged",
    }
    patients_coll.insert_one(patient1)

    emergencies_coll.update_one({"_id": emerg1_id}, {"$set": {
        "assignedAmbulanceId": amb1["_id"],
        "assignedHospitalId":  hosp1["_id"],
        "dispatchedAt":       datetime.utcnow() - timedelta(hours=5, minutes=50),
        "arrivedAt":          datetime.utcnow() - timedelta(hours=5, minutes=40),
        "completedAt":        datetime.utcnow() - timedelta(hours=5),
    }})

    dispatches_coll.insert_many([
        {
            "emergencyId": emerg1_id,
            "ambulanceId":  amb1["_id"],
            "hospitalId":   hosp1["_id"],
            "action":       "dispatched",
            "timestamp":    datetime.utcnow() - timedelta(hours=5, minutes=50),
            "location":     { "lat": 19.8782, "lng": 75.3280 },
            "actor":        admin_id,
            "notes":        "Cardiac arrest — immediate dispatch",
        },
        {
            "emergencyId": emerg1_id,
            "ambulanceId":  amb1["_id"],
            "hospitalId":   hosp1["_id"],
            "action":       "en_route",
            "timestamp":    datetime.utcnow() - timedelta(hours=5, minutes=48),
            "location":     { "lat": 19.8830, "lng": 75.3420 },
            "actor":        None,
            "notes":        "Ambulance departed MGM Hospital",
        },
        {
            "emergencyId": emerg1_id,
            "ambulanceId":  amb1["_id"],
            "hospitalId":   hosp1["_id"],
            "action":       "scene_arrived",
            "timestamp":    datetime.utcnow() - timedelta(hours=5, minutes=40),
            "location":     { "lat": 19.8735, "lng": 75.3340 },
            "actor":        None,
            "notes":        "Arrived at scene — Garkheda",
        },
        {
            "emergencyId": emerg1_id,
            "ambulanceId":  amb1["_id"],
            "hospitalId":   hosp1["_id"],
            "action":       "hospital_arrived",
            "timestamp":    datetime.utcnow() - timedelta(hours=5, minutes=20),
            "location":     { "lat": 19.8782, "lng": 75.3280 },
            "actor":        None,
            "notes":        "Patient handed over at MGM Hospital",
        },
        {
            "emergencyId": emerg1_id,
            "ambulanceId":  amb1["_id"],
            "hospitalId":   hosp1["_id"],
            "action":       "completed",
            "timestamp":    datetime.utcnow() - timedelta(hours=5),
            "location":     { "lat": 19.8782, "lng": 75.3280 },
            "actor":        admin_id,
            "notes":        "Dispatch completed successfully",
        },
    ])

    db["greenCorridors"].insert_one({
        "emergencyId":          emerg1_id,
        "status":               "cleared",
        "route": [
            { "lat": 19.8735, "lng": 75.3340, "order": 0 },
            { "lat": 19.8782, "lng": 75.3280, "order": 1 },
        ],
        "distanceKm":          1.2,
        "signalsCleared":       4,
        "activationTime":      datetime.utcnow() - timedelta(hours=5, minutes=48),
        "clearedTime":         datetime.utcnow() - timedelta(hours=5, minutes=10),
        "timeSavedPercent":     44,
        "originLocation":      { "lat": 19.8735, "lng": 75.3340 },
        "destinationHospitalId": hosp1["_id"],
        "etaMinutes":          8,
    })

    # ── Emergency 2 ──────────────────────────────────────────────────────────
    emerg2 = {
        "caseNumber":        "LLGCA-2026-0002",
        "status":            "completed",
        "emergencyType":     "Road Accident",
        "pickupLocation":    "Beed Bypass Road, Aurangabad",
        "pickupCoordinates": { "lat": 19.8650, "lng": 75.3550 },
        "assignedAmbulanceId": None,
        "assignedHospitalId":  None,
        "dispatchedAt":       None,
        "arrivedAt":           None,
        "completedAt":         None,
        "notes":              "Two-wheeler collision. One critical, one moderate injury.",
        "createdBy":          admin_id,
        "createdAt":          datetime.utcnow() - timedelta(hours=2),
        "updatedAt":          datetime.utcnow() - timedelta(hours=1),
    }
    emerg2_id = emergencies_coll.insert_one(emerg2).inserted_id

    hosp2 = db["hospitals"].find_one({"shortName": "Oak Hospital"})
    amb2  = db["ambulances"].find_one({"callSign": "AMB-02"})

    patient2 = {
        "emergencyId":    emerg2_id,
        "name":          "Neeraj Singh",
        "age":           32,
        "gender":        "M",
        "contactNumber": "+91-9988776655",
        "vitals": {
            "conscious":         True,
            "breathingNormally": True,
            "severeBleeding":    True,
        },
        "pcsScore":  7,
        "aiAssessment": {
            "summary":                   "Moderate trauma with significant blood loss. Requires immediate surgical consult.",
            "recommendedHospitalType":    "Trauma",
            "symptomScores": {
                "heartRate":     5,
                "bloodPressure": 4,
                "respRate":      3,
                "consciousness":  7,
                "bleeding":      2,
            },
            "assessedAt": datetime.utcnow() - timedelta(hours=1, minutes=50),
        },
        "status": "triaged",
    }
    patients_coll.insert_one(patient2)

    emergencies_coll.update_one({"_id": emerg2_id}, {"$set": {
        "assignedAmbulanceId": amb2["_id"],
        "assignedHospitalId":  hosp2["_id"],
        "dispatchedAt":       datetime.utcnow() - timedelta(hours=1, minutes=55),
        "arrivedAt":          datetime.utcnow() - timedelta(hours=1, minutes=42),
        "completedAt":         datetime.utcnow() - timedelta(hours=1),
    }})

    db["greenCorridors"].insert_one({
        "emergencyId":           emerg2_id,
        "status":                "cleared",
        "route": [
            { "lat": 19.8650, "lng": 75.3550, "order": 0 },
            { "lat": 19.8947, "lng": 75.3230, "order": 1 },
        ],
        "distanceKm":           4.1,
        "signalsCleared":        6,
        "activationTime":       datetime.utcnow() - timedelta(hours=1, minutes=55),
        "clearedTime":          datetime.utcnow() - timedelta(hours=0, minutes=50),
        "timeSavedPercent":      40,
        "originLocation":       { "lat": 19.8650, "lng": 75.3550 },
        "destinationHospitalId": hosp2["_id"],
        "etaMinutes":           11,
    })

    print("  Seeded 2 completed emergencies with patients, dispatches, and corridors")


def seed_system_settings(db):
    """Seed default system configuration."""
    coll = db["systemSettings"]
    if coll.count_documents({}) > 0:
        print("  systemSettings — already seeded, skipping")
        return

    now = datetime.utcnow()
    docs = [
        { "key": "aiAssessmentEnabled",    "value": True,                                        "updatedAt": now },
        { "key": "autoGreenCorridor",       "value": True,                                        "updatedAt": now },
        { "key": "emailNotificationsEnabled","value": True,                                        "updatedAt": now },
        { "key": "liveMapTrackingEnabled",  "value": True,                                        "updatedAt": now },
        { "key": "networkRegion",           "value": "Aurangabad, Maharashtra",                       "updatedAt": now },
        { "key": "avgDispatchTimeMinutes",  "value": 1.8,                                         "updatedAt": now },
        { "key": "corridorTimeSavedPercent","value": 45,                                          "updatedAt": now },
        { "key": "cerebrasApiKey",          "value": "",                                          "updatedAt": now },
        { "key": "smtpEmail",                "value": "",                                          "updatedAt": now },
        { "key": "smtpPassword",             "value": "",                                         "updatedAt": now },
        { "key": "googleMapsKey",            "value": "",                                          "updatedAt": now },
        { "key": "tavilyApiKey",             "value": "",                                          "updatedAt": now },
    ]
    coll.insert_many(docs)
    print("  Seeded 12 system settings")


def seed_notifications(db):
    """Seed a couple of notification records from completed cases."""
    coll = db["notifications"]
    if coll.count_documents({}) > 0:
        print("  notifications — already seeded, skipping")
        return

    emerg1 = db["emergencies"].find_one({"caseNumber": "LLGCA-2026-0001"})
    emerg2 = db["emergencies"].find_one({"caseNumber": "LLGCA-2026-0002"})

    docs = [
        {
            "emergencyId":  emerg1["_id"],
            "type":        "hospital",
            "channel":     "email",
            "recipient":    "er.aiims@hospital.gov.in",
            "subject":      "[LLGCA] Critical Arrival — LLGCA-2026-0001",
            "body":        "Critical cardiac patient en route. ETA 18 min. Prepare ICU bed and cardiac team.",
            "status":      "sent",
            "sentAt":      datetime.utcnow() - timedelta(hours=5, minutes=45),
            "errorMessage": None,
        },
        {
            "emergencyId":  emerg1["_id"],
            "type":        "police",
            "channel":     "email",
            "recipient":    "traffic.delhi@police.gov.in",
            "subject":      "[LLGCA] Green Corridor Activated — Route NH-9",
            "body":        "Green corridor activated for emergency LLGCA-2026-0001. Request signal priority on corridor route.",
            "status":      "sent",
            "sentAt":      datetime.utcnow() - timedelta(hours=5, minutes=48),
            "errorMessage": None,
        },
        {
            "emergencyId":  emerg2["_id"],
            "type":        "hospital",
            "channel":     "email",
            "recipient":    "emergency.fortis@fortis.in",
            "subject":      "[LLGCA] Trauma Arrival — LLGCA-2026-0002",
            "body":        "Road accident trauma case en route. ETA 12 min. Prepare surgical team.",
            "status":      "sent",
            "sentAt":      datetime.utcnow() - timedelta(hours=1, minutes=50),
            "errorMessage": None,
        },
    ]
    coll.insert_many(docs)
    print("  Seeded 3 notifications")


def seed_audit_logs(db):
    """Seed login audit trail."""
    coll = db["auditLogs"]
    if coll.count_documents({}) > 0:
        print("  auditLogs — already seeded, skipping")
        return

    admin     = db["users"].find_one({"username": "admin"})
    dispatcher = db["users"].find_one({"username": "dispatcher1"})

    docs = [
        {
            "userId":     dispatcher["_id"],
            "action":     "login",
            "details":    {"method": "password"},
            "ipAddress":  "10.0.0.45",
            "userAgent":  "Chrome/120 / Windows",
            "timestamp":  datetime.utcnow() - timedelta(hours=8),
        },
        {
            "userId":     admin["_id"],
            "action":     "login",
            "details":    {"method": "password"},
            "ipAddress":  "10.0.0.10",
            "userAgent":  "Chrome/120 / Windows",
            "timestamp":  datetime.utcnow() - timedelta(hours=7),
        },
        {
            "userId":     admin["_id"],
            "action":     "create_emergency",
            "details":    {"caseNumber": "LLGCA-2026-0001", "emergencyType": "Cardiac Arrest"},
            "ipAddress":  "10.0.0.10",
            "userAgent":  "Chrome/120 / Windows",
            "timestamp":  datetime.utcnow() - timedelta(hours=6),
        },
        {
            "userId":     admin["_id"],
            "action":     "dispatch",
            "details":    {"caseNumber": "LLGCA-2026-0001", "ambulance": "AMB-01", "hospital": "AIIMS"},
            "ipAddress":  "10.0.0.10",
            "userAgent":  "Chrome/120 / Windows",
            "timestamp":  datetime.utcnow() - timedelta(hours=5, minutes=50),
        },
    ]
    coll.insert_many(docs)
    print("  Seeded 4 audit log entries")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n=== LLGCA Database Setup ===\n")

    client = get_client()
    db = client[DB_NAME]

    print(f"[1/6] Creating collections...")
    create_collections(db)

    print(f"\n[2/6] Creating indexes...")
    create_indexes(db)

    print(f"\n[3/6] Seeding users...")
    seed_users(db)

    print(f"\n[4/6] Seeding hospitals...")
    seed_hospitals(db)

    print(f"\n[5/6] Seeding ambulances...")
    seed_ambulances(db)

    print(f"\n[6/6] Seeding reference / historical data...")
    seed_emergencies_patients(db)
    seed_system_settings(db)
    seed_notifications(db)
    seed_audit_logs(db)

    print(f"\n✅ Setup complete! Database: '{DB_NAME}'")
    print(f"   Connect string: {MONGO_URI.split('@')[1] if '@' in MONGO_URI else MONGO_URI}")
    print(f"\nDummy login credentials:")
    print(f"   admin / admin123      (role: admin)")
    print(f"   dispatcher1 / dispatch123  (role: operator)")
    print(f"   viewer / viewer123    (role: viewer)")

    client.close()


if __name__ == "__main__":
    main()
