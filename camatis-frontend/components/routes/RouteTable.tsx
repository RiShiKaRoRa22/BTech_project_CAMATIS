"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getRoutes, getResults } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Input } from "@/components/ui/Input";
import { Card, CardContent } from "@/components/ui/Card";

interface Route {
  id: string;
  demand: number;
  load_factor: number;
  status: string;
}

interface OptimizationResult {
  route_id: number;
  buses_added: number;
  frequency_multiplier: number;
  rerouted_to: number | null;
  actions: string[];
}

const getStatusStyle = (status: string, actions: string[]) => {
  if (status === "Anomaly") return "bg-red-100 text-red-700 border-red-200";
  if (actions.includes("High Demand Risk")) return "bg-red-100 text-red-700 border-red-200";
  if (actions.includes("Allocate Extra Bus")) return "bg-green-100 text-green-700 border-green-200";
  if (actions.includes("Increase Frequency")) return "bg-blue-100 text-blue-700 border-blue-200";
  if (status === "Risk") return "bg-yellow-100 text-yellow-700 border-yellow-200";
  return "bg-green-100 text-green-700 border-green-200";
};

const getStatusText = (status: string, actions: string[]) => {
  if (status === "Anomaly") return "Anomaly";
  if (actions.includes("High Demand Risk")) return "High Risk";
  if (actions.includes("Allocate Extra Bus")) return "Add Buses";
  if (actions.includes("Increase Frequency")) return "Increase Freq";
  if (status === "Risk") return "Risk";
  return "Normal";
};

export default function RouteTable() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [routes, setRoutes] = useState<Route[]>([]);
  const [optimizations, setOptimizations] = useState<Map<number, OptimizationResult>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getRoutes(), getResults()]).then(([routesData, resultsData]) => {
      setRoutes(routesData as Route[]);
      
      // Create map of route_id -> optimization data
      const optMap = new Map();
      (resultsData as any[]).forEach(r => {
        optMap.set(r.route_id, r);
      });
      setOptimizations(optMap);
      setLoading(false);
    });
  }, []);

  const filtered = routes.filter((r) =>
    r.id.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return <p className="text-slate-400 text-sm">Loading routes...</p>;
  }

  return (
    <>
      <div className="mb-4">
        <Input
          placeholder="Search by Route ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
      </div>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Route ID</TableHead>
                <TableHead>Demand</TableHead>
                <TableHead>Load %</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
                <TableHead>Freq</TableHead>
                <TableHead>Buses</TableHead>
                <TableHead>Reroute</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((route) => {
                const routeNum = parseInt(route.id.replace("R-", ""));
                const opt = optimizations.get(routeNum);
                const actions = opt?.actions || [];
                const statusText = getStatusText(route.status, actions);
                const statusStyle = getStatusStyle(route.status, actions);
                
                return (
                  <TableRow
                    key={route.id}
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => router.push(`/routes/${encodeURIComponent(route.id)}`)}
                  >
                    <TableCell className="font-medium text-blue-600 hover:underline">
                      {route.id}
                    </TableCell>
                    <TableCell>{Math.round(route.demand)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${route.load_factor > 70 ? 'bg-red-500' : route.load_factor > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(100, route.load_factor)}%` }}
                          />
                        </div>
                        <span>{Math.round(route.load_factor)}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusStyle}`}>
                        {statusText}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {actions.filter(a => a !== "No action").slice(0, 2).map((a, i) => (
                          <span key={i} className="text-xs px-1.5 py-0.5 bg-blue-50 rounded-full">
                            {a === "Allocate Extra Bus" ? "🚍 +Bus" : 
                             a === "Increase Frequency" ? "📈 Freq" :
                             a === "High Demand Risk" ? "⚠️ Risk" :
                             a === "Investigate Anomaly" ? "🔍 Inv" : a}
                          </span>
                        ))}
                        {(!actions.length || actions.every(a => a === "No action")) && (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {opt?.frequency_multiplier && opt.frequency_multiplier !== 1.0 ? 
                        `${opt.frequency_multiplier.toFixed(2)}x` : "—"}
                    </TableCell>
                    <TableCell>
                      {opt?.buses_added && opt.buses_added > 0 ? 
                        <span className="text-green-600">+{opt.buses_added}</span> : "—"}
                    </TableCell>
                    <TableCell>
                      {opt?.rerouted_to ? 
                        <span className="text-orange-600">→ {opt.rerouted_to}</span> : "—"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}