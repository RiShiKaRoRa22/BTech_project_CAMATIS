"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Route, BarChart2, Bell, Settings, Bus, PlayCircle, GitBranch } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/routes", label: "Routes", icon: Route },
  { href: "/rerouting", label: "Rerouting", icon: GitBranch },  // NEW
  { href: "/results", label: "Results", icon: BarChart2 },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 min-h-screen bg-slate-900 text-white flex flex-col">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-700">
        <Bus className="text-blue-400" size={22} />
        <span className="text-lg font-bold tracking-wide text-blue-400">CAMATIS</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname === href || pathname.startsWith(href + "/")
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-6 py-4 border-t border-slate-700 text-xs text-slate-500">
        AI-Powered Transit System
      </div>
    </aside>
  );
}