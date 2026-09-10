import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FilePlus,
  FileText,
  FileUp,
  MessageSquare,
  Shield,
  Clock,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  FolderOpen,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface ResearchItem {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  nature_of_research: string | null;
  created_at: string | null;
  updated_at: string | null;
  authors: { name: string; is_lead: boolean }[];
}

interface ResearcherStats {
  total: number;
  active: number;
  drafts: number;
  completed: number;
  action_required: number;
  by_status: Record<string, number>;
}

interface ActionItem {
  id: string;
  tracking_number: string;
  title: string;
  status: string;
  updated_at: string | null;
  action_required: string;
}

interface ActivityItem {
  id: string;
  research_id: string;
  action: string;
  new_status: string;
  prior_status: string | null;
  remarks: string | null;
  created_at: string | null;
}

const WORKFLOW_STAGES = [
  { label: "Submission", statuses: ["DRAFT", "SUBMITTED"] },
  { label: "Dean Endorsement", statuses: ["FOR_DEAN_ENDORSEMENT", "ENDORSED_TO_URO"] },
  { label: "URO Review", statuses: ["URO_RECEIVED", "INITIAL_REVIEW", "INITIAL_REVISION_REQUIRED", "INITIAL_REVISION_SUBMITTED", "INITIAL_REVIEW_PASSED"] },
  { label: "Turnitin", statuses: ["PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "PROPOSAL_TURNITIN_RESUBMITTED", "PROPOSAL_TURNITIN_PASSED"] },
  { label: "External Eval", statuses: ["READY_FOR_EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION_REVISION_REQUIRED", "EXTERNAL_EVALUATION_PASSED"] },
  { label: "IRB", statuses: ["FOR_IRB_REVIEW", "IRB_REVISION_REQUIRED", "PROPOSAL_APPROVED"] },
  { label: "Implementation", statuses: ["RESEARCH_IN_PROGRESS", "FINAL_PAPER_DUE", "FINAL_PAPER_SUBMITTED"] },
  { label: "Final Turnitin", statuses: ["FINAL_PAPER_TURNITIN", "FINAL_PAPER_TURNITIN_REVISION_REQUIRED", "FINAL_PAPER_TURNITIN_PASSED"] },
  { label: "Final Eval", statuses: ["FINAL_BLIND_EVALUATION", "FINAL_EVALUATION_REVISION_REQUIRED", "FINAL_BLIND_EVALUATION_PASSED"] },
  { label: "Completed", statuses: ["COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED"] },
];

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "For Dean",
  ENDORSED_TO_URO: "Endorsed",
  URO_RECEIVED: "Received",
  INITIAL_REVIEW: "Initial Review",
  INITIAL_REVISION_REQUIRED: "Revision Required",
  INITIAL_REVISION_SUBMITTED: "Revision Submitted",
  INITIAL_REVIEW_PASSED: "Review Passed",
  PROPOSAL_TURNITIN: "Turnitin Checking",
  PROPOSAL_TURNITIN_REVISION_REQUIRED: "Turnitin Revision Required",
  PROPOSAL_TURNITIN_RESUBMITTED: "Turnitin Resubmitted",
  PROPOSAL_TURNITIN_PASSED: "Turnitin Passed",
  READY_FOR_EXTERNAL_EVALUATION: "Ready for External",
  EXTERNAL_EVALUATION: "External Evaluation",
  EXTERNAL_EVALUATION_REVISION_REQUIRED: "External Eval Revision",
  EXTERNAL_EVALUATION_PASSED: "External Eval Passed",
  FOR_IRB_REVIEW: "IRB Review",
  IRB_REVISION_REQUIRED: "IRB Revision Required",
  PROPOSAL_APPROVED: "Proposal Approved",
  RESEARCH_IN_PROGRESS: "Research In Progress",
  FINAL_PAPER_SUBMITTED: "Final Paper Submitted",
  FINAL_PAPER_TURNITIN: "Final Turnitin",
  FINAL_PAPER_TURNITIN_REVISION_REQUIRED: "Final Turnitin Revision",
  FINAL_PAPER_TURNITIN_PASSED: "Final Turnitin Passed",
  FINAL_BLIND_EVALUATION: "Final Evaluation",
  FINAL_EVALUATION_REVISION_REQUIRED: "Final Eval Revision",
  FINAL_BLIND_EVALUATION_PASSED: "Final Eval Passed",
  COMPLETED: "Completed",
  READY_FOR_PRESENTATION: "Ready for Presentation",
  READY_FOR_PUBLICATION: "Ready for Publication",
  ARCHIVED: "Archived",
};

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
  EXTERNAL_EVALUATION_REVISION_REQUIRED: "bg-red-100 text-red-600",
  EXTERNAL_EVALUATION_PASSED: "bg-green-100 text-green-700",
  FOR_IRB_REVIEW: "bg-purple-100 text-purple-700",
  IRB_REVISION_REQUIRED: "bg-red-100 text-red-600",
  PROPOSAL_APPROVED: "bg-green-100 text-green-700",
  RESEARCH_IN_PROGRESS: "bg-blue-100 text-blue-700",
  FINAL_PAPER_SUBMITTED: "bg-yellow-100 text-yellow-700",
  FINAL_PAPER_TURNITIN: "bg-yellow-100 text-yellow-700",
  FINAL_PAPER_TURNITIN_REVISION_REQUIRED: "bg-red-100 text-red-600",
  FINAL_PAPER_TURNITIN_PASSED: "bg-green-100 text-green-700",
  FINAL_BLIND_EVALUATION: "bg-purple-100 text-purple-700",
  FINAL_EVALUATION_REVISION_REQUIRED: "bg-red-100 text-red-600",
  FINAL_BLIND_EVALUATION_PASSED: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-100 text-green-700",
  READY_FOR_PRESENTATION: "bg-green-100 text-green-700",
  READY_FOR_PUBLICATION: "bg-green-100 text-green-700",
  ARCHIVED: "bg-gray-100 text-gray-500",
};

