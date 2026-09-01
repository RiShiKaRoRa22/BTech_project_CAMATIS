import { Card, CardContent } from "@/components/ui/Card";
import { Gauge } from "lucide-react";

interface PredictionCardProps {
  confidence: number;
}

export default function PredictionCard({ confidence }: PredictionCardProps) {
  const color = confidence >= 80 ? "bg-green-500" : confidence >= 60 ? "bg-yellow-500" : "bg-red-500";
  const textColor = confidence >= 80 ? "text-green-600" : confidence >= 60 ? "text-yellow-600" : "text-red-600";

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-center gap-2 mb-3">
          <Gauge size={18} className="text-slate-500" />
          <span className="text-sm font-semibold text-slate-700">Model Confidence</span>
        </div>
        <div className="flex justify-between mb-1">
          <span className="text-sm text-slate-500">Prediction Confidence</span>
          <span className={`text-sm font-bold ${textColor}`}>{confidence}%</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-3">
          <div className={`${color} h-3 rounded-full transition-all`} style={{ width: `${confidence}%` }} />
        </div>
      </CardContent>
    </Card>
  );
}
