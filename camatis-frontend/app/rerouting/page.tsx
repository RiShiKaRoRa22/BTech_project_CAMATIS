"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { getResults } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ArrowRight, Bus, TrendingDown, TrendingUp } from "lucide-react";

interface OptimizationResult {
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

interface RerouteImpact {
  from_route: number;
  to_route: number;
  demand_shift: number;
  capacity_change: number;
}

export default function ReroutingPage() {
  const [reroutes, setReroutes] = useState<RerouteImpact[]>([]);
  const [loading, setLoading] = useState(true);
  const [targetCounts, setTargetCounts] = useState<Map<number, number>>(new Map());
  const [totalCapacityShift, setTotalCapacityShift] = useState(0);

  useEffect(() => {
    getResults().then((data) => {
      const results = data as OptimizationResult[];
      
      // Extract rerouting relationships
      const rerouteMap = new Map<string, RerouteImpact>();
      const targets = new Map<number, number>();
      let totalCapShift = 0;
      
      results.forEach(r => {
        if (r.rerouted_to && r.rerouted_to !== null && r.demand_after) {
          const key = `${r.route_id}->${r.rerouted_to}`;
          if (!rerouteMap.has(key)) {
            // Calculate approximate demand shift (15% of demand after)
            const demandShift = r.demand_after * 0.15;
            // Calculate capacity change (1 bus = 50 capacity * 4 frequency = 200)
            const capacityChange = 200;
            
            rerouteMap.set(key, {
              from_route: r.route_id,
              to_route: r.rerouted_to,
              demand_shift: demandShift,
              capacity_change: capacityChange
            });
            
            // Count how many routes reroute to each target
            targets.set(r.rerouted_to, (targets.get(r.rerouted_to) || 0) + 1);
            totalCapShift += capacityChange;
          }
        }
      });
      
      setReroutes(Array.from(rerouteMap.values()));
      setTargetCounts(targets);
      setTotalCapacityShift(totalCapShift);
      setLoading(false);
    });
  }, []);

  // Calculate statistics
  const routesLosingBuses = reroutes.length;
  const routesGainingBuses = targetCounts.size;
  const mostPopularTarget = Array.from(targetCounts.entries()).sort((a, b) => b[1] - a[1])[0];
  const targetNames = Array.from(targetCounts.keys()).join(", ");

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800">Rerouting Impact</h1>
          <p className="text-sm text-slate-500">Bus movements and demand shifts between routes</p>
        </div>

        {loading ? (
          <p className="text-slate-400">Loading rerouting data...</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Rerouting Flow */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Bus Rerouting Flow</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {reroutes.length === 0 ? (
                    <p className="text-sm text-slate-400 text-center py-8">No rerouting decisions applied</p>
                  ) : (
                    reroutes.map((reroute, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                            <span className="text-xs font-bold text-red-600">{reroute.from_route}</span>
                          </div>
                          <ArrowRight size={16} className="text-slate-400" />
                          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                            <span className="text-xs font-bold text-green-600">{reroute.to_route}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1 text-amber-600">
                            <Bus size={14} />
                            <span className="text-sm">+1 bus</span>
                          </div>
                          <div className="flex items-center gap-1 text-red-500">
                            <TrendingDown size={14} />
                            <span className="text-sm">-{Math.round(reroute.demand_shift)} demand</span>
                          </div>
                          <div className="flex items-center gap-1 text-green-500">
                            <TrendingUp size={14} />
                            <span className="text-sm">+{Math.round(reroute.capacity_change)} cap</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Impact Summary - NOW DYNAMIC */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold">System Impact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-red-50 rounded-lg">
                  <p className="text-sm text-red-600 font-medium">Routes Losing Buses</p>
                  <p className="text-2xl font-bold text-red-700">{routesLosingBuses}</p>
                  <p className="text-xs text-red-500 mt-1">Routes that sent buses away</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-600 font-medium">Routes Gaining Buses</p>
                  <p className="text-2xl font-bold text-green-700">{routesGainingBuses}</p>
                  <p className="text-xs text-green-500 mt-1">
                    {routesGainingBuses > 1 
                      ? `Routes: ${targetNames.substring(0, 30)}${targetNames.length > 30 ? '...' : ''}`
                      : `Route ${mostPopularTarget?.[0] || 'N/A'} received rerouted buses`}
                  </p>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-600 font-medium">Total Capacity Shift</p>
                  <p className="text-2xl font-bold text-blue-700">+{totalCapacityShift.toLocaleString()}</p>
                  <p className="text-xs text-blue-500 mt-1">Passengers/hour capacity redistributed</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <p className="text-sm text-purple-600 font-medium">Reroute Distribution</p>
                  <div className="mt-2 space-y-1">
                    {Array.from(targetCounts.entries()).slice(0, 5).map(([target, count]) => (
                      <div key={target} className="flex justify-between text-sm">
                        <span>Route {target}</span>
                        <span className="font-medium">{count} bus{count > 1 ? 'es' : ''}</span>
                      </div>
                    ))}
                    {targetCounts.size > 5 && (
                      <p className="text-xs text-slate-500 mt-1">+{targetCounts.size - 5} more routes</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}