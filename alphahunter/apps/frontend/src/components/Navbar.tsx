import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  History,
  Star,
  Bell,
  Settings,
  Crosshair,
} from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/history", label: "History", icon: History },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Navbar() {
  return (
    <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
      <NavLink to="/" className="flex items-center gap-2">
        <Crosshair className="text-emerald-400" size={24} />
        <span className="text-xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          AlphaHunter AI
        </span>
      </NavLink>

      <div className="flex items-center gap-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-700/50"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
