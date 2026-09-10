import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  History,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface ResearchDetail {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_id: string;
  lead_proponent_name: string | null;
  status: string;
  nature_of_research: string | null;
  created_at: string | null;
  submitted_at: string | null;
  school_name: string | null;
  department_name: string | null;
  assigned_dean_name: string | null;
  authors: { id: string; name: string; is_lead: boolean; affiliation: string | null }[];
}

interface WorkflowAction {
  action: string;
  label: string;
  variant: "primary" | "danger" | "secondary";
  requiresConfirm?: boolean;
}

interface HistoryEntry {
  id: string;
  action: string;
  new_status: string;
  prior_status: string | null;
  actor_role: string;
  remarks: string | null;
  created_at: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "For Dean Endorsement",
  ENDORSED_TO_URO: "Endorsed to URO",
  URO_RECEIVED: "Received by URO",
  INITIAL_REVIEW: "Under Initial Review",
  INITIAL_REVISION_REQUIRED: "Revision Required",
  INITIAL_REVISION_SUBMITTED: "Revision Submitted",
  INITIAL_REVIEW_PASSED: "Initial Review Passed",
  PROPOSAL_TURNITIN: "Turnitin Checking",
  PROPOSAL_TURNITIN_REVISION_REQUIRED: "Turnitin Revision Required",
  PROPOSAL_TURNITIN_RESUBMITTED: "Turnitin Revision Submitted",
  PROPOSAL_TURNITIN_PASSED: "Turnitin Passed",
  READY_FOR_EXTERNAL_EVALUATION: "Ready for External Evaluation",
  EXTERNAL_EVALUATION: "External Evaluation",
  EXTERNAL_EVALUATION_PASSED: "External Evaluation Passed",
  FOR_IRB_REVIEW: "IRB Review",
  PROPOSAL_APPROVED: "Proposal Approved",
  RESEARCH_IN_PROGRESS: "Research In Progress",
  COMPLETED: "Completed",
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
};

const WORKFLOW_ACTIONS: Record<string, WorkflowAction[]> = {
  ENDORSED_TO_URO: [
    { action: "RECEIVE_BY_URO", label: "Receive Submission", variant: "primary" },
  ],
  URO_RECEIVED: [
    { action: "BEGIN_INITIAL_REVIEW", label: "Start Initial Review", variant: "primary" },
  ],
  INITIAL_REVIEW: [
    { action: "INITIAL_REVIEW_PASS", label: "Pass Initial Review", variant: "primary", requiresConfirm: true },
    { action: "INITIAL_REVIEW_REVISION", label: "Require Revision", variant: "danger", requiresConfirm: true },
  ],
  INITIAL_REVISION_REQUIRED: [
    { action: "RESUBMIT_INITIAL_REVISION", label: "Submit Revision", variant: "primary" },
  ],
  INITIAL_REVISION_SUBMITTED: [
    { action: "BEGIN_INITIAL_REVIEW", label: "Start Review", variant: "primary" },
  ],
  INITIAL_REVIEW_PASSED: [
    { action: "BEGIN_PROPOSAL_TURNITIN", label: "Begin Turnitin Check", variant: "primary" },
  ],
  PROPOSAL_TURNITIN: [
    { action: "TURNITIN_PASSED", label: "Approve Turnitin", variant: "primary", requiresConfirm: true },
    { action: "TURNITIN_REVISION", label: "Require Revision", variant: "danger", requiresConfirm: true },
  ],
  PROPOSAL_TURNITIN_REVISION_REQUIRED: [
    { action: "RESUBMIT_TURNITIN_REVISION", label: "Submit Revised Proposal", variant: "primary" },
  ],
  PROPOSAL_TURNITIN_RESUBMITTED: [
    { action: "BEGIN_PROPOSAL_TURNITIN", label: "Begin Turnitin Check", variant: "primary" },
  ],
  PROPOSAL_TURNITIN_PASSED: [
    { action: "READY_FOR_EXTERNAL_EVAL", label: "Ready for External Evaluation", variant: "primary" },
  ],
};

