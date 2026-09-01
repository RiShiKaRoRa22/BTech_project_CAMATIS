"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { getRoute } from "@/lib/api";
import DemandChart from "@/components/routeDetail/DemandChart";
import LoadChart from "@/components/routeDetail/LoadChart";
import PredictionCard from "@/components/routeDetail/PredictionCard";
import ActionsPanel from "@/components/routeDetail/ActionsPanel";
import { ArrowLeft } from "lucide-react";

export default function RouteDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const routeId = decodeURIComponent(id);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRoute(routeId).then((data) => {
      setDetail(data);
      setLoading(false);
    });
  }, [routeId]);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8">Loading...</main>
      </div>
    );
  }

  if (!detail || !detail.demand_trend.length) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8">
          <p className="text-slate-500">Route data not found.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-4 transition-colors"
        >
          <ArrowLeft size={16} /> Back to Routes
        </button>

        <h1 className="text-2xl font-bold text-slate-800 mb-1">Route {routeId} — Detail Analysis</h1>
        <p className="text-sm text-slate-500 mb-6">AI-generated insights and recommendations</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <DemandChart data={detail.demand_trend} />
          <LoadChart data={detail.load_trend} />
        </div>

        <div className="mb-6">
          <PredictionCard confidence={detail.confidence} />
        </div>

        <ActionsPanel
          recommendations={detail.recommendations}
          actionBadges={detail.action_badges}
        />
      </main>
    </div>
  );
}