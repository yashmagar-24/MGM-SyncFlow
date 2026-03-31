import type { Request, Response } from "express";
import { runSimulation } from "../services/simulation/simulationEngine";
import { hospitals } from "../routes/hospitalRoutes";
import type { OrganDispatchRequest } from "../models/OrganDispatch";
import type { PatientDispatchRequest } from "../models/PatientDispatch";

function generateTrackingId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;
}

function pickRandomSource(excludeId: string): typeof hospitals[number] {
  const others = hospitals.filter((h) => h.id !== excludeId);
  return others[Math.floor(Math.random() * others.length)];
}

function findHospitalByName(name: string): typeof hospitals[number] | undefined {
  const lower = name.toLowerCase();
  return hospitals.find(
    (h) =>
      h.name.toLowerCase().includes(lower) ||
      lower.includes(h.name.toLowerCase().slice(0, 10)),
  );
}

export const dispatchOrgan = async (req: Request, res: Response): Promise<void> => {
  const { organType, bloodGroup, donorId, destinationHospital, urgencyLevel, notes } =
    req.body as OrganDispatchRequest;

  if (!organType || !bloodGroup || !destinationHospital) {
    res.status(400).json({ message: "organType, bloodGroup, and destinationHospital are required" });
    return;
  }

  const dest = findHospitalByName(destinationHospital);
  if (!dest) {
    res.status(404).json({ message: `Hospital not found: ${destinationHospital}` });
    return;
  }

  const source = pickRandomSource(dest.id);

  try {
    const result = await runSimulation(
      [source.lat, source.lng],
      [dest.lat, dest.lng],
    );

    const dispatch = {
      trackingId: generateTrackingId("ORG"),
      dispatchedAt: new Date().toISOString(),
      destinationHospital: dest.name,
      destinationLat: dest.lat,
      destinationLng: dest.lng,
      organType,
      bloodGroup,
      donorId: donorId || "",
      urgencyLevel: urgencyLevel || "medium",
      notes: notes || "",
      route: result.route,
      estimatedDurationSeconds: Math.round(result.logs.find((l) => l.data?.duration)?.data?.duration as number ?? 300),
      status: "DISPATCHED" as const,
      // CCTV and routing data for map visualization
      routes: result.routes,
      cctvs: result.cctvs,
      waypoints: result.waypoints,
      bestRouteIndex: result.bestRouteIndex,
      violations: result.violations,
    };

    res.json(dispatch);
  } catch (err) {
    console.error("Organ dispatch error:", err);
    res.status(500).json({ message: "Dispatch failed", details: String(err) });
  }
};

export const dispatchPatient = async (req: Request, res: Response): Promise<void> => {
  const {
    patientName,
    patientId,
    age,
    bloodGroup,
    condition,
    destinationHospital,
    ambulanceId,
    requiredDepartment,
    notes,
  } = req.body as PatientDispatchRequest;

  if (!patientName || !destinationHospital || !ambulanceId) {
    res.status(400).json({
      message: "patientName, destinationHospital, and ambulanceId are required",
    });
    return;
  }

  const dest = findHospitalByName(destinationHospital);
  if (!dest) {
    res.status(404).json({ message: `Hospital not found: ${destinationHospital}` });
    return;
  }

  const source = pickRandomSource(dest.id);

  try {
    const result = await runSimulation(
      [source.lat, source.lng],
      [dest.lat, dest.lng],
    );

    const dispatch = {
      trackingId: generateTrackingId("PAT"),
      dispatchedAt: new Date().toISOString(),
      destinationHospital: dest.name,
      destinationLat: dest.lat,
      destinationLng: dest.lng,
      patientName,
      patientId: patientId || "",
      age: Number(age) || 0,
      bloodGroup: bloodGroup || "",
      condition: condition || "Stable",
      ambulanceId,
      requiredDepartment: requiredDepartment || "Emergency",
      notes: notes || "",
      route: result.route,
      estimatedDurationSeconds: Math.round(result.logs.find((l) => l.data?.duration)?.data?.duration as number ?? 300),
      status: "DISPATCHED" as const,
      // CCTV and routing data for map visualization
      routes: result.routes,
      cctvs: result.cctvs,
      waypoints: result.waypoints,
      bestRouteIndex: result.bestRouteIndex,
      violations: result.violations,
    };

    res.json(dispatch);
  } catch (err) {
    console.error("Patient dispatch error:", err);
    res.status(500).json({ message: "Dispatch failed", details: String(err) });
  }
};
