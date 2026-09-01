const BASE = "http://localhost:8001/api";

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.error(`API Error for ${path}:`, err);
    return fallback;
  }
}

async function post<T>(path: string, body?: any): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.error(`API Error for POST ${path}:`, err);
    throw err;
  }
}

// ============== Auth ==============
export interface LoginRequest {
  email: string;
  password: string;
  role: string;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: { email: string; name: string; role: string };
  message: string;
}

export const postLogin = (data: LoginRequest) => post<LoginResponse>("/login", data);

// ============== Dashboard ==============
export interface DashboardStats {
  total_routes: number;
  active_buses: number;
  high_demand_routes: number;
  anomalies: number;
  avg_load_factor: number;
  avg_demand: number;
}

export interface DashboardData {
  stats: DashboardStats;
  demand: { time: string; demand: number }[];
  load: { route: string; load: number }[];
  alerts: Alert[];
}

export const getDashboard = () => get<DashboardData>("/dashboard", {
  stats: { total_routes: 0, active_buses: 0, high_demand_routes: 0, anomalies: 0, avg_load_factor: 0, avg_demand: 0 },
  demand: [],
  load: [],
  alerts: []
});

// ============== Routes ==============
export interface Route {
  id: string;
  demand: number;
  load_factor: number;
  status: string;
}

export const getRoutes = () => get<Route[]>("/routes", []);

// ============== Route Detail ==============
export interface RouteDetail {
  demand_trend: { time: string; demand: number }[];
  load_trend: { time: string; load: number }[];
  confidence: number;
  recommendations: {
    frequency_multiplier: string;
    buses_to_add: string;
    reroute_suggestion: string;
  };
  action_badges: { label: string; color: string }[];
}

export const getRoute = (id: string) => get<RouteDetail>(`/route/${id}`, {
  demand_trend: [],
  load_trend: [],
  confidence: 0,
  recommendations: { frequency_multiplier: "1.0x", buses_to_add: "0", reroute_suggestion: "No data" },
  action_badges: []
});

// ============== Optimization ==============
export interface OptimizeResponse {
  success: boolean;
  message: string;
  summary: {
    total_routes: number;
    routes_with_actions: number;
    total_buses_added: number;
    anomalies_detected: number;
    high_uncertainty_routes: number;
  };
  timestamp: string;
}

export const postOptimize = () => post<OptimizeResponse>("/optimize");

// ============== Results ==============
export interface OptimizationResult {
  route_id: number;
  demand_after: number;
  waiting_passengers: number;
  actions: string[];
  frequency_multiplier: number;
  buses_added: number;
  rerouted_to: number | null;
  anomaly: boolean;
  high_uncertainty: boolean;
}

export const getResults = () => get<OptimizationResult[]>("/results", []);

// ============== Alerts ==============
export interface Alert {
  id: number;
  route: string;
  message: string;
  severity: string;
  time: string;
}

export const getAlerts = () => get<Alert[]>("/alerts", []);

export interface SimulationSummary {
  total_routes: number;
  routes_with_actions: number;
  total_buses_added: number;
  avg_frequency: number;
  avg_waiting: number;
  critical_routes: number;
}

export const getSimulationSummary = async (): Promise<SimulationSummary> => {
  const results = await getResults();
  if (!results || results.length === 0) {
    return {
      total_routes: 0,
      routes_with_actions: 0,
      total_buses_added: 0,
      avg_frequency: 0,
      avg_waiting: 0,
      critical_routes: 0
    };
  }
  
  return {
    total_routes: results.length,
    routes_with_actions: results.filter(r => r.actions.length > 0 && !r.actions.includes("No action")).length,
    total_buses_added: results.reduce((sum, r) => sum + r.buses_added, 0),
    avg_frequency: parseFloat((results.reduce((sum, r) => sum + r.frequency_multiplier, 0) / results.length).toFixed(2)),
    avg_waiting: results.reduce((sum, r) => sum + r.waiting_passengers, 0) / results.length,
    critical_routes: results.filter(r => r.waiting_passengers > 5000).length
  };
};