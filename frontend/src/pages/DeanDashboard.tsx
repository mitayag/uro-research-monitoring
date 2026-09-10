import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  BookOpen,
  BarChart3,
  Send,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface DeanStats {
  total: number;
  pending_endorsement: number;
  active: number;
  needs_attention: number;
  under_evaluation: number;
  under_implementation: number;
  completed: number;
  by_status: Record<string, number>;
  school_name: string | null;
}

interface EndorsementItem {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  submitted_at: string | null;
  created_at: string | null;
  nature_of_research: string | null;
}

interface ActivityItem {
  id: string;
  research_id: string;
  research_title: string | null;
  action: string;
  new_status: string;
  prior_status: string | null;
  remarks: string | null;
  created_at: string | null;
}

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

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "Awaiting Endorsement",
  ENDORSED_TO_URO: "Endorsed to URO",
  URO_RECEIVED: "URO Received",
  INITIAL_REVIEW: "Initial Review",
  INITIAL_REVISION_REQUIRED: "Revision Required",
  INITIAL_REVISION_SUBMITTED: "Revision Submitted",
  INITIAL_REVIEW_PASSED: "Review Passed",
  PROPOSAL_TURNITIN: "Turnitin",
  PROPOSAL_TURNITIN_REVISION_REQUIRED: "Turnitin Revision",
  PROPOSAL_TURNITIN_RESUBMITTED: "Turnitin Resubmitted",
  PROPOSAL_TURNITIN_PASSED: "Turnitin Passed",
  READY_FOR_EXTERNAL_EVALUATION: "Ready for External",
  EXTERNAL_EVALUATION: "External Eval",
  EXTERNAL_EVALUATION_PASSED: "External Passed",
  FOR_IRB_REVIEW: "IRB Review",
  PROPOSAL_APPROVED: "Approved",
  RESEARCH_IN_PROGRESS: "In Progress",
  COMPLETED: "Completed",
};

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  SUBMITTED: "bg-blue-100 text-blue-700",
  FOR_DEAN_ENDORSEMENT: "bg-amber-100 text-amber-700",
  ENDORSED_TO_URO: "bg-blue-100 text-blue-700",
  COMPLETED: "bg-green-100 text-green-700",
  READY_FOR_PRESENTATION: "bg-green-100 text-green-700",
  READY_FOR_PUBLICATION: "bg-green-100 text-green-700",
};

function getDaysWaiting(submittedAt: string | null): number {
  if (!submittedAt) return 0;
  const submitted = new Date(submittedAt);
  const now = new Date();
  return Math.floor((now.getTime() - submitted.getTime()) / (1000 * 60 * 60 * 24));
}

