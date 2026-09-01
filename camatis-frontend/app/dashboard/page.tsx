"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import StatsCards from "@/components/dashboard/StatsCards";
import DemandChart from "@/components/dashboard/DemandChart";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import { postOptimize, getDashboard, getResults } from "@/lib/api";

export default function DashboardPage() {
  const [optimizing, setOptimizing] = useState(false);
  const [msg, setMsg] = useState("");
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [realBuses, setRealBuses] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch real data
    Promise.all([getDashboard(), getResults()]).then(([dashboard, results]) => {
      // Calculate REAL active buses from results
      const totalBuses = (results as any[]).reduce((sum, r) => sum + (r.buses_added || 0), 0) + (results?.length || 0);
      setRealBuses(totalBuses);
      setDashboardData(dashboard);
      setLoading(false);
    });
  }, []);

  const handleOptimize = async () => {
    setOptimizing(true);
    setMsg("");
    try {
      const res = await postOptimize();
      setMsg(res?.message ?? "Optimization complete");
      // Refresh data
      const [dashboard, results] = await Promise.all([getDashboard(), getResults()]);
      const totalBuses = (results as any[]).reduce((sum, r) => sum + (r.buses_added || 0), 0) + (results?.length || 0);
      setRealBuses(totalBuses);
      setDashboardData(dashboard);
    } catch (err) {
      setMsg("Optimization failed");
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8">
          <p>Loading dashboard...</p>
        </main>
      </div>
    );
  }
  const highDemandRoutes = (dashboardData?.stats?.high_demand_routes || 0);


  // Override stats with real data
  const realStats = dashboardData?.stats ? {
    ...dashboardData.stats,
    active_buses: realBuses,  // Use REAL bus count
    high_demand_routes: dashboardData.stats.high_demand_routes || 0
  } : null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {optimizing ? "Running..." : "Run Optimization"}
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-2">
          Real-time overview of the transit network
        </p>
        {msg && <p className="text-sm text-green-600 mb-4">{msg}</p>}

        
        <StatsCards stats={{
          total_routes: dashboardData?.stats?.total_routes || 0,
          active_buses: realBuses,
          high_demand_routes: highDemandRoutes,
          anomalies: dashboardData?.stats?.anomalies || 0,
          avg_load_factor: dashboardData?.stats?.avg_load_factor || 0,
          avg_demand: dashboardData?.stats?.avg_demand || 0
        }} />
        
        
        <div className="mb-8">
          <DemandChart 
            demandData={dashboardData?.demand || []} 
            loadData={dashboardData?.load || []} 
          />
        </div>
        
        <AlertsPanel alerts={dashboardData?.alerts || []} />
      </main>
    </div>
  );
}