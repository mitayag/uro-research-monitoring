import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FilePlus,
  UserCheck,
  Search,
  Shield,
  Eye,
  BarChart3,
  Clock,
  FileText,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import ResearcherDashboard from "./ResearcherDashboard";
import DeanDashboard from "./DeanDashboard";

interface ResearchItem {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  created_at: string | null;
  submitted_at: string | null;
}

interface StatsResponse {
  total: number;
  by_status: Record<string, number>;
}

interface Phase3Dashboard {
  awaiting_receipt: number;
  initial_review: number;
  revision_required: number;
  turnitin_pending: number;
  turnitin_revision: number;
  turnitin_passed: number;
  ready_for_external: number;
}

const QUICK_ACTIONS = [
  { label: "New Submission", desc: "Encode a new research proposal", icon: FilePlus, primary: true },
  { label: "Assign Evaluator", desc: "Manage panel of evaluators", icon: UserCheck },
  { label: "Check Turnitin", desc: "Run similarity check", icon: Search },
  { label: "IRB Review", desc: "Track ethics review", icon: Shield },
  { label: "Blind Evaluation", desc: "Manage evaluations", icon: Eye },
  { label: "Generate Reports", desc: "Create research reports", icon: BarChart3 },
];

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  SUBMITTED: "bg-blue-100 text-blue-700",
  FOR_DEAN_ENDORSEMENT: "bg-blue-100 text-blue-700",
  ENDORSED_TO_URO: "bg-blue-100 text-blue-700",
  URO_RECEIVED: "bg-purple-100 text-purple-700",
  INITIAL_REVIEW: "bg-yellow-100 text-yellow-700",
  INITIAL_REVISION_REQUIRED: "bg-red-100 text-red-600",
  INITIAL_REVISION_SUBMITTED: "bg-blue-100 text-blue-700",
  INITIAL_REVIEW_PASSED: "bg-green-100 text-green-700",
  PROPOSAL_TURNITIN: "bg-yellow-100 text-yellow-700",
  PROPOSAL_TURNITIN_REVISION_REQUIRED: "bg-red-100 text-red-600",
  PROPOSAL_TURNITIN_RESUBMITTED: "bg-blue-100 text-blue-700",
  PROPOSAL_TURNITIN_PASSED: "bg-green-100 text-green-700",
  READY_FOR_EXTERNAL_EVALUATION: "bg-green-100 text-green-700",
  EXTERNAL_EVALUATION: "bg-purple-100 text-purple-700",
  EXTERNAL_EVALUATION_PASSED: "bg-green-100 text-green-700",
  FOR_IRB_REVIEW: "bg-purple-100 text-purple-700",
  PROPOSAL_APPROVED: "bg-green-100 text-green-700",
  RESEARCH_IN_PROGRESS: "bg-blue-100 text-blue-700",
  FINAL_PAPER_SUBMITTED: "bg-yellow-100 text-yellow-700",
  FINAL_PAPER_TURNITIN: "bg-yellow-100 text-yellow-700",
  FINAL_PAPER_TURNITIN_PASSED: "bg-green-100 text-green-700",
  FINAL_BLIND_EVALUATION: "bg-purple-100 text-purple-700",
  FINAL_BLIND_EVALUATION_PASSED: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-100 text-green-700",
  READY_FOR_PRESENTATION: "bg-green-100 text-green-700",
  READY_FOR_PUBLICATION: "bg-green-100 text-green-700",
  ARCHIVED: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "For Dean",
  ENDORSED_TO_URO: "Endorsed",
  URO_RECEIVED: "Received",
  INITIAL_REVIEW: "Initial Review",
  INITIAL_REVISION_REQUIRED: "Revision Required",
  INITIAL_REVISION_SUBMITTED: "Revision Submitted",
  INITIAL_REVIEW_PASSED: "Passed",
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

const DEADLINES = [
  { date: "SEP 15", title: "Full Paper Submission (Batch 2)", subtitle: "Research Implementation", days: "5 days left", color: "text-status-danger" },
  { date: "SEP 22", title: "Turnitin Checking Deadline", subtitle: "Final Papers", days: "12 days left", color: "text-status-danger" },
  { date: "SEP 30", title: "IRB Review Meeting", subtitle: "Protocol Review", days: "20 days left", color: "text-status-warning" },
  { date: "OCT 06", title: "Final Evaluation (Blind Review)", subtitle: "Completed Papers", days: "26 days left", color: "text-status-success" },
];

