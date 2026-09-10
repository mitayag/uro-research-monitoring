import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface MonitoringStages {
  awaiting_endorsement: number;
  uro_processing: number;
  turnitin_proposal: number;
  external_evaluation: number;
  irb_review: number;
  implementation: number;
  turnitin_final: number;
  final_evaluation: number;
  completed: number;
}

const STAGES = [
  { key: "awaiting_endorsement", label: "Awaiting Dean Endorsement", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", filter: "FOR_DEAN_ENDORSEMENT" },
  { key: "uro_processing", label: "URO Processing", color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200", filter: "URO_PROCESSING" },
  { key: "turnitin_proposal", label: "Proposal Turnitin", color: "text-yellow-600", bg: "bg-yellow-50", border: "border-yellow-200", filter: "" },
  { key: "external_evaluation", label: "External Evaluation", color: "text-purple-600", bg: "bg-purple-50", border: "border-purple-200", filter: "EXTERNAL_EVALUATION" },
  { key: "irb_review", label: "IRB Review", color: "text-indigo-600", bg: "bg-indigo-50", border: "border-indigo-200", filter: "IRB" },
  { key: "implementation", label: "Research Implementation", color: "text-cyan-600", bg: "bg-cyan-50", border: "border-cyan-200", filter: "IMPLEMENTATION" },
  { key: "turnitin_final", label: "Final Paper Turnitin", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200", filter: "" },
  { key: "final_evaluation", label: "Final Blind Evaluation", color: "text-violet-600", bg: "bg-violet-50", border: "border-violet-200", filter: "" },
  { key: "completed", label: "Completed", color: "text-green-600", bg: "bg-green-50", border: "border-green-200", filter: "COMPLETED" },
];

export default function DeanMonitoring() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [monitoring, setMonitoring] = useState<MonitoringStages | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    apiRequest<MonitoringStages>("/dean/monitoring", { token })
      .then(setMonitoring)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const total = monitoring ? Object.values(monitoring).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Progress Monitoring</h1>
        <p className="text-sm text-gray-500 mt-1">Workflow stage overview for your academic unit</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse h-24 bg-gray-100 rounded-card" />
          ))}
        </div>
      ) : monitoring ? (
        <>
          {/* Summary */}
          <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading text-sm font-bold">Total Projects: {total}</h3>
            </div>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
              {STAGES.map((stage) => (
                <button
                  key={stage.key}
                  onClick={() => stage.filter && navigate(`/dean/research?filter=${stage.filter}`)}
                  className={`${stage.bg} border ${stage.border} rounded-card p-4 text-left hover:opacity-80 transition-opacity ${stage.filter ? "cursor-pointer" : "cursor-default"}`}
                >
                  <div className={`text-2xl font-bold ${stage.color}`}>{monitoring[stage.key as keyof MonitoringStages] || 0}</div>
                  <div className="text-[10px] text-gray-500 mt-1">{stage.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Visual Pipeline */}
          <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
            <h3 className="font-heading text-sm font-bold mb-4">Research Pipeline</h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {STAGES.map((stage, i) => {
                const count = monitoring[stage.key as keyof MonitoringStages] || 0;
                return (
                  <div key={stage.key} className="flex items-center gap-2 shrink-0">
                    <div className={`${stage.bg} border ${stage.border} rounded-card p-3 min-w-[100px] text-center`}>
                      <div className={`text-lg font-bold ${stage.color}`}>{count}</div>
                      <div className="text-[9px] text-gray-500 mt-0.5 leading-tight">{stage.label}</div>
                    </div>
                    {i < STAGES.length - 1 && <ArrowRight size={14} className="text-gray-300 shrink-0" />}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
