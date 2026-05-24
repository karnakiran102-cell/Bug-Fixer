"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  MessageSquareCode, 
  FolderGit2, 
  Cpu, 
  BarChart3, 
  TerminalSquare, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  Rocket
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const MENU_ITEMS = [
  { name: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { name: "AI Chat", icon: MessageSquareCode, href: "/dashboard/chat" },
  { name: "Projects", icon: FolderGit2, href: "/dashboard/projects" },
  { name: "Agents", icon: Cpu, href: "/dashboard/agents" },
  { name: "Analytics", icon: BarChart3, href: "/dashboard/analytics" },
  { name: "Logs", icon: TerminalSquare, href: "/dashboard/logs" },
  { name: "Deployments", icon: Rocket, href: "/dashboard/deployments" },
  { name: "Settings", icon: Settings, href: "/dashboard/settings" },
];

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <motion.aside
      initial={{ width: 260 }}
      animate={{ width: isCollapsed ? 80 : 260 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="relative flex flex-col h-full bg-[#0A0D1A] border-r border-white/5 shadow-2xl z-20"
    >
      <div className="flex items-center justify-between p-6">
        {!isCollapsed && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            transition={{ delay: 0.2 }}
            className="flex items-center gap-3 font-bold text-lg tracking-wide"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#7C3AED] to-[#2563EB] flex items-center justify-center shadow-[0_0_15px_rgba(124,58,237,0.5)]">
              <Cpu size={18} className="text-white" />
            </div>
            Nexus AI
          </motion.div>
        )}
        {isCollapsed && (
           <div className="w-8 h-8 mx-auto rounded-lg bg-gradient-to-br from-[#7C3AED] to-[#2563EB] flex items-center justify-center shadow-[0_0_15px_rgba(124,58,237,0.5)]">
             <Cpu size={18} className="text-white" />
           </div>
        )}
      </div>

      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-8 bg-[#0A0D1A] border border-white/10 rounded-full p-1 text-slate-400 hover:text-white transition-colors z-50"
      >
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto hide-scrollbar">
        {MENU_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          
          return (
            <Link key={item.name} href={item.href}>
              <div className="relative group flex items-center px-3 py-3 rounded-xl cursor-pointer text-slate-400 hover:text-white transition-colors">
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 bg-white/5 rounded-xl border border-white/10"
                    initial={false}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-indicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-[#7C3AED] rounded-r-full shadow-[0_0_10px_#7C3AED]"
                    initial={false}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <item.icon
                  size={20}
                  className={`relative z-10 transition-colors ${isActive ? "text-[#7C3AED]" : "group-hover:text-white"}`}
                />
                {!isCollapsed && (
                  <span className={`relative z-10 ml-3 font-medium ${isActive ? "text-white" : ""}`}>
                    {item.name}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/5">
        <div className={`flex items-center ${isCollapsed ? "justify-center" : "gap-3"} bg-white/5 p-3 rounded-xl hover:bg-white/10 transition-colors cursor-pointer border border-white/5`}>
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex-shrink-0 border border-white/20" />
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-semibold truncate text-white">Admin User</span>
              <span className="text-xs text-slate-400 truncate">System Operator</span>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}