export default function DeanDashboard() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DeanStats | null>(null);
  const [endorsements, setEndorsements] = useState<EndorsementItem[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [monitoring, setMonitoring] = useState<MonitoringStages | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiRequest<DeanStats>("/dean/stats", { token }),
      apiRequest<EndorsementItem[]>("/dean/endorsements", { token }),
      apiRequest<ActivityItem[]>("/dean/activity?page_size=8", { token }),
      apiRequest<MonitoringStages>("/dean/monitoring", { token }),
    ])
      .then(([statsData, endorsementsData, activityData, monitoringData]) => {
        setStats(statsData);
        setEndorsements(endorsementsData);
        setActivity(activityData);
        setMonitoring(monitoringData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const QUICK_ACTIONS = [
    { label: "Pending Endorsements", desc: "Review submissions", icon: Send, action: () => navigate("/dean/endorsements"), primary: true },
    { label: "Research Projects", desc: "View all projects", icon: FileText, action: () => navigate("/dean/research") },
    { label: "Needs Attention", desc: "Items requiring action", icon: AlertCircle, action: () => navigate("/dean/research?filter=needs-attention") },
    { label: "Progress Monitoring", desc: "Track workflow stages", icon: BarChart3, action: () => navigate("/dean/monitoring") },
    { label: "Completed Research", desc: "View completed", icon: CheckCircle, action: () => navigate("/dean/completed") },
    { label: "Generate Reports", desc: "School-level reports", icon: BookOpen, action: () => navigate("/dean/reports") },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Banner */}
      <div
        className="rounded-xl overflow-hidden relative h-40 flex items-center px-8"
        style={{
          background: "linear-gradient(135deg, #5A0E16 0%, #7E1320 40%, rgba(126,19,32,0.7) 100%)",
        }}
      >
        <div className="relative z-10">
          <p className="text-white/60 text-xs tracking-[0.15em] uppercase mb-1">School/College Oversight</p>
          <h1 className="font-heading text-3xl font-bold text-white mb-1">
            Welcome, {user?.first_name || "Dean"}!
          </h1>
          <p className="text-white/80 text-sm">Monitor and support research within your academic unit.</p>
        </div>
        {stats?.school_name && (
          <div className="absolute right-8 top-1/2 -translate-y-1/2 text-right hidden lg:block">
            <p className="font-heading text-white/90 text-lg italic">{stats.school_name}</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={action.action}
            className={`flex flex-col items-center gap-2 p-4 rounded-card border transition-all hover:-translate-y-0.5 hover:shadow-hover ${
              action.primary
                ? "bg-maroon-700 text-white border-maroon-700"
                : "bg-white text-gray-700 border-gray-200 hover:border-maroon-300"
            }`}
          >
            <action.icon size={22} />
            <span className="text-xs font-semibold text-center leading-tight">{action.label}</span>
          </button>
        ))}
      </div>

      {/* Requires My Action */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-base font-bold flex items-center gap-2">
            <AlertCircle size={18} className="text-amber-500" />
            Requires My Action
          </h3>
          {endorsements.length > 0 && (
            <span className="bg-amber-100 text-amber-700 text-xs font-semibold px-2.5 py-1 rounded-full">
              {endorsements.length}
            </span>
          )}
        </div>
        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse flex items-center gap-3">
                <div className="h-3 bg-gray-200 rounded w-full" />
              </div>
            ))}
          </div>
        ) : endorsements.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No research submissions currently require your endorsement.</p>
        ) : (
          <div className="space-y-3">
            {endorsements.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-amber-50 rounded-card border border-amber-100">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{item.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400 font-mono">{item.tracking_number}</span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500">{item.lead_proponent_name}</span>
                    {item.submitted_at && (
                      <>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-500">{getDaysWaiting(item.submitted_at)} days waiting</span>
                      </>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/dean/endorsements/${item.id}`)}
                  className="ml-4 px-3 py-1.5 bg-maroon-700 text-white text-xs font-semibold rounded-control hover:bg-maroon-600 transition-colors"
                >
                  Review
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Research Projects", value: loading ? "—" : String(stats?.total ?? 0), color: "text-gray-800", bg: "bg-gray-100", icon: FileText },
          { label: "Pending Endorsements", value: loading ? "—" : String(stats?.pending_endorsement ?? 0), color: "text-amber-600", bg: "bg-amber-500/10", icon: Send },
          { label: "Active Research", value: loading ? "—" : String(stats?.active ?? 0), color: "text-blue-600", bg: "bg-blue-500/10", icon: Clock },
          { label: "Needs Attention", value: loading ? "—" : String(stats?.needs_attention ?? 0), color: "text-red-600", bg: "bg-red-500/10", icon: AlertCircle },
          { label: "Under Evaluation", value: loading ? "—" : String(stats?.under_evaluation ?? 0), color: "text-purple-600", bg: "bg-purple-500/10", icon: Eye },
          { label: "Under Implementation", value: loading ? "—" : String(stats?.under_implementation ?? 0), color: "text-blue-600", bg: "bg-blue-500/10", icon: BarChart3 },
          { label: "Completed", value: loading ? "—" : String(stats?.completed ?? 0), color: "text-green-600", bg: "bg-green-500/10", icon: CheckCircle },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-card border border-gray-200 p-4 shadow-card">
            <div className={`w-8 h-8 rounded-lg ${kpi.bg} flex items-center justify-center mb-2`}>
              <kpi.icon size={16} className={kpi.color} />
            </div>
            <div className="text-xl font-bold text-gray-800">{kpi.value}</div>
            <div className="text-[10px] text-gray-500 mt-0.5">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Research Progress by Stage */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-base font-bold mb-4">Research Progress by Stage</h3>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-3 bg-gray-200 rounded w-full" />
            ))}
          </div>
        ) : monitoring ? (
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
            {[
              { label: "Awaiting Endorsement", count: monitoring.awaiting_endorsement, color: "text-amber-600", bg: "bg-amber-50" },
              { label: "URO Processing", count: monitoring.uro_processing, color: "text-blue-600", bg: "bg-blue-50" },
              { label: "External Evaluation", count: monitoring.external_evaluation, color: "text-purple-600", bg: "bg-purple-50" },
              { label: "IRB Review", count: monitoring.irb_review, color: "text-indigo-600", bg: "bg-indigo-50" },
              { label: "Implementation", count: monitoring.implementation, color: "text-cyan-600", bg: "bg-cyan-50" },
              { label: "Final Evaluation", count: monitoring.final_evaluation, color: "text-violet-600", bg: "bg-violet-50" },
              { label: "Completed", count: monitoring.completed, color: "text-green-600", bg: "bg-green-50" },
            ].map((stage) => (
              <button
                key={stage.label}
                onClick={() => navigate("/dean/monitoring")}
                className={`${stage.bg} rounded-card p-3 text-left hover:opacity-80 transition-opacity`}
              >
                <div className={`text-lg font-bold ${stage.color}`}>{stage.count}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">{stage.label}</div>
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-base font-bold mb-4">Recent Research Activity</h3>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-gray-200 mt-1.5" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 bg-gray-200 rounded w-3/4" />
                  <div className="h-2 bg-gray-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : activity.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No recent research activity.</p>
        ) : (
          <div className="space-y-3">
            {activity.map((item) => (
              <div key={item.id} className="flex items-start gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-maroon-500 mt-1.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-800 font-medium">
                    {item.action.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase())}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[item.new_status] || "bg-gray-100 text-gray-600"}`}>
                      {STATUS_LABELS[item.new_status] || item.new_status.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-gray-400">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                  {item.remarks && <p className="text-xs text-gray-500 mt-0.5">{item.remarks}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