export default function Dashboard() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [phase3, setPhase3] = useState<Phase3Dashboard | null>(null);
  const [recentItems, setRecentItems] = useState<ResearchItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Check if user is a pure researcher (not admin, URO director, or URO staff)
  const isResearcher = user?.roles?.includes("RESEARCHER") && !user?.roles?.includes("ADMIN") && !user?.roles?.includes("URO_DIRECTOR") && !user?.roles?.includes("URO_STAFF");

  // Check if user is a pure Dean (not admin, URO director, or URO staff)
  const isDean = user?.roles?.includes("DEAN") && !user?.roles?.includes("ADMIN") && !user?.roles?.includes("URO_DIRECTOR") && !user?.roles?.includes("URO_STAFF");

  // Render researcher-specific dashboard
  if (isResearcher) {
    return <ResearcherDashboard />;
  }

  // Render Dean-specific dashboard
  if (isDean) {
    return <DeanDashboard />;
  }

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiRequest<StatsResponse>("/research/stats/summary", { token }),
      apiRequest<{ items: ResearchItem[] }>("/research?page_size=4", { token }),
      apiRequest<Phase3Dashboard>("/research/phase3/dashboard", { token }).catch(() => null),
    ])
      .then(([statsData, researchData, phase3Data]) => {
        setStats(statsData);
        setRecentItems(researchData.items);
        setPhase3(phase3Data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const ongoing = stats
    ? Object.entries(stats.by_status)
        .filter(([s]) => !["COMPLETED", "ARCHIVED", "DRAFT"].includes(s))
        .reduce((sum, [, c]) => sum + c, 0)
    : 0;
  const completed = stats?.by_status?.["COMPLETED"] ?? 0;
  const drafts = stats?.by_status?.["DRAFT"] ?? 0;
  const total = stats?.total ?? 0;

  const totalInPhase3 = phase3
    ? phase3.awaiting_receipt + phase3.initial_review + phase3.revision_required + phase3.turnitin_pending + phase3.turnitin_revision + phase3.turnitin_passed
    : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Hero Banner */}
      <div
        className="rounded-xl overflow-hidden relative h-40 flex items-center px-8"
        style={{
          background: "linear-gradient(135deg, #5A0E16 0%, #7E1320 40%, rgba(126,19,32,0.7) 100%)",
        }}
      >
        <div className="relative z-10">
          <p className="text-white/60 text-xs tracking-[0.15em] uppercase mb-1">Research for a Brighter Tomorrow</p>
          <h1 className="font-heading text-3xl font-bold text-white mb-1">Welcome!</h1>
          <p className="text-white/80 text-sm">Monitor. Support. Advance Research.</p>
        </div>
        <div className="absolute right-8 top-1/2 -translate-y-1/2 text-right hidden lg:block">
          <p className="font-heading text-white/90 text-lg italic">"Knowledge<br/>in service of<br/>society."</p>
          <p className="text-white/50 text-xs mt-1">- Holy Angel University</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={() => {
              if (action.label === "New Submission") navigate("/research/new");
            }}
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

      {/* KPI Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="font-heading text-lg font-bold text-gray-800">Research Projects Overview</h2>
            <p className="text-xs text-gray-500">Current status of research projects</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Total Submissions", value: loading ? "—" : String(total), color: "text-maroon-700", bg: "bg-maroon-500/10", icon: FileText },
            { label: "Ongoing", value: loading ? "—" : String(ongoing), color: "text-green-600", bg: "bg-green-500/10", icon: Clock },
            { label: "Drafts", value: loading ? "—" : String(drafts), color: "text-yellow-600", bg: "bg-yellow-500/10", icon: FileText },
            { label: "Completed", value: loading ? "—" : String(completed), color: "text-green-700", bg: "bg-green-500/10", icon: CheckCircle },
          ].map((kpi) => (
            <div key={kpi.label} className="bg-white rounded-card border border-gray-200 p-4 shadow-card">
              <div className={`w-10 h-10 rounded-lg ${kpi.bg} flex items-center justify-center mb-3`}>
                <kpi.icon size={20} className={kpi.color} />
              </div>
              <div className="text-2xl font-bold text-gray-800">{kpi.value}</div>
              <div className="text-xs text-gray-500 mt-0.5">{kpi.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Phase 3 Workflow Status */}
      {phase3 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="font-heading text-lg font-bold text-gray-800">Phase 3: URO Processing</h2>
              <p className="text-xs text-gray-500">{totalInPhase3} research in URO workflow</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
            {[
              { label: "Awaiting Receipt", value: phase3.awaiting_receipt, color: "text-blue-600", bg: "bg-blue-500/10", icon: Clock },
              { label: "Initial Review", value: phase3.initial_review, color: "text-yellow-600", bg: "bg-yellow-500/10", icon: Search },
              { label: "Revision Required", value: phase3.revision_required, color: "text-red-600", bg: "bg-red-500/10", icon: AlertCircle },
              { label: "Turnitin Pending", value: phase3.turnitin_pending, color: "text-yellow-600", bg: "bg-yellow-500/10", icon: Clock },
              { label: "Turnitin Revision", value: phase3.turnitin_revision, color: "text-red-600", bg: "bg-red-500/10", icon: AlertCircle },
              { label: "Turnitin Passed", value: phase3.turnitin_passed, color: "text-green-600", bg: "bg-green-500/10", icon: CheckCircle },
              { label: "Ready for External", value: phase3.ready_for_external, color: "text-green-700", bg: "bg-green-500/10", icon: Eye },
            ].map((kpi) => (
              <div key={kpi.label} className="bg-white rounded-card border border-gray-200 p-3 shadow-card">
                <div className={`w-8 h-8 rounded-lg ${kpi.bg} flex items-center justify-center mb-2`}>
                  <kpi.icon size={16} className={kpi.color} />
                </div>
                <div className="text-xl font-bold text-gray-800">{loading ? "—" : String(kpi.value)}</div>
                <div className="text-[10px] text-gray-500 mt-0.5 leading-tight">{kpi.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Row: Deadlines + Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Deadlines */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading text-base font-bold flex items-center gap-2">
              <Clock size={18} className="text-maroon-600" />
              Upcoming Deadlines
            </h3>
          </div>
          <div className="space-y-3">
            {DEADLINES.map((d) => (
              <div key={d.title} className="flex items-start gap-3">
                <div className="text-center shrink-0 w-12">
                  <div className="text-[10px] text-gray-500 uppercase">{d.date.split(" ")[0]}</div>
                  <div className="text-lg font-bold text-gray-800">{d.date.split(" ")[1]}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-gray-800 truncate">{d.title}</div>
                  <div className="text-xs text-gray-500">{d.subtitle}</div>
                </div>
                <span className={`text-xs font-medium shrink-0 ${d.color}`}>{d.days}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Research from API */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading text-base font-bold flex items-center gap-2">
              <FileText size={18} className="text-maroon-600" />
              Recent Research
            </h3>
          </div>
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
          ) : (
            <div className="space-y-3">
              {recentItems.map((item) => (
                <div key={item.id} className="flex items-start gap-3 text-sm">
                  <div className="w-2 h-2 rounded-full bg-maroon-500 mt-1.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-gray-800 font-medium truncate">{item.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400 font-mono">{item.tracking_number}</span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[item.status] || "bg-gray-100 text-gray-600"}`}>
                        {STATUS_LABELS[item.status] || item.status.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
              {recentItems.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">No research projects yet</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Recent Submissions Table */}
      <div className="bg-white rounded-card border border-gray-200 shadow-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 className="font-heading text-base font-bold flex items-center gap-2">
            <FileText size={18} className="text-maroon-600" />
            All Research Projects
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
                <th className="px-5 py-3 font-semibold">Code</th>
                <th className="px-5 py-3 font-semibold">Title</th>
                <th className="px-5 py-3 font-semibold">Researcher</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Date Created</th>
              </tr>
            </thead>
            <tbody>
              {recentItems.map((s) => (
                <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer" onClick={() => window.location.href = `/research/${s.id}`}>
                  <td className="px-5 py-3 font-mono text-xs text-gray-600">{s.tracking_number}</td>
                  <td className="px-5 py-3 font-medium text-gray-800 max-w-[300px] truncate">{s.title}</td>
                  <td className="px-5 py-3 text-gray-600">{s.lead_proponent_name || "—"}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[s.status] || "bg-gray-100 text-gray-600"}`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      {STATUS_LABELS[s.status] || s.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-500 text-xs">
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
              {recentItems.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-gray-400 text-sm">
                    No research projects found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
