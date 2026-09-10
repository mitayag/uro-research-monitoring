import { useEffect, useState } from "react";
import { FileText, BarChart3, Users, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface DeanStats {
  total: number;
  pending_endorsement: number;
  active: number;
  needs_attention: number;
  under_evaluation: number;
  under_implementation: number;
  completed: number;
  by_status: Record<string, number>;
  school_name: string | null;
}

const REPORTS = [
  { label: "Research Project Summary", desc: "Overview of all research projects in your unit", icon: FileText },
  { label: "Pending Endorsement Report", desc: "Submissions awaiting your endorsement", icon: Clock },
  { label: "Active Research Report", desc: "Currently active research projects", icon: BarChart3 },
  { label: "Completed Research Report", desc: "Successfully completed research", icon: CheckCircle },
  { label: "Researcher Productivity", desc: "Research output by researcher", icon: Users },
  { label: "Needs Attention Report", desc: "Projects requiring attention", icon: AlertCircle },
];

export default function DeanReports() {
  const { token } = useAuth();
  const [stats, setStats] = useState<DeanStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    apiRequest<DeanStats>("/dean/stats", { token })
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-gray-800">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Generate school/college-level research reports</p>
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Research Summary{stats?.school_name ? ` — ${stats.school_name}` : ""}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Projects", value: loading ? "—" : String(stats?.total ?? 0), icon: FileText, color: "text-gray-600" },
            { label: "Pending Endorsement", value: loading ? "—" : String(stats?.pending_endorsement ?? 0), icon: Clock, color: "text-amber-600" },
            { label: "Active Research", value: loading ? "—" : String(stats?.active ?? 0), icon: BarChart3, color: "text-blue-600" },
            { label: "Completed", value: loading ? "—" : String(stats?.completed ?? 0), icon: CheckCircle, color: "text-green-600" },
          ].map((kpi) => (
            <div key={kpi.label} className="p-3 rounded-card border border-gray-100">
              <kpi.icon size={16} className={kpi.color} />
              <div className="text-xl font-bold text-gray-800 mt-1">{kpi.value}</div>
              <div className="text-[10px] text-gray-500">{kpi.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Available Reports */}
      <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
        <h3 className="font-heading text-sm font-bold mb-4">Available Reports</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {REPORTS.map((report) => (
            <div key={report.label} className="flex items-center gap-4 p-4 border border-gray-100 rounded-card hover:bg-gray-50 transition-colors cursor-pointer">
              <div className="w-10 h-10 rounded-lg bg-maroon-50 flex items-center justify-center shrink-0">
                <report.icon size={18} className="text-maroon-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">{report.label}</p>
                <p className="text-xs text-gray-500">{report.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Status Breakdown */}
      {stats && (
        <div className="bg-white rounded-card border border-gray-200 p-5 shadow-card">
          <h3 className="font-heading text-sm font-bold mb-4">Status Breakdown</h3>
          <div className="space-y-2">
            {Object.entries(stats.by_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-600">{status.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase())}</span>
                <span className="text-sm font-semibold text-gray-800">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
