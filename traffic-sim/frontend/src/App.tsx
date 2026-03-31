import { useRef, useState, useEffect } from "react";
import MapView from "./components/MapView.jsx";
import ControlPanel from "./components/ControlPanel.jsx";
import LogsPanel from "./components/LogsPanel.jsx";
import {
  getHospitals,
  startSimulation,
  type Hospital,
  type CCTVNode,
  type EventLog,
  type SimulationWaypoints,
  type ViolationEvent,
  type RouteWithCCTVs,
} from "./services/api";

type LatLng = [number, number];
const AMBULANCE_ANIMATION_INTERVAL_MS = 300;
const CCTV_HIGHLIGHT_DISTANCE_METERS = 50;

function metersBetween(a: LatLng, b: LatLng): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]) * 111000;
}

function findNearestCCTV(pos: LatLng, cctvs: CCTVNode[]): string | null {
  if (!pos || cctvs.length === 0) return null;
  let nearest: string | null = null;
  let minDist = Infinity;
  for (const cctv of cctvs) {
    const dist = metersBetween(pos, [cctv.lat, cctv.lng]);
    if (dist < minDist && dist < CCTV_HIGHLIGHT_DISTANCE_METERS) {
      minDist = dist;
      nearest = cctv.id;
    }
  }
  return nearest;
}

