import { create } from "zustand";

export type AgentStep = "Analyze" | "Plan" | "Implement" | "Test" | "Deploy" | "Completed";

interface AgentState {
  currentStep: AgentStep;
  isExecuting: boolean;
  setStep: (step: AgentStep) => void;
  setExecuting: (isExecuting: boolean) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  currentStep: "Analyze",
  isExecuting: false,
  setStep: (step) => set({ currentStep: step }),
  setExecuting: (isExecuting) => set({ isExecuting }),
}));