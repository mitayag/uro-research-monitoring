import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Users, ArrowRight } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface ResearcherItem {
  id: string;
  name: string;
  email: string;
  total_research: number;
  active_research: number;
  completed_research: number;
  latest_project: { id: string; title: string; status: string } | null;
}

export default function DeanResearchers() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [researchers, setResearchers] = useState<ResearcherItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    apiRequest<ResearcherItem[]>(`/dean/researchers?${params.toString()}`, { token })
      .then(setResearchers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, search]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Researchers</h1>
        <p className="text-sm text-gray-500 mt-1">Researchers in your academic unit</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search researchers..."
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
        ) : researchers.length === 0 ? (
          <div className="p-8 text-center">
            <Users size={32} className="mx-auto text-gray-300 mb-3" />
            <p className="text-sm text-gray-400">No researchers found for your academic unit.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs font-semibold text-gray-500 uppercase">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Total Research</th>
                <th className="px-4 py-3">Active</th>
                <th className="px-4 py-3">Completed</th>
                <th className="px-4 py-3">Latest Project</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {researchers.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-gray-800">{r.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{r.email}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 text-center">{r.total_research}</td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">{r.active_research}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold">{r.completed_research}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-[200px] truncate">
                    {r.latest_project ? r.latest_project.title : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => navigate(`/dean/research?search=${encodeURIComponent(r.name)}`)}
                      className="flex items-center gap-1 text-xs font-medium text-maroon-700 hover:text-maroon-600"
                    >
                      View Research <ArrowRight size={12} />
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
