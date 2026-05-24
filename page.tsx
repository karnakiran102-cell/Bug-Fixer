"use client";

import dynamic from "next/dynamic";
import { KeyboardEvent, useState, useRef, useEffect } from "react";
import { Send, Bot, Sparkles, RotateCcw } from "lucide-react";
import { useChatStore, type Message } from "@/store/useChatStore";
import { useEditorStore } from "@/store/useEditorStore";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { FileTree } from "@/components/dashboard/FileTree";
import { generateAssistantReply } from "@/lib/localChatAssistant";

// Dynamically import Monaco Editor and xterm.js to avoid hydration errors
const CodeEditor = dynamic(() => import("@/components/dashboard/CodeEditor"), { 
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-sm">Loading Editor Engine...</div>
});

const Terminal = dynamic(() => import("@/components/dashboard/Terminal"), { 
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-sm">Initializing Subsystem Console...</div>
});

const QUICK_PROMPTS = [
  "Find bugs in the editor code",
  "Explain the current code",
  "Write a test plan",
];

const STREAM_CHUNK_SIZE = 14;
const STREAM_INTERVAL_MS = 16;

export default function ChatWorkspacePage() {
  const { messages, addMessage, appendStream, finishStream, clearMessages, isTyping, setTyping } = useChatStore();
  const editorCode = useEditorStore((state) => state.code);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamDelayRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-scroll chat to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    return () => {
      if (streamDelayRef.current) {
        clearTimeout(streamDelayRef.current);
      }
      if (streamIntervalRef.current) {
        clearInterval(streamIntervalRef.current);
      }
    };
  }, []);

  const streamAssistantReply = (reply: string) => {
    const assistantId =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${Date.now()}-assistant`;

    streamDelayRef.current = setTimeout(() => {
      addMessage({ id: assistantId, role: "assistant", content: "", isStreaming: true });

      let cursor = 0;
      streamIntervalRef.current = setInterval(() => {
        const nextChunk = reply.slice(cursor, cursor + STREAM_CHUNK_SIZE);
        cursor += nextChunk.length;

        if (nextChunk) {
          appendStream(assistantId, nextChunk);
        }

        if (cursor >= reply.length) {
          if (streamIntervalRef.current) {
            clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
          }
          finishStream(assistantId);
          setTyping(false);
        }
      }, STREAM_INTERVAL_MS);
    }, 350);
  };

  const handleSend = (messageText = input) => {
    const prompt = messageText.trim();

    if (!prompt || isTyping) return;
    
    const reply = generateAssistantReply({
      prompt,
      history: messages,
      editorCode,
    });

    addMessage({ role: "user", content: prompt });
    setInput("");
    setTyping(true);
    streamAssistantReply(reply);
  };

  const handleInputKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] w-full gap-4 overflow-hidden">
      {/* Left Panel - File Tree */}
      <div className="w-64 flex-shrink-0 bg-[#101425] border border-white/5 rounded-2xl flex flex-col overflow-hidden shadow-lg hidden lg:flex">
        <div className="px-4 py-3 border-b border-white/5 font-medium text-sm text-slate-200">
          Explorer
        </div>
        <div className="flex-1 overflow-y-auto p-2 hide-scrollbar">
          <FileTree />
        </div>
      </div>

      {/* Center Panel - Editor & Terminal */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* Editor Area */}
        <div className="flex-1 bg-[#101425] border border-white/5 rounded-2xl overflow-hidden flex flex-col shadow-lg">
           <div className="flex items-center px-4 py-2 border-b border-white/5 bg-[#0A0D1A]">
             <div className="flex gap-2">
               <div className="px-3 py-1.5 bg-[#060816] rounded-t-lg border-t border-x border-white/10 text-xs text-white flex items-center gap-2 shadow-sm">
                 <span className="text-[#2563EB] font-bold">TS</span> main.ts
               </div>
             </div>
           </div>
           <div className="flex-1 relative">
             <CodeEditor />
           </div>
        </div>

        {/* Terminal Area */}
        <div className="h-64 flex-shrink-0 bg-[#101425] border border-white/5 rounded-2xl overflow-hidden flex flex-col shadow-lg">
          <div className="px-4 py-2 border-b border-white/5 bg-[#0A0D1A] text-xs font-mono text-slate-400">
            Terminal
          </div>
          <div className="flex-1 p-2">
            <Terminal />
          </div>
        </div>
      </div>

      {/* Right Panel - AI Chat */}
      <div className="w-96 flex-shrink-0 bg-[#101425] border border-white/5 rounded-2xl flex flex-col overflow-hidden relative shadow-lg">
        <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
          <Bot size={18} className="text-[#7C3AED]" />
          <span className="font-medium text-sm text-white">Nexus AI</span>
          <button
            type="button"
            onClick={clearMessages}
            disabled={!messages.length || isTyping}
            title="Clear chat"
            className="ml-auto rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            <RotateCcw size={15} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 hide-scrollbar">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4 text-slate-400 opacity-50">
              <Sparkles size={48} className="text-[#7C3AED]" />
              <p className="text-sm">How can I help you build today?</p>
              <div className="flex flex-wrap justify-center gap-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSend(prompt)}
                    className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-[#7C3AED]/60 hover:text-white"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg: Message, idx: number) => (
              <ChatMessage key={msg.id || idx} message={msg} />
            ))
          )}
          {isTyping && (
            <div className="flex items-center gap-2 text-slate-400 text-xs p-2">
              <Sparkles size={12} className="animate-pulse text-[#7C3AED]" /> Nexus AI is typing...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-white/5 bg-[#0A0D1A]">
          <div className="relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Ask Nexus AI..."
              rows={2}
              className="max-h-32 min-h-[52px] w-full resize-none rounded-xl border border-white/10 bg-[#060816] py-3 pl-4 pr-12 text-sm text-white placeholder-slate-500 outline-none transition-all focus:border-[#7C3AED] focus:ring-1 focus:ring-[#7C3AED]"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className="absolute bottom-3 right-2 rounded-lg bg-[#7C3AED] p-1.5 text-white transition-colors hover:bg-[#6D28D9] disabled:opacity-50 disabled:hover:bg-[#7C3AED]"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
