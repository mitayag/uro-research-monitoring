import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Upload, Filter, Download } from "lucide-react";
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
  authors: { name: string; is_lead: boolean }[];
}

interface StatsResponse {
  total: number;
  by_status: Record<string, number>;
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  SUBMITTED: "bg-blue-100 text-blue-700",
  FOR_DEAN_ENDORSEMENT: "bg-blue-100 text-blue-700",
  ENDORSED_TO_URO: "bg-blue-100 text-blue-700",
  INITIAL_EVALUATION: "bg-yellow-100 text-yellow-700",
  PROPOSAL_TURNITIN: "bg-yellow-100 text-yellow-700",
  PROPOSAL_TURNITIN_PASSED: "bg-green-100 text-green-700",
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

const PIPELINE = [
  { label: "Ongoing", color: "bg-status-success", statuses: ["SUBMITTED", "FOR_DEAN_ENDORSEMENT", "ENDORSED_TO_URO", "INITIAL_EVALUATION", "PROPOSAL_TURNITIN", "PROPOSAL_TURNITIN_PASSED", "EXTERNAL_EVALUATION", "EXTERNAL_EVALUATION_PASSED", "FOR_IRB_REVIEW", "PROPOSAL_APPROVED", "RESEARCH_IN_PROGRESS", "FINAL_PAPER_SUBMITTED", "FINAL_PAPER_TURNITIN", "FINAL_PAPER_TURNITIN_PASSED", "FINAL_BLIND_EVALUATION", "FINAL_BLIND_EVALUATION_PASSED"] },
  { label: "For Revision", color: "bg-status-warning", statuses: ["INITIAL_EVALUATION_REVISION_REQUIRED", "PROPOSAL_TURNITIN_REVISION_REQUIRED", "EXTERNAL_EVALUATION_REVISION_REQUIRED", "SELECTIVE_EXTERNAL_REEVALUATION", "IRB_REVISION_REQUIRED", "FINAL_PAPER_TURNITIN_REVISION_REQUIRED", "FINAL_EVALUATION_REVISION_REQUIRED", "SELECTIVE_FINAL_REEVALUATION"] },
  { label: "Draft", color: "bg-status-neutral", statuses: ["DRAFT"] },
  { label: "Completed", color: "bg-status-success", statuses: ["COMPLETED", "READY_FOR_PRESENTATION", "READY_FOR_PUBLICATION", "ARCHIVED"] },
];

export default function Research() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<ResearchItem[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 10;

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiRequest<StatsResponse>("/research/stats/summary", { token }),
      apiRequest<{ items: ResearchItem[]; total: number }>(`/research?page=${page}&page_size=${PAGE_SIZE}${search ? `&search=${encodeURIComponent(search)}` : ""}`, { token }),
    ])
      .then(([statsData, researchData]) => {
        setStats(statsData);
        setItems(researchData.items);
        setTotal(researchData.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, page, search]);

  const pipelineCounts = PIPELINE.map((p) => ({
    ...p,
    count: p.statuses.reduce((sum, s) => sum + (stats?.by_status?.[s] ?? 0), 0),
  }));
  const pipelineTotal = pipelineCounts.reduce((sum, p) => sum + p.count, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Hero */}
      <div
        className="rounded-xl overflow-hidden relative h-36 flex items-center px-8"
        style={{
          background: "linear-gradient(135deg, #5A0E16 0%, #7E1320 40%, rgba(126,19,32,0.7) 100%)",
        }}
      >
        <div className="relative z-10">
          <p className="text-white/60 text-xs tracking-[0.15em] uppercase mb-1">Research for a Brighter Tomorrow</p>
          <h1 className="font-heading text-3xl font-bold text-white mb-1">Research Projects</h1>
          <p className="text-white/80 text-sm">Manage. Monitor. Support. Advance Research.</p>
        </div>
      </div>

      {/* Action Toolbar */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/research/new")}
          className="flex items-center gap-2 bg-maroon-700 text-white px-4 py-2.5 rounded-control text-sm font-semibold hover:bg-maroon-600 transition-colors"
        >
          <Plus size={16} /> New Submission
        </button>
        {!user?.roles?.includes("RESEARCHER") && (
          <>
            <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2.5 rounded-control text-sm font-medium hover:bg-gray-50 transition-colors">
              <Upload size={16} /> Import
            </button>
            <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2.5 rounded-control text-sm font-medium hover:bg-gray-50 transition-colors">
              <Download size={16} /> Export
            </button>
          </>
        )}
        <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2.5 rounded-control text-sm font-medium hover:bg-gray-50 transition-colors">
          <Filter size={16} /> Filter
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total Projects", value: loading ? "—" : String(stats?.total ?? 0), color: "text-maroon-700", bg: "bg-maroon-500/10" },
          { label: "Ongoing", value: loading ? "—" : String(pipelineCounts[0].count), color: "text-green-600", bg: "bg-green-500/10" },
          { label: "For Revision", value: loading ? "—" : String(pipelineCounts[1].count), color: "text-yellow-600", bg: "bg-yellow-500/10" },
          { label: "Completed", value: loading ? "—" : String(pipelineCounts[3].count), color: "text-green-700", bg: "bg-green-500/10" },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-card border border-gray-200 p-4 shadow-card">
            <div className="text-2xl font-bold text-gray-800">{kpi.value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search projects, researchers, or codes..."
            className="w-full pl-4 pr-4 py-2.5 rounded-control border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          />
        </div>
      </div>

      {/* Main Content: Table + Sidebar */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Table */}
        <div className="xl:col-span-3 bg-white rounded-card border border-gray-200 shadow-card">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-heading text-base font-bold">Research Projects ({total})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
                  <th className="px-5 py-3 font-semibold">#</th>
                  <th className="px-5 py-3 font-semibold">Code</th>
                  <th className="px-5 py-3 font-semibold">Title</th>
                  <th className="px-5 py-3 font-semibold">Researcher(s)</th>
                  <th className="px-5 py-3 font-semibold">Type</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td colSpan={7} className="px-5 py-4">
                        <div className="animate-pulse flex items-center gap-3">
                          <div className="h-3 bg-gray-200 rounded w-full" />
                        </div>
                      </td>
                    </tr>
                  ))
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-8 text-center text-gray-400 text-sm">
                      No research projects found
                    </td>
                  </tr>
                ) : (
                  items.map((p, i) => (
                    <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer" onClick={() => window.location.href = `/research/${p.id}`}>
                      <td className="px-5 py-3 text-gray-500">{(page - 1) * PAGE_SIZE + i + 1}</td>
                      <td className="px-5 py-3 font-mono text-xs text-gray-600">{p.tracking_number}</td>
                      <td className="px-5 py-3 font-medium text-gray-800 max-w-[200px] truncate">{p.title}</td>
                      <td className="px-5 py-3 text-gray-600">{p.authors?.find(a => a.is_lead)?.name || p.lead_proponent_name || "—"}</td>
                      <td className="px-5 py-3 text-gray-600">{p.nature_of_research || "—"}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[p.status] || "bg-gray-100 text-gray-600"}`}>
                          <span className="w-1.5 h-1.5 rounded-full bg-current" />
                          {p.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-gray-500 text-xs">
                        {p.created_at ? new Date(p.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Showing {(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, total)} of {total}</span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-2 py-1 rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
              >
                &lt;
              </button>
              <span className="px-2.5 py-1 rounded bg-maroon-700 text-white">{page}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * PAGE_SIZE >= total}
                className="px-2 py-1 rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
              >
                &gt;
              </button>
            </div>
          </div>
        </div>

        {/* Right Sidebar — Pipeline */}
        <div className="space-y-5">
          <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading text-sm font-bold">Project Pipeline</h3>
            </div>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-20 h-20 rounded-full border-[8px] border-status-success relative shrink-0">
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-bold">{loading ? "—" : pipelineTotal}</span>
                </div>
              </div>
              <span className="text-xs text-gray-500">Projects</span>
            </div>
            <div className="space-y-1.5 text-xs">
              {pipelineCounts.map((p) => (
                <div key={p.label} className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${p.color}`} />
                  <span className="flex-1 text-gray-600">{p.label}</span>
                  <span className="font-medium text-gray-800">{p.count}</span>
                  <span className="text-gray-400 w-8 text-right">
                    {pipelineTotal > 0 ? Math.round((p.count / pipelineTotal) * 100) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
