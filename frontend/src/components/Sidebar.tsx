import {
  AlertTriangle,
  ClipboardCheck,
  Gauge,
  LayoutDashboard,
  Map,
  ShieldAlert,
  Users,
  Wrench,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { BarChart3 } from "lucide-react";

const menuItems = [
  {
    name: "Command Center",
    path: "/command-center",
    icon: LayoutDashboard,
  },
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: Gauge,
  },
  {
    name: "Plant Safety Map",
    path: "/plant-map",
    icon: Map,
  },
  {
    name: "Workers & PPE",
    path: "/workers",
    icon: Users,
  },
  {
    name: "Incidents & Alerts",
    path: "/incidents",
    icon: AlertTriangle,
  },
  {
    name: "Emergency Response",
    path: "/emergency",
    icon: ShieldAlert,
  },
  {
    name: "Permits",
    path: "/permits",
    icon: ClipboardCheck,
  },
  {
    name: "Maintenance",
    path: "/maintenance",
    icon: Wrench,
  },
  {
    name: "Risk Intelligence",
    path: "/risk",
    icon: Gauge,
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  
];


function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo-section">
        <div className="logo-icon">S</div>

        <div>
          <h1>SurakshaAI</h1>
          <p>Industrial Safety</p>
        </div>
      </div>

      <nav className="sidebar-menu">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                isActive ? "menu-item active" : "menu-item"
              }
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;