"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

export default function SettingsPage() {
  const [form, setForm] = useState({
    maxBuses: "30",
    frequencyLimit: "12",
    optimizationPreference: "balanced",
  });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8001/api/settings")
      .then(res => res.json())
      .then(data => {
        setForm({
          maxBuses: data.maxBuses?.toString() || "30",
          frequencyLimit: data.frequencyLimit?.toString() || "12",
          optimizationPreference: data.optimizationPreference || "balanced",
        });
        setLoading(false);
      })
      .catch(() => {
        // Use defaults if API fails
        setLoading(false);
      });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8001/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          max_buses: parseInt(form.maxBuses),
          frequency_limit: parseInt(form.frequencyLimit),
          optimization_preference: form.optimizationPreference,
        }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } catch (err) {
      console.error("Failed to save:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8">Loading settings...</main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">Settings</h1>
        <p className="text-sm text-slate-500 mb-6">Configure optimization parameters</p>

        <Card className="max-w-lg">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Optimization Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-5">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Max Buses (per route)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={form.maxBuses}
                  onChange={(e) => setForm({ ...form, maxBuses: e.target.value })}
                  className="w-full border border-input rounded-lg px-3 py-2 text-sm"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Maximum buses that can be allocated to a single route
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Frequency Limit (buses/hour)</label>
                <input
                  type="number"
                  min="4"
                  max="20"
                  value={form.frequencyLimit}
                  onChange={(e) => setForm({ ...form, frequencyLimit: e.target.value })}
                  className="w-full border border-input rounded-lg px-3 py-2 text-sm"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Maximum buses per hour (base is 4, this is the cap)
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Optimization Preference</label>
                <select
                  value={form.optimizationPreference}
                  onChange={(e) => setForm({ ...form, optimizationPreference: e.target.value })}
                  className="w-full border border-input rounded-lg px-3 py-2 text-sm"
                >
                  <option value="balanced">Balanced (Default)</option>
                  <option value="cost">Cost Minimization</option>
                  <option value="demand">Demand Coverage</option>
                  <option value="efficiency">Efficiency First</option>
                </select>
                <p className="text-xs text-slate-400 mt-1">
                  {form.optimizationPreference === "balanced" && "Equal weight to cost, demand, and efficiency"}
                  {form.optimizationPreference === "cost" && "Prioritize minimizing operational costs"}
                  {form.optimizationPreference === "demand" && "Prioritize serving maximum passenger demand"}
                  {form.optimizationPreference === "efficiency" && "Prioritize optimal bus utilization"}
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {saved ? "✓ Saved!" : "Save Settings"}
              </button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}