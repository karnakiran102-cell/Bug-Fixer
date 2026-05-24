import { create } from "zustand";

export type Message = {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
};

interface ChatState {
  messages: Message[];
  isTyping: boolean;
  addMessage: (message: Message) => void;
  setTyping: (isTyping: boolean) => void;
  appendStream: (id: string, chunk: string) => void;
  finishStream: (id: string) => void;
  clearMessages: () => void;
}

function createMessageId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isTyping: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, { ...message, id: message.id || createMessageId() }],
    })),
  setTyping: (isTyping) => set({ isTyping }),
  appendStream: (id, chunk) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + chunk } : msg
      ),
    })),
  finishStream: (id) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, isStreaming: false } : msg
      ),
    })),
  clearMessages: () => set({ messages: [], isTyping: false }),
}));
