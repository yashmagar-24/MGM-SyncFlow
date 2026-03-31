# 🚑 AI-Powered Green Corridor System

> A real-time traffic orchestration system that automates green corridor creation for emergency vehicles using CCTV-based tracking, graph-based routing, and dynamic signal control.

---

## 📌 Table of Contents

* Overview
* Problem Statement
* System Concept
* How the System Works
* Architecture
* Core Modules
* Simulation Approach
* Tech Stack
* Project Structure
* Features
* Design Decisions
* Limitations
* Future Scope
* Conclusion

---

## 🧠 Overview

Urban traffic systems are not designed to adapt to emergency scenarios in real time. Even though green corridors exist, they rely heavily on manual coordination between hospitals, traffic police, and control centers.

This project proposes an **automated, AI-driven system** that eliminates manual delays by:

* Taking **verified hospital requests**
* Computing optimal routes using a **graph-based model**
* Tracking ambulance movement via **CCTV nodes**
* Dynamically controlling signals using a **rolling corridor strategy**

---

## 🚨 Problem Statement

Current emergency traffic management faces several limitations:

* 🚫 Traffic signals operate on static timing
* 🚫 Green corridors are manually coordinated
* 🚫 No real-time tracking of ambulance movement
* 🚫 Delays significantly impact critical transport (e.g., organ transfer)

---

## 💡 System Concept

The system is designed as an **event-driven orchestration pipeline**, where:

* Inputs are received from hospitals
* CCTV nodes act as distributed sensing points
* A central decision engine manages traffic signals

> The key idea is to **separate perception (detection) from decision-making (control)**.

---

## ⚙️ How the System Works

```text
Hospital Request
      ↓
Route Calculation (Graph)
      ↓
CCTV-Based Tracking
      ↓
Dual Verification
      ↓
Decision Engine
      ↓
Rolling Green Corridor
      ↓
Traffic Signal Control
```

---

## 🏗️ System Architecture

### 1. Input Layer

* Hospital-initiated emergency request
* Optional: CCTV / model outputs

---

### 2. Routing Layer

* City modeled as a graph
* Nodes = CCTV intersections
* Edges = roads

Shortest path is computed using algorithms like:

* A* (preferred)
* BFS (for simulation)

---

### 3. Perception Layer

* Each CCTV node runs the same detection logic
* Detects ambulance presence

Example output:

```json
{
  "cctv_id": "S7",
  "ambulance": true,
  "confidence": 0.93
}
```

---

### 4. Verification Layer

To ensure reliability, the system uses **dual validation**:

* Hospital request (trusted source)
* Sequential CCTV detections

This prevents:

* False triggers
* Random activations

---

### 5. Decision Engine

The core brain of the system:

* Controls signal states
* Activates emergency mode
* Handles route updates

---

### 6. Rolling Green Corridor

Instead of activating all signals:

* Only **current + next intersections** are green
* Corridor moves dynamically with ambulance

Example:

```text
Route: S3 → S7 → S9 → S12

At S7:
GREEN → S7, S9
RED → others
```

---

### 7. Output Layer

* Real-time signal updates
* Event logs
* Dashboard visualization

---

## 🖥️ Command Center Dashboard

### Layout:

* **Left (70%)** → 4×4 CCTV grid
* **Right (30%)** → control panel

---

### Features:

* CCTV status (Normal / Traffic / Emergency)
* Route tracking (node-by-node)
* Event logs (real-time updates)
* Active request information

---

## 🧪 Simulation Approach

Since real-world infrastructure is not available:

* CCTV feeds are simulated as **event streams**
* Ambulance movement is modeled as **graph traversal**
* Signal updates are computed in real time

> This allows accurate representation of system behavior without relying on external hardware.

---

## 🛠️ Tech Stack

### Backend

* Python
* FastAPI
* WebSockets

### Frontend

* React.js
* Tailwind CSS

### AI Models

* CNN (Ambulance detection)
* Optional: traffic density classification

---

## 📂 Project Structure

```text
backend/
│
├── main.py
├── state.py
│
├── engine/
│   ├── dispatch.py
│   ├── routing.py
│   ├── decision.py
│   ├── events.py
│
├── cctv/
│   ├── simulator.py
│   ├── processor.py
│
├── api/
│   ├── routes.py
│   ├── websocket.py
│
frontend/
│
├── components/
│   ├── CCTVGrid.jsx
│   ├── CCTVCard.jsx
│   ├── SidePanel.jsx
│   ├── RouteTracker.jsx
│   ├── EventLog.jsx
│
├── pages/
│   ├── Dashboard.jsx
```

---

## 🚀 Key Features

* Automated green corridor activation
* Graph-based route computation
* CCTV-based ambulance tracking
* Rolling traffic signal control
* Real-time dashboard visualization
* Event-driven architecture

---

## 🧠 Design Decisions

* Focused on **system orchestration**, not just ML models
* Used simulation to ensure **reliable demo execution**
* Separated:

  * perception (CNN)
  * decision-making (logic engine)

---

## ⚠️ Limitations

* Uses simulated CCTV inputs
* No integration with real traffic signal hardware
* AI models are not deployed in real-time video pipeline

---

## 🔮 Future Scope

* Real CCTV integration
* GPS + CCTV fusion
* Smart signal hardware integration
* Multi-ambulance conflict handling
* Automated accident detection
* Vehicle violation detection (ANPR)

---

## 🏆 Conclusion

This project demonstrates how **real-time traffic systems can be automated using AI and event-driven design**.

Rather than focusing only on detection, it emphasizes:

> **intelligent coordination, scalability, and real-world applicability**

---

## 👨‍💻 Authors

* Team 405 Found