function App() {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [route, setRoute] = useState<LatLng[]>([]);
  const [allRoutes, setAllRoutes] = useState<RouteWithCCTVs[]>([]);
  const [shortestRouteIndex, setShortestRouteIndex] = useState<number | null>(null);
  const [ambulancePos, setAmbulancePos] = useState<LatLng | null>(null);
  const [activeCCTVId, setActiveCCTVId] = useState<string | null>(null);
  const [violations, setViolations] = useState<ViolationEvent[]>([]);
  const [logs, setLogs] = useState<EventLog[]>([]);
  const [waypoints, setWaypoints] = useState<SimulationWaypoints | null>(null);
  const [loading, setLoading] = useState(false);

  // Refs to avoid stale closures in animation intervals
  const allRoutesRef = useRef<RouteWithCCTVs[]>([]);
  const shortestRouteIndexRef = useRef<number | null>(null);

  // CCTV nodes from the best route — used for proximity highlighting
  const bestRouteCCTVs = shortestRouteIndex !== null ? (allRoutes[shortestRouteIndex]?.cctvs ?? []) : [];

  const animationRef = useRef<number | null>(null);

  // Fetch hospitals from backend on mount
  useEffect(() => {
    getHospitals()
      .then(setHospitals)
      .catch((err) => console.error("Failed to fetch hospitals:", err));
  }, []);

  const simulate = async () => {
    if (hospitals.length < 3) {
      console.error("Not enough hospitals available");
      return;
    }

    const source = hospitals[2];
    const destination = hospitals[1];

    setLoading(true);

    try {
      if (animationRef.current !== null) {
        clearInterval(animationRef.current);
        animationRef.current = null;
      }

      const result = await startSimulation(source, destination);

      // Sync refs first so the interval callback sees current data
      allRoutesRef.current = result.routes || [];
      shortestRouteIndexRef.current = result.bestRouteIndex ?? null;

      // Use backend's best route for ambulance animation
      setRoute(result.route);
      setAllRoutes(result.routes || []);
      setShortestRouteIndex(result.bestRouteIndex ?? null);
      setViolations(result.violations || []);
      setLogs(result.logs || []);
      setWaypoints(result.waypoints || null);
      setAmbulancePos(result.route[0]);

      // Ambulance animation along the route
      let i = 0;
      animationRef.current = window.setInterval(() => {
        const currentBestRouteCCTVs =
          shortestRouteIndexRef.current !== null
            ? (allRoutesRef.current[shortestRouteIndexRef.current]?.cctvs ?? [])
            : [];
        const pos = result.route[i];
        setAmbulancePos(pos);
        setActiveCCTVId(findNearestCCTV(pos, currentBestRouteCCTVs));
        i++;

        if (i >= result.route.length && animationRef.current !== null) {
          clearInterval(animationRef.current);
          animationRef.current = null;
        }
      }, AMBULANCE_ANIMATION_INTERVAL_MS);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOrganDispatch = (result: any) => {
    if (animationRef.current !== null) {
      clearInterval(animationRef.current);
      animationRef.current = null;
    }

    const logs: EventLog[] = [
      {
        id: `log-${Date.now()}-1`,
        timestamp: new Date(),
        event: "AMBULANCE_DISPATCHED",
        message: `🚑 Organ dispatch: ${result.organType} to ${result.destinationHospital}`,
        data: { trackingId: result.trackingId, urgency: result.urgencyLevel },
      },
      {
        id: `log-${Date.now()}-2`,
        timestamp: new Date(),
        event: "HOSPITAL_ALERTED",
        message: `🏥 Destination: ${result.destinationHospital}`,
      },
      {
        id: `log-${Date.now()}-3`,
        timestamp: new Date(),
        event: "SIMULATION_END",
        message: "✅ Organ delivery dispatched",
      },
    ];

    // Sync refs first so the interval callback sees current data
    allRoutesRef.current = result.routes || [];
    shortestRouteIndexRef.current = result.bestRouteIndex ?? null;

    setRoute(result.route || []);
    setAllRoutes(result.routes || []);
    setShortestRouteIndex(result.bestRouteIndex ?? null);
    setViolations(result.violations || []);
    setLogs(logs);
    setWaypoints(result.waypoints || null);
    setActiveCCTVId(null);
    setAmbulancePos((result.route && result.route[0]) || null);

    // Ambulance animation along the route
    if (result.route && result.route.length > 0) {
      let i = 0;
      animationRef.current = window.setInterval(() => {
        const currentBestRouteCCTVs =
          shortestRouteIndexRef.current !== null
            ? (allRoutesRef.current[shortestRouteIndexRef.current]?.cctvs ?? [])
            : [];
        const pos = result.route[i];
        setAmbulancePos(pos);
        setActiveCCTVId(findNearestCCTV(pos, currentBestRouteCCTVs));
        i++;
        if (i >= result.route.length && animationRef.current !== null) {
          clearInterval(animationRef.current);
          animationRef.current = null;
        }
      }, AMBULANCE_ANIMATION_INTERVAL_MS);
    }
  };

  const handlePatientDispatch = (result: any) => {
    if (animationRef.current !== null) {
      clearInterval(animationRef.current);
      animationRef.current = null;
    }

    const logs: EventLog[] = [
      {
        id: `log-${Date.now()}-1`,
        timestamp: new Date(),
        event: "AMBULANCE_DISPATCHED",
        message: `🚑 Patient dispatch: ${result.patientName} to ${result.destinationHospital}`,
        data: { trackingId: result.trackingId, ambulanceId: result.ambulanceId },
      },
      {
        id: `log-${Date.now()}-2`,
        timestamp: new Date(),
        event: "HOSPITAL_ALERTED",
        message: `🏥 Destination: ${result.destinationHospital} | Dept: ${result.requiredDepartment}`,
      },
      {
        id: `log-${Date.now()}-3`,
        timestamp: new Date(),
        event: "SIMULATION_END",
        message: "✅ Patient transport dispatched",
      },
    ];

    // Sync refs first so the interval callback sees current data
    allRoutesRef.current = result.routes || [];
    shortestRouteIndexRef.current = result.bestRouteIndex ?? null;

    setRoute(result.route || []);
    setAllRoutes(result.routes || []);
    setShortestRouteIndex(result.bestRouteIndex ?? null);
    setViolations(result.violations || []);
    setLogs(logs);
    setWaypoints(result.waypoints || null);
    setActiveCCTVId(null);
    setAmbulancePos((result.route && result.route[0]) || null);

    // Ambulance animation along the route
    if (result.route && result.route.length > 0) {
      let i = 0;
      animationRef.current = window.setInterval(() => {
        const currentBestRouteCCTVs =
          shortestRouteIndexRef.current !== null
            ? (allRoutesRef.current[shortestRouteIndexRef.current]?.cctvs ?? [])
            : [];
        const pos = result.route[i];
        setAmbulancePos(pos);
        setActiveCCTVId(findNearestCCTV(pos, currentBestRouteCCTVs));
        i++;
        if (i >= result.route.length && animationRef.current !== null) {
          clearInterval(animationRef.current);
          animationRef.current = null;
        }
      }, AMBULANCE_ANIMATION_INTERVAL_MS);
    }
  };

  return (
    <div className="app-shell">
      <section className="map-pane">
        <ControlPanel onSimulate={simulate} onOrganDispatch={handleOrganDispatch} onPatientDispatch={handlePatientDispatch} loading={loading} />

        <MapView
          hospitals={hospitals}
          route={route}
          allRoutes={allRoutes}
          shortestRouteIndex={shortestRouteIndex}
          ambulancePos={ambulancePos}
          activeCCTVId={activeCCTVId}
          bestRouteCCTVs={bestRouteCCTVs}
        />
      </section>

      <section className="logs-pane">
        <LogsPanel logs={logs} waypoints={waypoints} violations={violations} loading={loading} />
      </section>
    </div>
  );
}

export default App;
