import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Users,
  UserCheck,
  Shield,
  Search,
  BarChart3,
  BookOpen,
  Settings,
  Send,
  FolderOpen,
  MessageSquare,
  FileUp,
  Bell,
  AlertCircle,
  CheckCircle,
  Building2,
} from "lucide-react";
import logoImg from "../../assets/logo.png";
import { useAuth } from "../../contexts/AuthContext";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
}

const ADMIN_NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/schools", label: "Schools / Colleges", icon: Building2 },
  { to: "/research", label: "Research", icon: FileText },
  { to: "/submissions", label: "Submissions", icon: Send },
  { to: "/researchers", label: "Researchers", icon: Users },
  { to: "/evaluators", label: "Evaluators", icon: UserCheck },
  { to: "/irb", label: "IRB", icon: Shield },
  { to: "/turnitin", label: "Turnitin", icon: Search },
  { to: "/monitoring", label: "Monitoring", icon: BarChart3 },
  { to: "/reports", label: "Reports", icon: BookOpen },
  { to: "/resources", label: "Resources", icon: BookOpen },
  { to: "/settings", label: "Settings", icon: Settings },
];

const RESEARCHER_NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/research", label: "My Research", icon: FileText },
  { to: "/research/new", label: "New Submission", icon: Send },
  { to: "/submissions", label: "My Submissions", icon: FolderOpen },
  { to: "/actions", label: "Required Actions", icon: AlertCircle },
  { to: "/evaluations", label: "Evaluations & Feedback", icon: MessageSquare },
  { to: "/irb", label: "IRB / Ethics", icon: Shield },
  { to: "/turnitin", label: "Turnitin Results", icon: Search },
  { to: "/monitoring", label: "Implementation", icon: BarChart3 },
  { to: "/documents", label: "Documents", icon: FileUp },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/resources", label: "Resources", icon: BookOpen },
];

const DEAN_NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dean/endorsements", label: "Pending Endorsements", icon: Send },
  { to: "/dean/research", label: "Research Projects", icon: FileText },
  { to: "/dean/departments", label: "Departments", icon: Building2 },
  { to: "/dean/staff", label: "Academic Staff", icon: Users },
  { to: "/dean/monitoring", label: "Progress Monitoring", icon: BarChart3 },
  { to: "/dean/completed", label: "Completed Research", icon: CheckCircle },
  { to: "/dean/reports", label: "Reports", icon: BookOpen },
  { to: "/resources", label: "Resources", icon: BookOpen },
];

export default function Sidebar() {
  const location = useLocation();
  const { user } = useAuth();

  const isResearcher = user?.roles?.includes("RESEARCHER") && !user?.roles?.includes("ADMIN") && !user?.roles?.includes("URO_DIRECTOR") && !user?.roles?.includes("URO_STAFF");
  const isDean = user?.roles?.includes("DEAN") && !user?.roles?.includes("ADMIN") && !user?.roles?.includes("URO_DIRECTOR") && !user?.roles?.includes("URO_STAFF");

  const navItems = isDean ? DEAN_NAV_ITEMS : isResearcher ? RESEARCHER_NAV_ITEMS : ADMIN_NAV_ITEMS;

  return (
    <aside className="w-60 h-screen flex flex-col text-white shrink-0"
      style={{
        background: "linear-gradient(180deg, #6E101C 0%, #5A0E16 55%, #3E0B10 100%)",
      }}
    >
      {/* Logo */}
      <div className="flex flex-col items-center py-6 px-4">
        <img
          src={logoImg}
          alt="Holy Angel University"
          className="w-24 h-24 object-contain mb-3"
        />
        <div className="text-center">
          <div className="text-xl font-bold tracking-wide">URO</div>
          <div className="text-[11px] opacity-80 leading-tight">Research Monitoring System</div>
          <div className="text-[10px] opacity-60">Holy Angel University</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            item.to === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-medium transition-colors ${
                isActive
                  ? "bg-white/20 text-white"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              }`}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Motto */}
      <div className="px-4 py-5 text-center">
        <div className="text-[11px] tracking-[0.2em] opacity-50 font-semibold uppercase">
          Virtus
        </div>
        <div className="text-[11px] tracking-[0.2em] opacity-50 font-semibold uppercase">
          Scientia
        </div>
        <div className="text-[11px] tracking-[0.2em] opacity-50 font-semibold uppercase">
          Caritas
        </div>
      </div>
    </aside>
  );
}
