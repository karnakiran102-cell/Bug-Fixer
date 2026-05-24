"use client";

import { Search, Bell, Sparkles, Command } from "lucide-react";

export function TopNavbar() {
  return (
    <header className="h-20 w-full bg-[#060816]/80 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative group w-full max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={18} className="text-slate-500 group-hover:text-[#7C3AED] transition-colors" />
          </div>
          <input
            type="text"
            placeholder="Search commands, projects, files..."
            className="w-full bg-[#101425] border border-white/10 rounded-xl py-2.5 pl-10 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#7C3AED]/50 focus:border-[#7C3AED] transition-all"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <div className="flex items-center gap-1 bg-white/5 px-1.5 py-0.5 rounded text-[10px] text-slate-400 font-mono">
              <Command size={10} /> K
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] text-xs font-medium">
          <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse shadow-[0_0_8px_#10B981]" />
          AI Agent Active
        </div>

        <div className="flex items-center gap-4">
          <button className="relative p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-colors">
            <Sparkles size={20} />
          </button>
          
          <button className="relative p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-colors">
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-[#2563EB] border-2 border-[#060816] rounded-full" />
          </button>
        </div>
      </div>
    </header>
  );
}