"use client";

import { motion } from "framer-motion";
import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";
import { useAgentStore, AgentStep } from "@/store/useAgentStore";

const STEPS: AgentStep[] = ["Analyze", "Plan", "Implement", "Test", "Deploy"];

export function AgentTimeline() {
  const { currentStep, isExecuting } = useAgentStore();

  const getCurrentStepIndex = () => STEPS.indexOf(currentStep as any);
  const currentIndex = getCurrentStepIndex();

  return (
    <div className="flex flex-col gap-6 w-full max-w-xl">
      {STEPS.map((step, index) => {
        const isActive = index === currentIndex && isExecuting;
        const isCompleted = index < currentIndex || currentStep === "Completed";
        
        return (
          <div key={step} className="relative flex items-start gap-4 group">
            {/* Connecting Line */}
            {index !== STEPS.length - 1 && (
              <div 
                className={`absolute left-4 top-10 w-0.5 h-12 -ml-[1px] rounded-full transition-colors duration-500 ${
                  isCompleted ? "bg-[#10B981]" : "bg-white/10"
                }`}
              />
            )}

            {/* Glowing Icon Indicator */}
            <div className="relative z-10 flex-shrink-0 mt-1">
              {isActive ? (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0.5 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ repeat: Infinity, duration: 1, ease: "easeInOut", repeatType: "reverse" }}
                  className="w-8 h-8 rounded-full bg-[#7C3AED]/20 border border-[#7C3AED] flex items-center justify-center shadow-[0_0_15px_rgba(124,58,237,0.5)] text-[#7C3AED]"
                >
                  <Loader2 size={16} className="animate-spin" />
                </motion.div>
              ) : isCompleted ? (
                <div className="w-8 h-8 rounded-full bg-[#10B981]/20 border border-[#10B981] flex items-center justify-center shadow-[0_0_10px_rgba(16,185,129,0.3)] text-[#10B981]">
                  <CheckCircle2 size={16} />
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full bg-[#101425] border border-white/10 flex items-center justify-center text-slate-500 group-hover:border-white/20 transition-colors">
                  <CircleDashed size={16} />
                </div>
              )}
            </div>

            {/* Step Content */}
            <div className="flex flex-col">
              <h4 className={`text-sm font-semibold transition-colors duration-300 ${isActive ? "text-[#7C3AED] drop-shadow-[0_0_5px_rgba(124,58,237,0.5)]" : isCompleted ? "text-white" : "text-slate-500"}`}>{step}</h4>
              <p className="text-xs text-slate-500 mt-1">{isActive ? `Running ${step.toLowerCase()} sequence...` : isCompleted ? `${step} completed successfully.` : `Awaiting ${step.toLowerCase()} phase.`}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}