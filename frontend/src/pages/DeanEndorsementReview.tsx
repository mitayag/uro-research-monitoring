import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Download,
} from "lucide-react";
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
  created_at: string | null;
  submitted_at: string | null;
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
};

export default function DeanEndorsementReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [remarks, setRemarks] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [showEndorseConfirm, setShowEndorseConfirm] = useState(false);
  const [showReturnConfirm, setShowReturnConfirm] = useState(false);

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

  const handleEndorse = async () => {
    if (!token || !id) return;
    setActionLoading(true);
    try {
      await apiRequest(`/dean/${id}/endorse`, {
        token,
        method: "POST",
        body: { remarks: remarks.trim() || undefined },
      });
      setToast({ type: "success", message: "Research endorsed to URO successfully" });
      setShowEndorseConfirm(false);
      setRemarks("");
      await fetchData();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || "Failed to endorse research" });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReturn = async () => {
    if (!token || !id) return;
    if (!remarks.trim()) {
      setToast({ type: "error", message: "Remarks are required when returning to researcher" });
      return;
    }
    setActionLoading(true);
    try {
      await apiRequest(`/dean/${id}/return`, {
        token,
        method: "POST",
        body: { remarks: remarks.trim() },
      });
      setToast({ type: "success", message: "Research returned to researcher" });
      setShowReturnConfirm(false);
      setRemarks("");
      await fetchData();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || "Failed to return research" });
    } finally {
      setActionLoading(false);
    }
  };

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
        <button onClick={() => navigate("/dean/endorsements")} className="mt-4 text-maroon-600 hover:underline">
          Back to Endorsements
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
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
        <button onClick={() => navigate("/dean/endorsements")} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold text-gray-800">{research.title}</h1>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
              {STATUS_LABELS[research.status] || research.status.replace(/_/g, " ")}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1 font-mono">{research.tracking_number}</p>
        </div>
      </div>

      {/* Research Information */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Research Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Researcher</span>
            <p className="font-medium">{research.lead_proponent_name}</p>
          </div>
          <div>
            <span className="text-gray-500">Research Type</span>
            <p className="font-medium">{research.nature_of_research || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500">Date Submitted</span>
            <p className="font-medium">{research.submitted_at ? new Date(research.submitted_at).toLocaleDateString() : "—"}</p>
          </div>
          <div>
            <span className="text-gray-500">Target Journal</span>
            <p className="font-medium">{research.target_journal || "—"}</p>
          </div>
          {research.research_agenda && (
            <div className="col-span-2">
              <span className="text-gray-500">Abstract</span>
              <p className="font-medium mt-1">{research.research_agenda}</p>
            </div>
          )}
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
          <div>
            <span className="text-gray-500">Endorsement Status</span>
            <p className="font-medium text-amber-600">Awaiting Dean Endorsement</p>
          </div>
        </div>
      </div>

      {/* Authors */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Researchers / Authors</h3>
        <div className="space-y-2">
          {research.authors.map((author) => (
            <div key={author.id} className="flex items-center gap-3 text-sm">
              <span className="font-medium">{author.name}</span>
              {author.is_lead && <span className="text-xs bg-maroon-100 text-maroon-700 px-2 py-0.5 rounded-full">Lead</span>}
              {author.affiliation && <span className="text-gray-400">• {author.affiliation}</span>}
              {author.email && <span className="text-gray-400">• {author.email}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Documents */}
      {research.documents.length > 0 && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Submitted Documents</h3>
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

      {/* Dean Actions */}
      {research.status === "FOR_DEAN_ENDORSEMENT" && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card space-y-4">
          <h3 className="font-heading text-sm font-bold">Dean Decision</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Dean Remarks</label>
            <textarea
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Enter your remarks (required for return, optional for endorsement)..."
              rows={3}
              className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (remarks.trim()) {
                  setShowReturnConfirm(true);
                } else {
                  setToast({ type: "error", message: "Remarks are required when returning to researcher" });
                }
              }}
              disabled={actionLoading}
              className="px-4 py-2.5 rounded-control text-sm font-semibold border border-red-200 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              Return to Researcher
            </button>
            <button
              onClick={() => setShowEndorseConfirm(true)}
              disabled={actionLoading}
              className="px-4 py-2.5 rounded-control text-sm font-semibold bg-maroon-700 text-white hover:bg-maroon-600 transition-colors disabled:opacity-50"
            >
              Endorse to URO
            </button>
          </div>
        </div>
      )}

      {/* Endorse Confirmation Modal */}
      {showEndorseConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowEndorseConfirm(false)}>
          <div className="bg-white rounded-modal p-6 w-full max-w-md shadow-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-heading text-lg font-bold mb-2">Endorse to URO?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will forward the research submission to URO for initial review and processing.
            </p>
            {remarks.trim() && (
              <div className="mb-4 p-3 bg-gray-50 rounded-card text-sm">
                <p className="font-medium text-gray-700">Your Remarks:</p>
                <p className="text-gray-600 mt-1">{remarks}</p>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowEndorseConfirm(false)}
                className="px-4 py-2 rounded-control text-sm font-medium border border-gray-200 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleEndorse}
                disabled={actionLoading}
                className="px-4 py-2 rounded-control text-sm font-semibold text-white bg-maroon-700 hover:bg-maroon-600 disabled:opacity-50"
              >
                {actionLoading ? "Endorsing..." : "Endorse to URO"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Return Confirmation Modal */}
      {showReturnConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowReturnConfirm(false)}>
          <div className="bg-white rounded-modal p-6 w-full max-w-md shadow-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-heading text-lg font-bold mb-2">Return to Researcher?</h3>
            <p className="text-sm text-gray-600 mb-4">
              The researcher will be notified and asked to revise the submission.
            </p>
            <div className="mb-4 p-3 bg-red-50 rounded-card text-sm">
              <p className="font-medium text-red-700">Your Remarks:</p>
              <p className="text-red-600 mt-1">{remarks}</p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowReturnConfirm(false)}
                className="px-4 py-2 rounded-control text-sm font-medium border border-gray-200 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleReturn}
                disabled={actionLoading}
                className="px-4 py-2 rounded-control text-sm font-semibold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50"
              >
                {actionLoading ? "Returning..." : "Return to Researcher"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
