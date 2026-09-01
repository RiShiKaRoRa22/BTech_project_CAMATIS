import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { AlertTriangle, Info, XCircle } from "lucide-react";

interface Alert {
  id: number;
  route: string;
  message: string;
  severity: string;
  time: string;
}

const severityConfig: Record<string, { icon: typeof XCircle; color: string; bg: string }> = {
  High: { icon: XCircle, color: "text-red-500", bg: "bg-red-50" },
  Medium: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-50" },
  Low: { icon: Info, color: "text-blue-500", bg: "bg-blue-50" },
};

export default function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-semibold">Alerts</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {alerts.map((alert) => {
            const cfg = severityConfig[alert.severity] ?? severityConfig.Low;
            const Icon = cfg.icon;
            return (
              <div key={alert.id} className={`flex items-start gap-3 p-3 rounded-lg ${cfg.bg}`}>
                <Icon size={16} className={`mt-0.5 shrink-0 ${cfg.color}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{alert.message}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{alert.time}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}