import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Clock } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

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

function getDaysWaiting(submittedAt: string | null): number {
  if (!submittedAt) return 0;
  const submitted = new Date(submittedAt);
  const now = new Date();
  return Math.floor((now.getTime() - submitted.getTime()) / (1000 * 60 * 60 * 24));
}

export default function DeanEndorsements() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [endorsements, setEndorsements] = useState<EndorsementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("oldest");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    params.set("sort", sort);
    apiRequest<EndorsementItem[]>(`/dean/endorsements?${params.toString()}`, { token })
      .then(setEndorsements)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, search, sort]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Pending Endorsements</h1>
        <p className="text-sm text-gray-500 mt-1">Research submissions awaiting your endorsement</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title, researcher, or ID..."
            className="w-full pl-9 pr-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          />
        </div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="px-3 py-2.5 rounded-control border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
        >
          <option value="oldest">Oldest First</option>
          <option value="newest">Newest First</option>
        </select>
      </div>

      {/* List */}
      <div className="bg-white rounded-card border border-gray-200 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />
            ))}
          </div>
        ) : endorsements.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-gray-400">No research submissions currently require your endorsement.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs font-semibold text-gray-500 uppercase">
                <th className="px-4 py-3">Research ID</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Researcher</th>
                <th className="px-4 py-3">Date Submitted</th>
                <th className="px-4 py-3">Days Waiting</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {endorsements.map((item) => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.tracking_number}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-800 max-w-xs truncate">{item.title}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{item.lead_proponent_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {item.submitted_at ? new Date(item.submitted_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                      getDaysWaiting(item.submitted_at) > 7 ? "text-red-600" : "text-gray-500"
                    }`}>
                      <Clock size={12} />
                      {getDaysWaiting(item.submitted_at)}d
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => navigate(`/dean/endorsements/${item.id}`)}
                      className="px-3 py-1.5 bg-maroon-700 text-white text-xs font-semibold rounded-control hover:bg-maroon-600 transition-colors"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
