import { Card, CardContent } from "@/components/ui/Card";
import { Clock, Bus, Map } from "lucide-react";

interface ActionsPanelProps {
  recommendations: {
    frequencyMultiplier: string;
    busesToAdd: string;
    rerouteSuggestion: string;
  };
  actionBadges: { label: string; color: string }[];
}

const badgeColors: Record<string, string> = {
  blue: "bg-blue-100 text-blue-700 border-blue-200",
  green: "bg-green-100 text-green-700 border-green-200",
  yellow: "bg-yellow-100 text-yellow-700 border-yellow-200",
  orange: "bg-orange-100 text-orange-700 border-orange-200",
  red: "bg-red-100 text-red-700 border-red-200",
};

export default function ActionsPanel({ recommendations, actionBadges }: ActionsPanelProps) {
  return (
    <>
      <h2 className="text-base font-semibold text-slate-700 mb-3">AI Recommended Actions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="p-3 rounded-full bg-blue-50 text-blue-500"><Clock size={20} /></div>
            <div>
              <p className="text-xs text-slate-500">Frequency Multiplier</p>
              <p className="text-xl font-bold text-slate-800">{recommendations.frequencyMultiplier}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="p-3 rounded-full bg-green-50 text-green-500"><Bus size={20} /></div>
            <div>
              <p className="text-xs text-slate-500">Buses to Add</p>
              <p className="text-xl font-bold text-slate-800">{recommendations.busesToAdd}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="p-3 rounded-full bg-orange-50 text-orange-500"><Map size={20} /></div>
            <div>
              <p className="text-xs text-slate-500">Reroute Suggestion</p>
              <p className="text-base font-bold text-slate-800">{recommendations.rerouteSuggestion}</p>
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="flex flex-wrap gap-2">
        {actionBadges.map((badge) => (
          <span
            key={badge.label}
            className={`inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium border ${badgeColors[badge.color] ?? badgeColors.blue}`}
          >
            {badge.label}
          </span>
        ))}
      </div>
    </>
  );
}
