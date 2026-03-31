// api.ts — Traffic-Sim Frontend API Service

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

// ─── Helper ───────────────────────────────────────────────────────────────────

async function post<T>(endpoint: string, body: object): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({} as Record<string, unknown>));
    const message =
      (typeof err.message === "string" && err.message) ||
      (typeof err.error === "string" && err.error) ||
      `Request failed: ${res.status}`;
    const details = typeof err.details === "string" ? err.details : "";
    throw new Error(details ? `${message} (${details})` : message);
  }
  return res.json();
}

async function get<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Hospital {
  id: string;
  name: string;
  location: string;
  lat: number;
  lng: number;
}

export interface OrganPayload {
  organType: string;
  bloodGroup: string;
  donorId: string;
  destinationHospital: string;
  urgencyLevel: "low" | "medium" | "high" | "critical";
  notes?: string;
}

export interface OrganResponse {
  success: boolean;
  message: string;
  trackingId: string;
  dispatchedAt: string;
  destinationHospital: string;
  organType: string;
  route: LatLng[];
  routes: RouteWithCCTVs[];
  cctvs: CCTVNode[];
  waypoints: SimulationWaypoints | null;
  bestRouteIndex: number;
  violations: ViolationEvent[];
}

export interface PatientPayload {
  patientName: string;
  patientId: string;
  age: number;
  bloodGroup: string;
  condition: string;
  destinationHospital: string;
  ambulanceId: string;
  requiredDepartment: string;
  notes?: string;
}

export interface PatientResponse {
  success: boolean;
  message: string;
  trackingId: string;
  dispatchedAt: string;
  destinationHospital: string;
  patientName: string;
  ambulanceId: string;
  route: LatLng[];
  routes: RouteWithCCTVs[];
  cctvs: CCTVNode[];
  waypoints: SimulationWaypoints | null;
  bestRouteIndex: number;
  violations: ViolationEvent[];
}

export type LatLng = [number, number];

export interface CCTVNode {
  id: string;
  lat: number;
  lng: number;
  status: "IDLE" | "TRACKING" | "VIOLATION" | "OFFLINE";
  lastUpdate?: string | Date;
  assignedRouteId?: string;
  routeIndex?: number;
  pathIndex?: number;
  turnAngleDeg?: number;
  intersectionValidated?: boolean;
}

export interface EventLog {
  id: string;
  timestamp: string | Date;
  event: string;
  message: string;
  data?: Record<string, unknown>;
}

export interface ViolationEvent {
  type: "VIOLATION";
  plate: string;
  timestamp: string | Date;
  cctvId: string;
  lat: number;
  lng: number;
}

export interface WaypointNode {
  index: number;
  cctvId: string;
  coordinates: LatLng;
}

export interface SimulationWaypoints {
  source: WaypointNode;
  intermediate: WaypointNode[];
  destination: WaypointNode;
}

export interface RouteWithCCTVs {
  index: number;
  path: LatLng[];
  distance: number;
  duration: number;
  score: number;
  isBest: boolean;
  cctvs: CCTVNode[];
}

export interface SimulationResult {
  route: LatLng[];
  cctvs: CCTVNode[];
  logs: EventLog[];
  waypoints: SimulationWaypoints | null;
  routes: RouteWithCCTVs[];
  bestRouteIndex: number;
  violations: ViolationEvent[];
}

export interface SimulationResponse {
  success: boolean;
  message: string;
  simulationId: string;
  startedAt: string;
}

// ─── API Functions ────────────────────────────────────────────────────────────

/**
 * GET /hospitals
 * Fetches list of all available hospitals
 */
export async function getHospitals(): Promise<Hospital[]> {
  return get<Hospital[]>("/api/hospitals");
}

/**
 * POST /start-simulation
 * Starts the traffic simulation
 */
export async function startSimulation(
  source: Hospital,
  destination: Hospital
): Promise<SimulationResult> {
  return post<SimulationResult>("/api/simulation/start", {
    source: [source.lat, source.lng],
    destination: [destination.lat, destination.lng],
  });
}

/**
 * POST /send-organ
 * Dispatches an organ to a specified hospital
 */
export async function sendOrgan(payload: OrganPayload): Promise<OrganResponse> {
  return post<OrganResponse>("/api/dispatch/organ", payload);
}

/**
 * POST /send-patient
 * Dispatches a patient to a specified hospital via ambulance
 */
export async function sendPatient(payload: PatientPayload): Promise<PatientResponse> {
  return post<PatientResponse>("/api/dispatch/patient", payload);
}