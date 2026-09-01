import { Card, CardContent } from "@/components/ui/Card";
import { Bus, Route, TrendingUp, AlertTriangle } from "lucide-react";

export default function StatsCards({ stats }: { stats?: any }) {
  const statItems = [
    { title: "Total Routes", value: stats?.total_routes ?? 0, icon: Route, color: "text-blue-500" },
    { title: "Active Buses", value: stats?.active_buses ?? 0, icon: Bus, color: "text-green-500" },
    { title: "High Demand Routes", value: stats?.high_demand_routes ?? 0, icon: TrendingUp, color: "text-orange-500" },
    { title: "Anomalies", value: stats?.anomalies ?? 0, icon: AlertTriangle, color: "text-red-500" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
      {statItems.map(({ title, value, icon: Icon, color }) => (
        <Card key={title}>
          <CardContent className="flex items-center gap-4 p-5">
            <div className={`p-3 rounded-full bg-slate-100 ${color}`}>
              <Icon size={22} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold">{value.toLocaleString()}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}