import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, CheckCircle, ArrowRight } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface CompletedItem {
  id: string;
  tracking_number: string;
  title: string;
  lead_proponent_name: string | null;
  status: string;
  completed_at: string | null;
  updated_at: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  COMPLETED: "Completed",
  READY_FOR_PRESENTATION: "Ready for Presentation",
  READY_FOR_PUBLICATION: "Ready for Publication",
  ARCHIVED: "Archived",
};

export default function DeanCompleted() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [items, setItems] = useState<CompletedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", "20");
    if (search) params.set("search", search);
    apiRequest<{ items: CompletedItem[]; total: number }>(`/dean/completed?${params.toString()}`, { token })
      .then((data) => { setItems(data.items); setTotal(data.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, search, page]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Completed Research</h1>
        <p className="text-sm text-gray-500 mt-1">Research projects completed in your academic unit</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search completed research..."
          className="w-full pl-9 pr-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
        />
      </div>

      {/* List */}
      <div className="bg-white rounded-card border border-gray-200 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center">
            <CheckCircle size={32} className="mx-auto text-gray-300 mb-3" />
            <p className="text-sm text-gray-400">No completed research projects yet.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs font-semibold text-gray-500 uppercase">
                <th className="px-4 py-3">Research ID</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Researcher</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Completion Date</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.tracking_number}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-800 max-w-xs truncate">{item.title}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{item.lead_proponent_name}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700">
                      {STATUS_LABELS[item.status] || item.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {item.completed_at ? new Date(item.completed_at).toLocaleDateString() : "—"}
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
          <p className="text-sm text-gray-500">Showing {items.length} of {total}</p>
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
              disabled={items.length < 20}
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
