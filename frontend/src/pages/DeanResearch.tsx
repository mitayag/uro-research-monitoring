import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ArrowRight } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface ResearchItem {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  nature_of_research: string | null;
  updated_at: string | null;
  created_at: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  FOR_DEAN_ENDORSEMENT: "Awaiting Endorsement",
  ENDORSED_TO_URO: "Endorsed",
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

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  SUBMITTED: "bg-blue-100 text-blue-700",
  FOR_DEAN_ENDORSEMENT: "bg-amber-100 text-amber-700",
  ENDORSED_TO_URO: "bg-blue-100 text-blue-700",
  URO_RECEIVED: "bg-purple-100 text-purple-700",
  INITIAL_REVIEW: "bg-yellow-100 text-yellow-700",
  INITIAL_REVISION_REQUIRED: "bg-red-100 text-red-600",
  INITIAL_REVIEW_PASSED: "bg-green-100 text-green-700",
  PROPOSAL_TURNITIN: "bg-yellow-100 text-yellow-700",
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

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "FOR_DEAN_ENDORSEMENT", label: "Pending Endorsement" },
  { value: "URO_PROCESSING", label: "URO Processing" },
  { value: "EXTERNAL_EVALUATION", label: "Under Evaluation" },
  { value: "REVISION", label: "For Revision" },
  { value: "IRB", label: "IRB" },
  { value: "IMPLEMENTATION", label: "Implementation" },
  { value: "COMPLETED", label: "Completed" },
];

const URO_PROCESSING_STATUSES = ["ENDORSED_TO_URO", "URO_RECEIVED", "INITIAL_REVIEW", "INITIAL_REVISION_REQUIRED", "INITIAL_REVISION_SUBMITTED", "INITIAL_REVIEW_PASSED", "PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "PROPOSAL_TURNITIN_RESUBMITTED", "PROPOSAL_TURNITIN_PASSED"];
const EVALUATION_STATUSES = ["READY_FOR_EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION_REVISION_REQUIRED", "SELECTIVE_EXTERNAL_REEVALUATION", "EXTERNAL_EVALUATION_PASSED"];
const REVISION_STATUSES = ["INITIAL_REVISION_REQUIRED", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "EXTERNAL_EVALUATION_REVISION_REQUIRED", "IRB_REVISION_REQUIRED", "FINAL_PAPER_TURNITIN_REVISION_REQUIRED", "FINAL_EVALUATION_REVISION_REQUIRED"];
const IRB_STATUSES = ["FOR_IRB_REVIEW", "IRB_REVISION_REQUIRED", "PROPOSAL_APPROVED"];
const IMPLEMENTATION_STATUSES = ["RESEARCH_IN_PROGRESS", "FINAL_PAPER_DUE", "FINAL_PAPER_SUBMITTED", "FINAL_PAPER_TURNITIN", "FINAL_PAPER_TURNITIN_REVISION_REQUIRED", "FINAL_PAPER_TURNITIN_PASSED", "FINAL_BLIND_EVALUATION", "FINAL_EVALUATION_REVISION_REQUIRED", "SELECTIVE_FINAL_REEVALUATION", "FINAL_BLIND_EVALUATION_PASSED"];
const COMPLETED_STATUSES = ["COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED"];

function filterByCategory(status: string, filter: string): boolean {
  if (!filter) return true;
  switch (filter) {
    case "FOR_DEAN_ENDORSEMENT": return status === "FOR_DEAN_ENDORSEMENT";
    case "URO_PROCESSING": return URO_PROCESSING_STATUSES.includes(status);
    case "EXTERNAL_EVALUATION": return EVALUATION_STATUSES.includes(status);
    case "REVISION": return REVISION_STATUSES.includes(status);
    case "IRB": return IRB_STATUSES.includes(status);
    case "IMPLEMENTATION": return IMPLEMENTATION_STATUSES.includes(status);
    case "COMPLETED": return COMPLETED_STATUSES.includes(status);
    default: return true;
  }
}

export default function DeanResearch() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [items, setItems] = useState<ResearchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", "20");
    if (search) params.set("search", search);
    // Map frontend filter to backend status_filter
    if (filter === "FOR_DEAN_ENDORSEMENT") params.set("status_filter", "FOR_DEAN_ENDORSEMENT");
    else if (filter === "COMPLETED") params.set("status_filter", "COMPLETED");
    apiRequest<{ items: ResearchItem[]; total: number }>(`/dean/research?${params.toString()}`, { token })
      .then((data) => { setItems(data.items); setTotal(data.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, search, filter, page]);

  const filteredItems = filter && filter !== "FOR_DEAN_ENDORSEMENT" && filter !== "COMPLETED"
    ? items.filter((r) => filterByCategory(r.status, filter))
    : items;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Research Projects</h1>
        <p className="text-sm text-gray-500 mt-1">Research projects in your academic unit</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 relative min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title or ID..."
            className="w-full pl-9 pr-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => { setFilter(f.value); setPage(1); }}
              className={`px-3 py-1.5 rounded-control text-xs font-medium transition-colors ${
                filter === f.value
                  ? "bg-maroon-700 text-white"
                  : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="bg-white rounded-card border border-gray-200 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />
            ))}
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-gray-400">No research projects found for your academic unit.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs font-semibold text-gray-500 uppercase">
                <th className="px-4 py-3">Research ID</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Researcher</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Last Updated</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.tracking_number}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-800 max-w-xs truncate">{item.title}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{item.lead_proponent_name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[item.status] || "bg-gray-100 text-gray-600"}`}>
                      {STATUS_LABELS[item.status] || item.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {item.updated_at ? new Date(item.updated_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => navigate(`/dean/research/${item.id}`)}
                      className="flex items-center gap-1 text-xs font-medium text-maroon-700 hover:text-maroon-600"
                    >
                      View <ArrowRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">Showing {filteredItems.length} of {total}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-control text-sm border border-gray-200 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={filteredItems.length < 20}
              className="px-3 py-1.5 rounded-control text-sm border border-gray-200 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
