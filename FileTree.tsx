"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Folder, FileCode2, FileJson, FileText, Database } from "lucide-react";

export type FileNodeType = {
  name: string;
  type: "file" | "folder";
  icon?: "code" | "json" | "text" | "database";
  children?: FileNodeType[];
};

const MOCK_FILE_SYSTEM: FileNodeType[] = [
  {
    name: "src",
    type: "folder",
    children: [
      {
        name: "agents",
        type: "folder",
        children: [
          { name: "CodeAnalyzer.ts", type: "file", icon: "code" },
          { name: "DependencyGraph.ts", type: "file", icon: "code" },
        ],
      },
      {
        name: "config",
        type: "folder",
        children: [{ name: "settings.json", type: "file", icon: "json" }],
      },
      { name: "main.ts", type: "file", icon: "code" },
    ],
  },
  { name: "schema.prisma", type: "file", icon: "database" },
  { name: "package.json", type: "file", icon: "json" },
  { name: "README.md", type: "file", icon: "text" },
];

const getFileIcon = (iconType?: string) => {
  switch (iconType) {
    case "json":
      return <FileJson size={14} className="text-[#10B981]" />;
    case "database":
      return <Database size={14} className="text-[#F59E0B]" />;
    case "text":
      return <FileText size={14} className="text-slate-400" />;
    case "code":
    default:
      return <FileCode2 size={14} className="text-[#2563EB]" />;
  }
};

function FileNode({ node, depth = 0 }: { node: FileNodeType; depth?: number }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="select-none font-mono tracking-tight">
      <div
        className="flex items-center gap-1.5 px-2 py-1.5 hover:bg-white/5 rounded-md cursor-pointer text-sm text-slate-400 hover:text-slate-100 transition-colors"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => setIsOpen(!isOpen)}
      >
        {node.type === "folder" ? (
          <>
            <ChevronRight size={14} className={`transition-transform duration-200 ${isOpen ? "rotate-90" : ""}`} />
            <Folder size={14} className="text-[#7C3AED]" />
          </>
        ) : (
          <span className="ml-5">{getFileIcon(node.icon)}</span>
        )}
        <span className="truncate">{node.name}</span>
      </div>

      {node.type === "folder" && (
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              {node.children?.map((child, idx) => (
                <FileNode key={idx} node={child} depth={depth + 1} />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}

export function FileTree() {
  return (
    <div className="w-full h-full pb-4">
      {MOCK_FILE_SYSTEM.map((node, idx) => (
        <FileNode key={idx} node={node} />
      ))}
    </div>
  );
}