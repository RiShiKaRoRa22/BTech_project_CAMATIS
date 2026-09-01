"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { getAlerts } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { AlertTriangle, Info } from "lucide-react";

interface Alert {
  id: number;
  route: string;
  message: string;
  severity: string;
  time: string;
}

// Only two types: Yellow for Investigate Anomaly, Blue for Uncertainty
const getAlertStyle = (message: string) => {
  if (message.toLowerCase().includes("investigate") || message.toLowerCase().includes("flagged")) {
    return {
      icon: AlertTriangle,
      color: "text-yellow-600",
      bg: "bg-yellow-50",
      badge: "bg-yellow-100 text-yellow-700 border-yellow-200",
      label: "Investigate"
    };
  }
  // Uncertainty alerts
  return {
    icon: Info,
    color: "text-blue-600",
    bg: "bg-blue-50",
    badge: "bg-blue-100 text-blue-700 border-blue-200",
    label: "Uncertainty"
  };
};

export default function AlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAlerts().then((data) => {
      setAlerts(data as Alert[]);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">Alerts</h1>
        <p className="text-sm text-slate-500 mb-6">Detected anomalies and system warnings</p>

        {loading ? (
          <p className="text-slate-400 text-sm">Loading...</p>
        ) : (
          <div className="flex flex-col gap-3">
            {alerts.map((alert) => {
              const cfg = getAlertStyle(alert.message);
              const Icon = cfg.icon;
              return (
                <Card key={alert.id}>
                  <CardContent className={`flex items-start gap-4 p-4 rounded-xl ${cfg.bg}`}>
                    <Icon size={18} className={`mt-0.5 shrink-0 ${cfg.color}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-700">{alert.route}</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cfg.badge}`}>
                          {cfg.label}
                        </span>
                        <span className="text-xs text-slate-400 ml-auto">{alert.time}</span>
                      </div>
                      <p className="text-sm text-slate-600">{alert.message}</p>
                    </div>
                    <button
                      onClick={() => router.push(`/routes/${encodeURIComponent(alert.route)}`)}
                      className="shrink-0 text-xs font-medium text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg px-3 py-1.5 transition-colors"
                    >
                      Investigate
                    </button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}