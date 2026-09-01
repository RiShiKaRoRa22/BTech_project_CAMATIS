"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { getResults } from "@/lib/api";
import { 
  Bus, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  ArrowRight,
  Clock,
  Map,
  BarChart3
} from "lucide-react";

interface SimulationResult {
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

export default function SimulationPage() {
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRoute, setSelectedRoute] = useState<number | null>(null);

  useEffect(() => {
    getResults().then((data) => {
      setResults(data as SimulationResult[]);
      setLoading(false);
    });
  }, []);

  const getImpactColor = (waiting: number) => {
    if (waiting > 10000) return "text-red-600 bg-red-50";
    if (waiting > 5000) return "text-orange-600 bg-orange-50";
    if (waiting > 2000) return "text-yellow-600 bg-yellow-50";
    return "text-green-600 bg-green-50";
  };

  const calculateEfficiency = (waiting: number, demand: number) => {
    if (demand === 0) return 100;
    return Math.max(0, Math.min(100, 100 - (waiting / demand) * 100));
  };

  const selectedData = selectedRoute ? results.find(r => r.route_id === selectedRoute) : null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800 mb-1">Simulation Results</h1>
          <p className="text-sm text-slate-500">
            Dynamic system state after agent decisions and simulation
          </p>
        </div>

        {loading ? (
          <p className="text-slate-400 text-sm">Loading simulation data...</p>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Total Routes</p>
                      <p className="text-2xl font-bold">{results.length}</p>
                    </div>
                    <Map className="text-blue-500" size={32} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Buses Added</p>
                      <p className="text-2xl font-bold">
                        {results.reduce((sum, r) => sum + r.buses_added, 0)}
                      </p>
                    </div>
                    <Bus className="text-green-500" size={32} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Avg Frequency</p>
                      <p className="text-2xl font-bold">
                        {(results.reduce((sum, r) => sum + r.frequency_multiplier, 0) / results.length).toFixed(2)}x
                      </p>
                    </div>
                    <Clock className="text-purple-500" size={32} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Routes with Actions</p>
                      <p className="text-2xl font-bold">
                        {results.filter(r => r.actions.length > 0 && !r.actions.includes("No action")).length}
                      </p>
                    </div>
                    <BarChart3 className="text-orange-500" size={32} />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Route List */}
              <div className="lg:col-span-1">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-semibold">Routes with Decisions</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="divide-y">
                      {results.slice(0, 50).map((route) => (
                        <div
                          key={route.route_id}
                          onClick={() => setSelectedRoute(route.route_id)}
                          className={`p-4 cursor-pointer transition-colors hover:bg-slate-50 ${
                            selectedRoute === route.route_id ? "bg-blue-50 border-l-4 border-blue-500" : ""
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-medium text-slate-800">Route {route.route_id}</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              route.anomaly || route.high_uncertainty 
                                ? "bg-red-100 text-red-700" 
                                : route.buses_added > 0 || route.frequency_multiplier > 1
                                ? "bg-green-100 text-green-700"
                                : "bg-slate-100 text-slate-600"
                            }`}>
                              {route.anomaly ? "Anomaly" : route.buses_added > 0 ? "Optimized" : "Normal"}
                            </span>
                          </div>
                          <div className="text-sm text-slate-600 mb-2">
                            Waiting: <span className="font-medium">{route.waiting_passengers.toLocaleString()}</span>
                          </div>
                          {route.actions.length > 0 && !route.actions.includes("No action") && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {route.actions.slice(0, 2).map((action) => (
                                <span key={action} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                                  {action}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Route Details */}
              <div className="lg:col-span-2">
                {selectedData ? (
                  <div className="space-y-6">
                    {/* Decision Impact Card */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold">Route {selectedData.route_id} - Simulation Outcome</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-4 mb-6">
                          <div className="bg-slate-50 rounded-lg p-4">
                            <p className="text-xs text-slate-500 mb-1">After Decisions</p>
                            <p className="text-2xl font-bold">{selectedData.waiting_passengers.toLocaleString()}</p>
                            <p className="text-xs text-slate-500">Waiting Passengers</p>
                          </div>
                          <div className="bg-slate-50 rounded-lg p-4">
                            <p className="text-xs text-slate-500 mb-1">Efficiency Score</p>
                            <p className="text-2xl font-bold">
                              {calculateEfficiency(selectedData.waiting_passengers, selectedData.demand_after)}%
                            </p>
                            <p className="text-xs text-slate-500">Based on waiting/demand ratio</p>
                          </div>
                        </div>

                        {/* Actions Applied */}
                        {selectedData.actions.length > 0 && !selectedData.actions.includes("No action") && (
                          <div className="mb-6">
                            <h3 className="text-sm font-semibold text-slate-700 mb-3">Actions Applied</h3>
                            <div className="flex flex-wrap gap-2">
                              {selectedData.actions.map((action) => (
                                <span key={action} className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm">
                                  {action}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Quantified Decisions */}
                        <div className="grid grid-cols-2 gap-4 mb-6">
                          {selectedData.buses_added > 0 && (
                            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                              <Bus className="text-green-600" size={20} />
                              <div>
                                <p className="text-xs text-green-600 font-medium">Buses Added</p>
                                <p className="text-lg font-bold text-green-700">+{selectedData.buses_added}</p>
                              </div>
                            </div>
                          )}
                          {selectedData.frequency_multiplier !== 1.0 && (
                            <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                              <Clock className="text-purple-600" size={20} />
                              <div>
                                <p className="text-xs text-purple-600 font-medium">Frequency</p>
                                <p className="text-lg font-bold text-purple-700">{selectedData.frequency_multiplier}x</p>
                              </div>
                            </div>
                          )}
                          {selectedData.rerouted_to && (
                            <div className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                              <Map className="text-orange-600" size={20} />
                              <div>
                                <p className="text-xs text-orange-600 font-medium">Rerouted To</p>
                                <p className="text-lg font-bold text-orange-700">Route {selectedData.rerouted_to}</p>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Impact Indicators */}
                        <div className="border-t pt-4">
                          <h3 className="text-sm font-semibold text-slate-700 mb-3">System Impact</h3>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-600">Current Waiting Passengers</span>
                              <span className={`font-medium ${getImpactColor(selectedData.waiting_passengers)}`}>
                                {selectedData.waiting_passengers.toLocaleString()}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-600">After Decision Demand</span>
                              <span className="font-medium">{selectedData.demand_after.toLocaleString()}</span>
                            </div>
                            {selectedData.high_uncertainty && (
                              <div className="flex items-center gap-2 mt-3 p-2 bg-yellow-50 rounded">
                                <AlertTriangle size={14} className="text-yellow-600" />
                                <span className="text-xs text-yellow-700">High uncertainty in predictions - monitor closely</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Simulation Insights */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold">Simulation Insights</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {selectedData.buses_added > 0 && (
                            <div className="flex items-start gap-3">
                              <TrendingDown className="text-green-500 mt-0.5" size={16} />
                              <p className="text-sm text-slate-600">
                                Added <span className="font-medium">{selectedData.buses_added}</span> bus(es) to Route {selectedData.route_id}. 
                                Expected load reduction of ~{Math.min(40, selectedData.buses_added * 15)}%.
                              </p>
                            </div>
                          )}
                          {selectedData.frequency_multiplier > 1 && (
                            <div className="flex items-start gap-3">
                              <TrendingUp className="text-blue-500 mt-0.5" size={16} />
                              <p className="text-sm text-slate-600">
                                Increased frequency by <span className="font-medium">{selectedData.frequency_multiplier}x</span>. 
                                Waiting time reduced by ~{Math.min(50, (selectedData.frequency_multiplier - 1) * 30)}%.
                              </p>
                            </div>
                          )}
                          {selectedData.rerouted_to && (
                            <div className="flex items-start gap-3">
                              <ArrowRight className="text-orange-500 mt-0.5" size={16} />
                              <p className="text-sm text-slate-600">
                                Rerouted to Route {selectedData.rerouted_to}. 
                                Load distribution improved across network.
                              </p>
                            </div>
                          )}
                          {selectedData.actions.length === 0 || selectedData.actions.includes("No action") ? (
                            <div className="flex items-start gap-3">
                              <AlertTriangle className="text-slate-400 mt-0.5" size={16} />
                              <p className="text-sm text-slate-600">
                                No actions applied. Route operating within normal parameters.
                              </p>
                            </div>
                          ) : null}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <p className="text-slate-500">Select a route to view simulation details</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}