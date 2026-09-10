import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, Download } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface ResearchDetail {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  nature_of_research: string | null;
  research_agenda: string | null;
  target_journal: string | null;
  is_continuation: boolean;
  continuation_ref: string | null;
  mobile_number: string | null;
  institutional_email: string | null;
  created_at: string | null;
  submitted_at: string | null;
  updated_at: string | null;
  school_name: string | null;
  department_name: string | null;
  assigned_dean_name: string | null;
  authors: { id: string; name: string; affiliation: string | null; email: string | null; is_lead: boolean }[];
  documents: { id: string; document_type: string; active_version: { id: string; version_number: number; original_filename: string; file_size: number; mime_type: string; uploaded_at: string | null } | null }[];
  history: { id: string; prior_status: string | null; new_status: string; action: string; actor_role: string; remarks: string | null; created_at: string | null }[];
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "Awaiting Dean Endorsement",
  ENDORSED_TO_URO: "Endorsed to URO",
  URO_RECEIVED: "URO Received",
  INITIAL_REVIEW: "Initial Review",
  INITIAL_REVISION_REQUIRED: "Revision Required",
  INITIAL_REVIEW_PASSED: "Review Passed",
  PROPOSAL_TURNITIN: "Turnitin",
  PROPOSAL_TURNITIN_PASSED: "Turnitin Passed",
  READY_FOR_EXTERNAL_EVALUATION: "Ready for External",
  EXTERNAL_EVALUATION: "External Eval",
  EXTERNAL_EVALUATION_PASSED: "External Passed",
  FOR_IRB_REVIEW: "IRB Review",
  PROPOSAL_APPROVED: "Approved",
  RESEARCH_IN_PROGRESS: "In Progress",
  FINAL_PAPER_SUBMITTED: "Final Paper",
  FINAL_PAPER_TURNITIN: "Final Turnitin",
  FINAL_PAPER_TURNITIN_PASSED: "Final Turnitin Passed",
  FINAL_BLIND_EVALUATION: "Final Eval",
  FINAL_BLIND_EVALUATION_PASSED: "Final Eval Passed",
  COMPLETED: "Completed",
  READY_FOR_PRESENTATION: "Ready for Presentation",
  READY_FOR_PUBLICATION: "Ready for Publication",
  ARCHIVED: "Archived",
};

const PROGRESS_STEPS = [
  { label: "Submission", statuses: ["DRAFT", "SUBMITTED"] },
  { label: "Dean Endorsement", statuses: ["FOR_DEAN_ENDORSEMENT", "ENDORSED_TO_URO"] },
  { label: "URO Processing", statuses: ["URO_RECEIVED", "INITIAL_REVIEW", "INITIAL_REVISION_REQUIRED", "INITIAL_REVISION_SUBMITTED", "INITIAL_REVIEW_PASSED"] },
  { label: "Turnitin", statuses: ["PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "PROPOSAL_TURNITIN_RESUBMITTED", "PROPOSAL_TURNITIN_PASSED"] },
  { label: "External Eval", statuses: ["READY_FOR_EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION_PASSED"] },
  { label: "IRB", statuses: ["FOR_IRB_REVIEW", "IRB_REVISION_REQUIRED", "PROPOSAL_APPROVED"] },
  { label: "Implementation", statuses: ["RESEARCH_IN_PROGRESS", "FINAL_PAPER_DUE", "FINAL_PAPER_SUBMITTED"] },
  { label: "Final Eval", statuses: ["FINAL_PAPER_TURNITIN", "FINAL_BLIND_EVALUATION", "FINAL_BLIND_EVALUATION_PASSED"] },
  { label: "Completed", statuses: ["COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED"] },
];

function getStepStatus(currentStatus: string, stepStatuses: string[]): "completed" | "current" | "pending" | "revision" {
  if (stepStatuses.includes(currentStatus)) {
    if (currentStatus.includes("REVISION") || currentStatus.includes("REVISION_REQUIRED")) return "revision";
    return "current";
  }
  const allStatuses = Object.keys(STATUS_LABELS);
  const currentIdx = allStatuses.indexOf(currentStatus);
  const stepFirstIdx = Math.min(...stepStatuses.map(s => allStatuses.indexOf(s)).filter(i => i >= 0));
  if (currentIdx > stepFirstIdx) return "completed";
  return "pending";
}

export default function DeanResearchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!token || !id) return;
    try {
      const data = await apiRequest<ResearchDetail>(`/dean/${id}`, { token });
      setResearch(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (!research) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Research not found</p>
        <button onClick={() => navigate("/dean/research")} className="mt-4 text-maroon-600 hover:underline">
          Back to Research
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/dean/research")} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold text-gray-800">{research.title}</h1>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
              {STATUS_LABELS[research.status] || research.status.replace(/_/g, " ")}
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

      {/* Research Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Research Information</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Principal Researcher</span>
              <span className="font-medium">{research.lead_proponent_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Research Type</span>
              <span className="font-medium">{research.nature_of_research || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Target Journal</span>
              <span className="font-medium">{research.target_journal || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Submitted</span>
              <span className="font-medium">{research.submitted_at ? new Date(research.submitted_at).toLocaleDateString() : "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Updated</span>
              <span className="font-medium">{research.updated_at ? new Date(research.updated_at).toLocaleDateString() : "—"}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Researchers / Authors</h3>
          <div className="space-y-2">
            {research.authors.map((author) => (
              <div key={author.id} className="flex items-center gap-2 text-sm">
                <span className="font-medium">{author.name}</span>
                {author.is_lead && <span className="text-xs bg-maroon-100 text-maroon-700 px-2 py-0.5 rounded-full">Lead</span>}
                {author.email && <span className="text-gray-400 text-xs">• {author.email}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Academic Affiliation */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Academic Affiliation</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Department</span>
            <p className="font-medium">{research.department_name || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500">School / College</span>
            <p className="font-medium">{research.school_name || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500">Endorsing Dean</span>
            <p className="font-medium">{research.assigned_dean_name || "—"}</p>
          </div>
        </div>
      </div>

      {/* Abstract */}
      {research.research_agenda && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Abstract</h3>
          <p className="text-sm text-gray-600">{research.research_agenda}</p>
        </div>
      )}

      {/* Documents */}
      {research.documents.length > 0 && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Documents</h3>
          <div className="space-y-2">
            {research.documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-card">
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-maroon-600" />
                  <div>
                    <p className="text-sm font-medium">{doc.active_version?.original_filename || doc.document_type}</p>
                    <p className="text-xs text-gray-400">
                      {doc.document_type} • v{doc.active_version?.version_number || 1}
                      {doc.active_version?.file_size && ` • ${(doc.active_version.file_size / 1024 / 1024).toFixed(1)} MB`}
                    </p>
                  </div>
                </div>
                {doc.active_version && (
                  <Download size={16} className="text-gray-400 cursor-pointer hover:text-maroon-600" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflow History */}
      {research.history.length > 0 && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Workflow History</h3>
          <div className="space-y-3">
            {research.history.map((h) => (
              <div key={h.id} className="flex items-start gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-maroon-500 mt-1.5 shrink-0" />
                <div className="flex-1">
                  <p className="font-medium">
                    {h.action.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase())}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-400">{h.actor_role}</span>
                    {h.created_at && <span className="text-xs text-gray-400">• {new Date(h.created_at).toLocaleString()}</span>}
                  </div>
                  {h.remarks && <p className="text-xs text-gray-500 mt-1">{h.remarks}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
