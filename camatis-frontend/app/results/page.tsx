"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { getResults } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Bus, Clock, TrendingUp, ArrowRight, AlertTriangle } from "lucide-react";

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

export default function ResultsPage() {
  const [results, setResults] = useState<OptimizationResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResults().then((data) => {
      setResults(data as OptimizationResult[]);
      setLoading(false);
    });
  }, []);

  // Calculate summary stats with safe defaults
  const totalBusesAdded = results.reduce((sum, r) => sum + (r.buses_added || 0), 0);
  const routesWithActions = results.filter(r => r.actions && r.actions.length > 0 && !r.actions.includes("No action")).length;
  const routesRerouted = results.filter(r => r.rerouted_to !== null && r.rerouted_to !== undefined).length;
  const avgFreqMultiplier = results.length > 0 
    ? results.reduce((sum, r) => sum + (r.frequency_multiplier || 1), 0) / results.length 
    : 0;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800">Optimization Results</h1>
          <p className="text-sm text-slate-500">AI-generated decisions with simulated impact</p>
        </div>

        {loading ? (
          <p className="text-slate-400">Loading results...</p>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Routes with Actions</p>
                      <p className="text-xl font-bold">{routesWithActions} / {results.length}</p>
                    </div>
                    <TrendingUp size={24} className="text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Total Buses Added</p>
                      <p className="text-xl font-bold">+{totalBusesAdded}</p>
                    </div>
                    <Bus size={24} className="text-green-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Routes Rerouted</p>
                      <p className="text-xl font-bold">{routesRerouted}</p>
                    </div>
                    <ArrowRight size={24} className="text-orange-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Avg Frequency</p>
                      <p className="text-xl font-bold">{avgFreqMultiplier.toFixed(2)}x</p>
                    </div>
                    <Clock size={24} className="text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Results Table */}
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Route</TableHead>
                      <TableHead>Actions</TableHead>
                      <TableHead>Demand</TableHead>
                      <TableHead>Waiting</TableHead>
                      <TableHead>Freq</TableHead>
                      <TableHead>Buses</TableHead>
                      <TableHead>Reroute</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.slice(0, 50).map((r) => (
                      <TableRow key={r.route_id} className={r.rerouted_to ? "bg-orange-50/50" : ""}>
                        <TableCell className="font-medium">Route {r.route_id}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {(r.actions || []).filter(a => a !== "No action").slice(0, 2).map((a, i) => (
                              <span key={i} className="text-xs px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
                                {a === "Allocate Extra Bus" ? "🚍 +Bus" : 
                                 a === "Increase Frequency" ? "📈 Freq" :
                                 a === "High Demand Risk" ? "⚠️ Risk" :
                                 a === "Investigate Anomaly" ? "🔍 Inv" : a}
                              </span>
                            ))}
                            {(!r.actions || r.actions.length === 0 || r.actions.every(a => a === "No action")) && (
                              <span className="text-xs text-slate-400">—</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{Math.round(r.demand_after || 0)}</TableCell>
                        <TableCell>{Math.round(r.waiting_passengers || 0)}</TableCell>
                        <TableCell>{(r.frequency_multiplier || 1) !== 1.0 ? `${(r.frequency_multiplier || 1).toFixed(2)}x` : "—"}</TableCell>
                        <TableCell>{(r.buses_added || 0) > 0 ? `+${r.buses_added}` : "—"}</TableCell>
                        <TableCell>{r.rerouted_to ? `→ ${r.rerouted_to}` : "—"}</TableCell>
                        <TableCell>
                          {r.high_uncertainty && (
                            <span className="inline-flex items-center gap-1 text-xs text-yellow-600">
                              <AlertTriangle size={12} /> Uncertain
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}