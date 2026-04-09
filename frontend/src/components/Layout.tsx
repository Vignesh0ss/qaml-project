import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Shield,
  Microscope,
  Settings,
  Menu,
  X,
  LogOut,
  User as UserIcon,
  PlugZap,
} from "lucide-react";
import { useState } from "react";
import { cn } from "../lib/utils";
import { useAuth } from "../contexts/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/query", label: "New Query", icon: Search },
  { to: "/custom-query", label: "Custom Query", icon: PlugZap },
  { to: "/disease-drug-classification", label: "Disease and Drug Classification", icon: Microscope },
  { to: "/audit-history", label: "Audit History", icon: Shield },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-gradient-to-b from-primary-900 to-primary-800 text-white min-h-screen fixed left-0 top-0 z-40">
        <div className="p-6 border-b border-white/10">
          <Link to="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center overflow-hidden">
              <img src="/logo.png" alt="QAML Logo" className="w-full h-full object-contain" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">QAML</h1>
              <p className="text-xs text-white/60 font-medium">Drug Repurposing</p>
            </div>
          </Link>
        </div>

        {/* User Profile */}
        <div className="px-6 py-4 border-b border-white/10 bg-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-accent-500/20 border border-accent-500/30 flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-accent-400" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-bold truncate text-white">{user?.username || "Researcher"}</p>
              <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Authorized</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
                loc.pathname === to || (to !== "/" && loc.pathname.startsWith(to))
                  ? "bg-white/15 text-white font-medium"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/10 space-y-1">
          <Link
            to="/settings"
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 text-sm",
              loc.pathname === "/settings"
                ? "bg-white/15 text-white font-medium"
                : "text-white/60 hover:text-white hover:bg-white/10"
            )}
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-white/60 hover:text-red-300 hover:bg-red-500/10 transition-all duration-200 rounded-lg text-sm"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-primary-900 text-white px-4 py-3 flex items-center justify-between border-b border-white/10">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center overflow-hidden">
            <img src="/logo.png" alt="QAML Logo" className="w-full h-full object-contain" />
          </div>
          <span className="font-bold text-lg">QAML</span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 hover:bg-white/10 rounded-lg"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-primary-900 pt-16">
          <nav className="p-4 space-y-2">
            {navItems.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-4 py-4 rounded-lg transition-all",
                  loc.pathname === to
                    ? "bg-white/15 text-white font-medium"
                    : "text-white/70 hover:bg-white/10"
                )}
              >
                <Icon className="w-5 h-5" />
                {label}
              </Link>
            ))}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 lg:ml-64 pt-16 lg:pt-0">
        <div className="max-w-7xl mx-auto p-4 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
