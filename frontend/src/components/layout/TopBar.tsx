import { Bell, ChevronDown, LogOut, Search } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";

export default function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const initials = user
    ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    : "??";

  const roleDisplay = user?.roles?.[0]?.replace(/_/g, " ") || "User";

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 shrink-0">
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search submissions, researchers, projects, or documents..."
            className="w-full pl-10 pr-16 py-2.5 rounded-xl border border-gray-200 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-maroon-500/30 focus:border-maroon-500 transition-colors"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] text-gray-400 bg-white border border-gray-200 rounded px-1.5 py-0.5">
            Ctrl + K
          </kbd>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4 ml-6">
        {/* Notification bell */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors">
          <Bell size={20} />
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-maroon-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            3
          </span>
        </button>

        {/* User info */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 rounded-lg px-3 py-1.5 transition-colors"
          >
            <div className="w-9 h-9 rounded-full bg-maroon-700 text-white flex items-center justify-center text-sm font-bold">
              {initials}
            </div>
            <div className="hidden md:block text-right">
              <div className="text-sm font-semibold text-gray-800">
                {user?.full_name || "User"}
              </div>
              <div className="text-xs text-gray-500">{roleDisplay}</div>
            </div>
            <ChevronDown size={16} className="text-gray-400" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-200 rounded-card shadow-modal py-1 z-50">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <LogOut size={16} />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