const DEADLINES = [
  { date: "SEP 15", title: "Full Paper Submission", subtitle: "Research Implementation", days: "5 days left", color: "text-red-600" },
  { date: "SEP 22", title: "Turnitin Revision Deadline", subtitle: "Final Papers", days: "12 days left", color: "text-yellow-600" },
  { date: "SEP 30", title: "IRB Document Deadline", subtitle: "Ethics Review", days: "20 days left", color: "text-blue-600" },
];

function getWorkflowProgress(status: string): { stage: number; percent: number } {
  for (let i = 0; i < WORKFLOW_STAGES.length; i++) {
    if (WORKFLOW_STAGES[i].statuses.includes(status)) {
      return { stage: i, percent: Math.round(((i + 1) / WORKFLOW_STAGES.length) * 100) };
    }
  }
  return { stage: 0, percent: 0 };
}

export default function ResearcherDashboard() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<ResearcherStats | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [recentResearch, setRecentResearch] = useState<ResearchItem[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiRequest<ResearcherStats>("/research/stats/researcher", { token }),
      apiRequest<ActionItem[]>("/research/actions", { token }),
      apiRequest<{ items: ResearchItem[] }>("/research?page_size=3", { token }),
      apiRequest<ActivityItem[]>("/research/activity?page_size=5", { token }),
    ])
      .then(([statsData, actionsData, researchData, activityData]) => {
        setStats(statsData);
        setActions(actionsData);
        setRecentResearch(researchData.items);
        setActivity(activityData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const activeResearch = recentResearch.filter(
    (r) => !["DRAFT", "COMPLETED", "ARCHIVED"].includes(r.status)
  );

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
          <p className="text-white/60 text-xs tracking-[0.15em] uppercase mb-1">Research for a Brighter Tomorrow</p>
          <h1 className="font-heading text-3xl font-bold text-white mb-1">
            Welcome, {user?.first_name || "Researcher"}!
          </h1>
          <p className="text-white/80 text-sm">Track your research progress and manage submissions.</p>
        </div>
        <div className="absolute right-8 top-1/2 -translate-y-1/2 text-right hidden lg:block">
          <p className="font-heading text-white/90 text-lg italic">"Knowledge<br/>in service of<br/>society."</p>
          <p className="text-white/50 text-xs mt-1">- Holy Angel University</p>
        </div>
      </div>

      {/* Quick Actions - Researcher Specific */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {[
          { label: "New Submission", desc: "Create a new research", icon: FilePlus, primary: true, action: () => navigate("/research/new") },
          { label: "My Research", desc: "View your projects", icon: FileText, action: () => navigate("/research") },
          { label: "Upload Revision", desc: "Submit revisions", icon: FileUp, action: () => navigate("/actions") },
          { label: "Feedback", desc: "View evaluations", icon: MessageSquare, action: () => navigate("/evaluations") },
          { label: "IRB Status", desc: "Ethics review", icon: Shield, action: () => navigate("/irb") },
          { label: "My Documents", desc: "Manage files", icon: FolderOpen, action: () => navigate("/documents") },
        ].map((action) => (
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

      {/* Action Required */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-base font-bold flex items-center gap-2">
            <AlertCircle size={18} className="text-red-500" />
            Action Required
          </h3>
          {actions.length > 0 && (
            <span className="bg-red-100 text-red-700 text-xs font-semibold px-2.5 py-1 rounded-full">
              {actions.length}
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
        ) : actions.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No action is currently required.</p>
        ) : (
          <div className="space-y-3">
            {actions.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-red-50 rounded-card border border-red-100">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{item.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400 font-mono">{item.tracking_number}</span>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[item.status] || "bg-gray-100 text-gray-600"}`}>
                      {STATUS_LABELS[item.status] || item.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p className="text-xs text-red-600 mt-1">{item.action_required}</p>
                </div>
                <button
                  onClick={() => navigate(`/research/${item.id}`)}
                  className="ml-4 px-3 py-1.5 bg-maroon-700 text-white text-xs font-semibold rounded-control hover:bg-maroon-600 transition-colors"
                >
                  View
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Active Research */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-base font-bold flex items-center gap-2">
            <FileText size={18} className="text-maroon-600" />
            Active Research
          </h3>
        </div>
        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse flex items-center gap-3">
                <div className="h-3 bg-gray-200 rounded w-full" />
              </div>
            ))}
          </div>
        ) : activeResearch.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No active research projects.</p>
        ) : (
          <div className="space-y-4">
            {activeResearch.map((research) => {
              const progress = getWorkflowProgress(research.status);
              return (
                <div key={research.id} className="border border-gray-100 rounded-card p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{research.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-400 font-mono">{research.tracking_number}</span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[research.status] || "bg-gray-100 text-gray-600"}`}>
                          {STATUS_LABELS[research.status] || research.status.replace(/_/g, " ")}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/research/${research.id}`)}
                      className="ml-4 px-3 py-1.5 bg-maroon-700 text-white text-xs font-semibold rounded-control hover:bg-maroon-600 transition-colors flex items-center gap-1"
                    >
                      Open <ArrowRight size={12} />
                    </button>
                  </div>

                  {/* Workflow Progress */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1.5">
                      <span>Progress</span>
                      <span>{progress.percent}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-maroon-600 rounded-full transition-all"
                        style={{ width: `${progress.percent}%` }}
                      />
                    </div>
                    <div className="flex items-center gap-1 mt-2 overflow-x-auto pb-1">
                      {WORKFLOW_STAGES.map((stage, i) => (
                        <div
                          key={stage.label}
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0 ${
                            i < progress.stage
                              ? "bg-green-500 text-white"
                              : i === progress.stage
                              ? "bg-maroon-600 text-white"
                              : "bg-gray-200 text-gray-500"
                          }`}
                        >
                          {i < progress.stage ? "✓" : i + 1}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Summary Cards + Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Research Summary */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-base font-bold mb-4">Research Summary</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "My Research", value: loading ? "—" : String(stats?.total ?? 0), color: "text-maroon-700", bg: "bg-maroon-500/10", icon: FileText },
              { label: "Active", value: loading ? "—" : String(stats?.active ?? 0), color: "text-green-600", bg: "bg-green-500/10", icon: Clock },
              { label: "Requires Action", value: loading ? "—" : String(stats?.action_required ?? 0), color: "text-red-600", bg: "bg-red-500/10", icon: AlertCircle },
              { label: "Completed", value: loading ? "—" : String(stats?.completed ?? 0), color: "text-green-700", bg: "bg-green-500/10", icon: CheckCircle },
            ].map((kpi) => (
              <div key={kpi.label} className="p-3 rounded-card border border-gray-100">
                <div className={`w-8 h-8 rounded-lg ${kpi.bg} flex items-center justify-center mb-2`}>
                  <kpi.icon size={16} className={kpi.color} />
                </div>
                <div className="text-xl font-bold text-gray-800">{kpi.value}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">{kpi.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Deadlines */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-base font-bold flex items-center gap-2 mb-4">
            <Clock size={18} className="text-maroon-600" />
            Upcoming Deadlines
          </h3>
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
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-base font-bold flex items-center gap-2">
            <Clock size={18} className="text-maroon-600" />
            Recent Activity
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
        ) : activity.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No recent activity.</p>
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
