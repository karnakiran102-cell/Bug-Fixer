"use client";

import { useState } from "react";
import { Message } from "@/store/useChatStore";
import { User, Cpu, Sparkles, Copy, Check, FileCode2 } from "lucide-react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { useEditorStore } from "@/store/useEditorStore";

const CodeBlock = ({ node, inline, className, children, ...props }: any) => {
  const match = /language-(\w+)/.exec(className || "");
  const codeString = String(children).replace(/\n$/, "");
  const [isCopied, setIsCopied] = useState(false);
  const [isApplied, setIsApplied] = useState(false);
  const setEditorCode = useEditorStore((state: any) => state.setCode);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleApply = () => {
    setEditorCode(codeString);
    setIsApplied(true);
    setTimeout(() => setIsApplied(false), 2000);
  };

  return !inline && match ? (
    <div className="rounded-xl overflow-hidden my-3 border border-white/10 bg-[#060816]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#0A0D1A] border-b border-white/5">
        <span className="text-xs font-mono text-slate-400">{match[1]}</span>
        <div className="flex items-center gap-3">
          <button onClick={handleCopy} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
            {isCopied ? <Check size={14} className="text-[#10B981]" /> : <Copy size={14} />}
            {isCopied ? "Copied" : "Copy"}
          </button>
          <div className="w-px h-3 bg-white/10" />
          <button onClick={handleApply} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-[#7C3AED] transition-colors">
            {isApplied ? <Check size={14} className="text-[#10B981]" /> : <FileCode2 size={14} />}
            {isApplied ? "Applied" : "Apply to Editor"}
          </button>
        </div>
      </div>
      <SyntaxHighlighter {...props} children={codeString} style={vscDarkPlus} language={match[1]} PreTag="div" customStyle={{ margin: 0, background: 'transparent', padding: '1rem', fontSize: '12px' }} />
    </div>
  ) : (
    <code {...props} className="bg-white/10 text-[#7C3AED] px-1.5 py-0.5 rounded-md font-mono text-[11px]">{children}</code>
  );
};

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-4 w-full ${isUser ? "flex-row-reverse" : ""}`}
    >
      <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${isUser ? "bg-gradient-to-br from-indigo-500 to-purple-500" : "bg-gradient-to-br from-[#7C3AED] to-[#2563EB] shadow-[0_0_15px_rgba(124,58,237,0.3)]"}`}>
        {isUser ? <User size={16} className="text-white" /> : <Cpu size={16} className="text-white" />}
      </div>

      <div className={`flex flex-col min-w-[200px] max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        <div className="flex items-center gap-2 mb-1 px-1">
          <span className="text-xs font-medium text-slate-400">{isUser ? "Admin User" : "Nexus AI"}</span>
          {message.isStreaming && <Sparkles size={12} className="text-[#7C3AED] animate-pulse" />}
        </div>
        
        <div className={`p-4 rounded-2xl text-sm leading-relaxed ${isUser ? "bg-[#2563EB] text-white rounded-tr-sm" : "bg-[#101425] border border-white/5 text-slate-200 rounded-tl-sm shadow-xl"}`}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <ReactMarkdown
              className="prose prose-invert max-w-none prose-pre:bg-transparent prose-pre:p-0 prose-pre:m-0"
              components={{ code: CodeBlock }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </motion.div>
  );
}