const PROGRESS_STEPS = [
  { label: "Application", statuses: ["DRAFT", "SUBMITTED"] },
  { label: "Dean Endorsement", statuses: ["FOR_DEAN_ENDORSEMENT", "ENDORSED_TO_URO"] },
  { label: "URO Initial Review", statuses: ["URO_RECEIVED", "INITIAL_REVIEW", "INITIAL_REVISION_REQUIRED", "INITIAL_REVISION_SUBMITTED", "INITIAL_REVIEW_PASSED"] },
  { label: "Proposal Turnitin", statuses: ["PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "PROPOSAL_TURNITIN_RESUBMITTED", "PROPOSAL_TURNITIN_PASSED"] },
  { label: "External Evaluation", statuses: ["READY_FOR_EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION_PASSED"] },
  { label: "IRB Review", statuses: ["FOR_IRB_REVIEW", "IRB_REVISION_REQUIRED", "PROPOSAL_APPROVED"] },
  { label: "Research Implementation", statuses: ["RESEARCH_IN_PROGRESS", "FINAL_PAPER_DUE", "FINAL_PAPER_SUBMITTED"] },
  { label: "Final Evaluation", statuses: ["FINAL_PAPER_TURNITIN", "FINAL_BLIND_EVALUATION", "FINAL_BLIND_EVALUATION_PASSED"] },
  { label: "Completed", statuses: ["COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED"] },
];

function getStepStatus(currentStatus: string, stepStatuses: string[]): "completed" | "current" | "pending" | "revision" {
  if (stepStatuses.includes(currentStatus)) {
    if (currentStatus.includes("REVISION") || currentStatus.includes("REVISION_REQUIRED")) {
      return "revision";
    }
    return "current";
  }
  const allStatuses = Object.values(STATUS_LABELS);
  const currentIdx = allStatuses.indexOf(currentStatus);
  const stepFirstIdx = Math.min(...stepStatuses.map(s => allStatuses.indexOf(s)).filter(i => i >= 0));
  if (currentIdx > stepFirstIdx) return "completed";
  return "pending";
}

export default function ResearchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{ action: string; label: string; variant: string } | null>(null);
  const [revisionModal, setRevisionModal] = useState<{ action: string; label: string } | null>(null);
  const [remarks, setRemarks] = useState("");
  const [revisionInstructions, setRevisionInstructions] = useState("");
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    if (!token || !id) return;
    try {
      const [researchData, historyData] = await Promise.all([
        apiRequest<ResearchDetail>(`/research/${id}`, { token }),
        apiRequest<HistoryEntry[]>(`/research/${id}/history`, { token }),
      ]);
      setResearch(researchData);
      setHistory(historyData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const executeAction = async (action: string, body?: Record<string, string>) => {
    if (!token || !id) return;
    setActionLoading(true);
    try {
      // Check if this is a Phase 3 specific action
      const phase3Actions = ["RECEIVE_BY_URO", "BEGIN_INITIAL_REVIEW", "INITIAL_REVIEW_PASS", "INITIAL_REVIEW_REVISION", "RESUBMIT_INITIAL_REVISION", "BEGIN_PROPOSAL_TURNITIN", "TURNITIN_PASSED", "TURNITIN_REVISION", "RESUBMIT_TURNITIN_REVISION", "READY_FOR_EXTERNAL_EVAL"];

      if (phase3Actions.includes(action)) {
        // Use phase3 endpoints
        const endpointMap: Record<string, string> = {
          RECEIVE_BY_URO: `/research/${id}/receive`,
          BEGIN_INITIAL_REVIEW: `/research/${id}/initial-review`,
          INITIAL_REVIEW_PASS: `/research/${id}/initial-review/pass`,
          INITIAL_REVIEW_REVISION: `/research/${id}/initial-review/revision`,
          RESUBMIT_INITIAL_REVISION: `/research/${id}/initial-review/resubmit`,
          BEGIN_PROPOSAL_TURNITIN: `/research/${id}/transition`,
          TURNITIN_PASSED: `/research/${id}/turnitin/pass`,
          TURNITIN_REVISION: `/research/${id}/turnitin/revision`,
          RESUBMIT_TURNITIN_REVISION: `/research/${id}/turnitin/resubmit`,
          READY_FOR_EXTERNAL_EVAL: `/research/${id}/transition`,
        };

        const endpoint = endpointMap[action] || `/research/${id}/transition`;
        const method = ["RECEIVE_BY_URO", "BEGIN_INITIAL_REVIEW"].includes(action) ? "POST" : "POST";
        const bodyData = body || (["INITIAL_REVIEW_PASS", "INITIAL_REVIEW_REVISION", "INITIAL_REVISION_REQUIRED", "TURNITIN_PASSED", "TURNITIN_REVISION"].includes(action) ? { remarks_researcher: remarks } : {});

        await apiRequest(endpoint, { token, method, body: bodyData });
      } else {
        // Use standard transition endpoint
        await apiRequest(`/research/${id}/transition`, {
          token,
          method: "POST",
          body: { action, remarks },
        });
      }

      setToast({ type: "success", message: `Action "${action}" completed successfully` });
      setRemarks("");
      setRevisionInstructions("");
      await fetchData();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || "Action failed" });
    } finally {
      setActionLoading(false);
      setConfirmModal(null);
      setRevisionModal(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (!research) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Research not found</p>
        <button onClick={() => navigate("/research")} className="mt-4 text-maroon-600 hover:underline">
          Back to Research
        </button>
      </div>
    );
  }

  const availableActions = WORKFLOW_ACTIONS[research.status] || [];
  const userRoles = user?.roles || [];
  const canPerform = (action: string) => {
    const roleMap: Record<string, string[]> = {
      RECEIVE_BY_URO: ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
      BEGIN_INITIAL_REVIEW: ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
      INITIAL_REVIEW_PASS: ["URO_DIRECTOR", "ADMIN"],
      INITIAL_REVIEW_REVISION: ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
      RESUBMIT_INITIAL_REVISION: ["RESEARCHER", "ADMIN"],
      BEGIN_PROPOSAL_TURNITIN: ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
      TURNITIN_PASSED: ["URO_DIRECTOR", "ADMIN"],
      TURNITIN_REVISION: ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
      RESUBMIT_TURNITIN_REVISION: ["RESEARCHER", "ADMIN"],
      READY_FOR_EXTERNAL_EVAL: ["URO_DIRECTOR", "ADMIN"],
      SUBMIT: ["RESEARCHER", "ADMIN"],
      FORWARD_TO_DEAN: ["RESEARCHER", "ADMIN"],
      DEAN_ENDORSE: ["DEAN", "ADMIN"],
    };
    const allowed = roleMap[action] || [];
    return allowed.some(r => userRoles.includes(r));
  };

  return (
    <div className="p-6 space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-control text-sm font-medium shadow-modal ${
          toast.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
        }`}>
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-3 underline">Dismiss</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/research")} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold text-gray-800">{research.title}</h1>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[research.status] || "bg-gray-100 text-gray-600"}`}>
              {STATUS_LABELS[research.status] || research.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1 font-mono">{research.tracking_number}</p>
        </div>
      </div>

      {/* Progress Tracker */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Workflow Progress</h3>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {PROGRESS_STEPS.map((step, i) => {
            const stepStatus = getStepStatus(research.status, step.statuses);
            return (
              <div key={step.label} className="flex items-center gap-1 shrink-0">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  stepStatus === "completed" ? "bg-green-500 text-white" :
                  stepStatus === "current" ? "bg-blue-500 text-white" :
                  stepStatus === "revision" ? "bg-red-500 text-white" :
                  "bg-gray-200 text-gray-500"
                }`}>
                  {stepStatus === "completed" ? "✓" : i + 1}
                </div>
                <span className={`text-[10px] whitespace-nowrap ${
                  stepStatus === "current" ? "text-blue-600 font-semibold" :
                  stepStatus === "revision" ? "text-red-600 font-semibold" :
                  "text-gray-400"
                }`}>
                  {step.label}
                </span>
                {i < PROGRESS_STEPS.length - 1 && <div className="w-4 h-px bg-gray-300" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      {availableActions.length > 0 && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Available Actions</h3>
          <div className="flex flex-wrap gap-3">
            {availableActions.map((act) => {
              if (!canPerform(act.action)) return null;
              if (act.action === "INITIAL_REVIEW_REVISION" || act.action === "TURNITIN_REVISION") {
                return (
                  <button
                    key={act.action}
                    onClick={() => setRevisionModal({ action: act.action, label: act.label })}
                    disabled={actionLoading}
                    className={`px-4 py-2.5 rounded-control text-sm font-semibold transition-colors ${
                      act.variant === "danger"
                        ? "bg-red-600 text-white hover:bg-red-500"
                        : "bg-maroon-700 text-white hover:bg-maroon-600"
                    } disabled:opacity-50`}
                  >
                    {act.label}
                  </button>
                );
              }
              return (
                <button
                  key={act.action}
                  onClick={() => {
                    if (act.requiresConfirm) {
                      setConfirmModal({ action: act.action, label: act.label, variant: act.variant });
                    } else {
                      executeAction(act.action);
                    }
                  }}
                  disabled={actionLoading}
                  className={`px-4 py-2.5 rounded-control text-sm font-semibold transition-colors ${
                    act.variant === "danger"
                      ? "bg-red-600 text-white hover:bg-red-500"
                      : "bg-maroon-700 text-white hover:bg-maroon-600"
                  } disabled:opacity-50`}
                >
                  {act.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Research Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Research Information</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Principal Researcher</span>
              <span className="font-medium">{research.lead_proponent_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Co-Researchers</span>
              <span className="font-medium">{research.authors.filter(a => !a.is_lead).map(a => a.name).join(", ") || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Created</span>
              <span className="font-medium">{research.created_at ? new Date(research.created_at).toLocaleDateString() : "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Submitted</span>
              <span className="font-medium">{research.submitted_at ? new Date(research.submitted_at).toLocaleDateString() : "—"}</span>
            </div>
          </div>
        </div>

        {/* Academic Affiliation */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Academic Affiliation</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Department</span>
              <span className="font-medium">{research.department_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">School / College</span>
              <span className="font-medium">{research.school_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Endorsing Dean</span>
              <span className="font-medium">{research.assigned_dean_name || "—"}</span>
            </div>
            {research.status === "FOR_DEAN_ENDORSEMENT" && (
              <div className="flex justify-between">
                <span className="text-gray-500">Endorsement Status</span>
                <span className="font-medium text-amber-600">Awaiting Dean Endorsement</span>
              </div>
            )}
          </div>
        </div>

        {/* Workflow Timeline */}
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4 flex items-center gap-2">
            <History size={16} className="text-maroon-600" />
            Workflow Timeline
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {history.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No history yet</p>
            ) : (
              history.map((h) => (
                <div key={h.id} className="flex items-start gap-3 text-sm">
                  <div className="w-2 h-2 rounded-full bg-maroon-500 mt-1.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800">{h.action.replace(/_/g, " ")}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                        h.new_status.includes("REVISION") ? "bg-red-100 text-red-600" : "bg-green-100 text-green-700"
                      }`}>
                        {STATUS_LABELS[h.new_status] || h.new_status}
                      </span>
                    </div>
                    {h.remarks && <p className="text-xs text-gray-500 mt-0.5">{h.remarks}</p>}
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {h.created_at ? new Date(h.created_at).toLocaleString() : ""} · {h.actor_role}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Confirm Modal */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setConfirmModal(null)}>
          <div className="bg-white rounded-modal p-6 w-full max-w-md shadow-modal" onClick={e => e.stopPropagation()}>
            <h3 className="font-heading text-lg font-bold mb-2">Confirm Action</h3>
            <p className="text-sm text-gray-600 mb-4">Are you sure you want to: <strong>{confirmModal.label}</strong>?</p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Remarks (optional)</label>
              <textarea
                value={remarks}
                onChange={e => setRemarks(e.target.value)}
                className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
                rows={2}
                placeholder="Add remarks..."
              />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 rounded-control text-sm font-medium border border-gray-200 hover:bg-gray-50">
                Cancel
              </button>
              <button
                onClick={() => executeAction(confirmModal.action)}
                disabled={actionLoading}
                className={`px-4 py-2 rounded-control text-sm font-semibold text-white disabled:opacity-50 ${
                  confirmModal.variant === "danger" ? "bg-red-600 hover:bg-red-500" : "bg-maroon-700 hover:bg-maroon-600"
                }`}
              >
                {actionLoading ? "Processing..." : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Revision Modal */}
      {revisionModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setRevisionModal(null)}>
          <div className="bg-white rounded-modal p-6 w-full max-w-lg shadow-modal" onClick={e => e.stopPropagation()}>
            <h3 className="font-heading text-lg font-bold mb-2">Require Revision</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Review Findings</label>
                <textarea
                  value={remarks}
                  onChange={e => setRemarks(e.target.value)}
                  className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
                  rows={3}
                  placeholder="Describe the findings..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Revision Instructions</label>
                <textarea
                  value={revisionInstructions}
                  onChange={e => setRevisionInstructions(e.target.value)}
                  className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
                  rows={3}
                  placeholder="Specific instructions for the researcher..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setRevisionModal(null)} className="px-4 py-2 rounded-control text-sm font-medium border border-gray-200 hover:bg-gray-50">
                Cancel
              </button>
              <button
                onClick={() => executeAction(revisionModal.action, { remarks_researcher: remarks, revision_instructions: revisionInstructions })}
                disabled={actionLoading || !remarks}
                className="px-4 py-2 rounded-control text-sm font-semibold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50"
              >
                {actionLoading ? "Sending..." : "Send Revision Request"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
