"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronRight, Clock } from "lucide-react";
import { WSMessage, ReasoningStep, Document } from "@/types";

// --- ConversationItem ---
export interface ConversationItem {
  id: string;
  timestamp: string;
  question: string;
  reasoning: string;
  answer: string;
}

// --- SiriWaveform ---
type WaveformState = "idle" | "listening" | "thinking" | "speaking";

function SiriWaveform({ state }: { state: WaveformState }) {
  const barCount = 40;
  const getAmplitude = () => {
    switch (state) {
      case "idle": return { min: 2, max: 8 };
      case "listening": return { min: 8, max: 48 };
      case "thinking": return { min: 12, max: 32 };
      case "speaking": return { min: 16, max: 56 };
    }
  };
  const getDuration = () => {
    switch (state) {
      case "idle": return 3;
      case "listening": return 0.6;
      case "thinking": return 2;
      case "speaking": return 0.8;
    }
  };
  const amplitude = getAmplitude();
  const duration = getDuration();

  return (
    <div className="flex items-center justify-center gap-1.5 h-32">
      {[...Array(barCount)].map((_, i) => {
        const phase = (i / barCount) * Math.PI * 2;
        const heightVariation = Math.sin(phase) * 0.5 + 0.5;
        return (
          <motion.div
            key={i}
            className="w-1 rounded-full"
            style={{ background: "rgba(88, 166, 255, 0.8)", boxShadow: "0 0 8px rgba(88, 166, 255, 0.4)" }}
            animate={{
              height: [
                amplitude.min + heightVariation * 4,
                amplitude.min + (amplitude.max - amplitude.min) * heightVariation,
                amplitude.min + heightVariation * 4,
              ],
              opacity: state === "idle" ? [0.3, 0.5, 0.3] : [0.6, 1, 0.6],
            }}
            transition={{
              duration,
              repeat: Infinity,
              delay: (i / barCount) * 0.5,
              ease: "easeInOut",
            }}
          />
        );
      })}
    </div>
  );
}

// --- AgenticReasoning (adapted to use backend reasoning steps) ---
interface AgenticReasoningProps {
  reasoningSteps: ReasoningStep[];
}

function AgenticReasoning({ reasoningSteps }: AgenticReasoningProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (reasoningSteps.length === 0) return;
    
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % reasoningSteps.length);
    }, 3000); // Change step every 3 seconds

    return () => clearInterval(interval);
  }, [reasoningSteps.length]);

  if (reasoningSteps.length === 0) return null;

  const step = reasoningSteps[currentStep];
  const colors = ["#58a6ff", "#56d4dd", "#3fb950", "#d29922", "#8b949e"];
  const color = colors[currentStep % colors.length];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -20 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
      className="max-w-2xl w-full"
    >
      <motion.div
        className="rounded-xl p-8 relative overflow-hidden"
        style={{
          background: "rgba(22, 27, 34, 0.4)",
          backdropFilter: "blur(40px)",
          border: "1px solid rgba(88, 166, 255, 0.12)",
        }}
      >
        <div className="absolute top-0 left-0 right-0 h-px" style={{ background: "linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.3), transparent)" }} />
        <div className="flex items-center gap-3 mb-5">
          <motion.div
            className="w-2 h-2 rounded-full"
            style={{ background: color }}
            animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.p
            key={currentStep}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.3 }}
            className="text-xs"
            style={{ fontFamily: "'Space Mono', monospace", color: color, letterSpacing: "0.5px" }}
          >
            {step.step?.toUpperCase() || "ANALYZING"}
          </motion.p>
        </div>
        <div className="space-y-4">
          <motion.div
            key={`step-${currentStep}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.3 }}
          >
            <p className="text-sm leading-relaxed" style={{ color: "#c9d1d9", fontFamily: "'Crimson Pro', serif" }}>
              {step.content}
            </p>
          </motion.div>
        </div>
        <div className="flex items-center gap-1.5 mt-6">
          {reasoningSteps.map((_, index) => (
            <motion.div
              key={index}
              className="h-1 rounded-full"
              style={{ flex: 1, background: index === currentStep ? color : "rgba(139, 148, 158, 0.2)" }}
              animate={{ opacity: index === currentStep ? 1 : 0.4 }}
              transition={{ duration: 0.3 }}
            />
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

// --- ConversationHistory ---
function ConversationHistory({ conversations }: { conversations: ConversationItem[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (conversations.length === 0) return null;

  return (
    <div className="relative">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all relative overflow-hidden"
        style={{
          background: isOpen ? "rgba(88, 166, 255, 0.15)" : "rgba(13, 17, 23, 0.6)",
          border: isOpen ? "1px solid rgba(88, 166, 255, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(10px)",
          fontFamily: "'Space Mono', monospace",
          color: "#e6edf3",
        }}
        whileHover={{ scale: 1.02, borderColor: "rgba(88, 166, 255, 0.6)" }}
        whileTap={{ scale: 0.98 }}
      >
        <Clock size={16} style={{ color: "#58a6ff" }} />
        <span className="text-sm">History ({conversations.length})</span>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.3 }}>
          <ChevronDown size={16} style={{ color: "#8b949e" }} />
        </motion.div>
      </motion.button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full mt-2 right-0 w-96 max-h-96 overflow-y-auto rounded-xl z-50"
            style={{
              background: "rgba(13, 17, 23, 0.95)",
              border: "1px solid rgba(88, 166, 255, 0.3)",
              backdropFilter: "blur(20px)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
            }}
          >
            <div className="p-2 space-y-1">
              {conversations.map((conversation, index) => (
                <div key={conversation.id}>
                  <motion.button
                    onClick={() => setExpandedId(expandedId === conversation.id ? null : conversation.id)}
                    className="w-full text-left p-3 rounded-lg transition-all relative overflow-hidden"
                    style={{
                      background: expandedId === conversation.id ? "rgba(88, 166, 255, 0.1)" : "transparent",
                      border: expandedId === conversation.id ? "1px solid rgba(88, 166, 255, 0.3)" : "1px solid transparent",
                    }}
                    whileHover={{ background: "rgba(88, 166, 255, 0.08)", borderColor: "rgba(88, 166, 255, 0.2)" }}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <motion.div animate={{ rotate: expandedId === conversation.id ? 90 : 0 }} transition={{ duration: 0.2 }}>
                          <ChevronRight size={14} style={{ color: "#58a6ff" }} />
                        </motion.div>
                        <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e" }}>
                          {conversation.timestamp}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm line-clamp-2 ml-5" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                      {conversation.question}
                    </p>
                  </motion.button>
                  <AnimatePresence>
                    {expandedId === conversation.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden ml-5 mr-2"
                      >
                        <div className="p-3 mt-1 mb-2 rounded-lg" style={{ background: "rgba(22, 27, 34, 0.6)", border: "1px solid rgba(88, 166, 255, 0.2)" }}>
                          <div className="mb-2">
                            <span className="text-xs font-semibold" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>REASONING</span>
                          </div>
                          <p className="text-xs leading-relaxed mb-3" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>{conversation.reasoning}</p>
                          <div className="mb-1">
                            <span className="text-xs font-semibold" style={{ color: "#3fb950", fontFamily: "'Space Mono', monospace" }}>RESPONSE</span>
                          </div>
                          <p className="text-xs leading-relaxed" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>{conversation.answer}</p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// --- VoiceInterface (exported) ---
export type VoiceState = "idle" | "listening" | "thinking" | "reasoning" | "speaking";

export interface VoiceInterfaceProps {
  state: VoiceState;
  transcript?: string;
  reasoningSummary?: string;
  onWaveformClick: () => void;
  onTextSubmit?: (text: string) => void;
  conversationHistory?: ConversationItem[];
  reasoningSteps: ReasoningStep[];
  response: string;
  wsConnected: boolean;
}

export function VoiceInterface({
  state,
  transcript,
  onWaveformClick,
  onTextSubmit,
  conversationHistory = [],
  reasoningSteps,
  response,
  wsConnected,
}: VoiceInterfaceProps) {
  const [textInput, setTextInput] = useState("");
  return (
    <div className="flex-1 relative flex flex-col overflow-hidden" style={{ fontFamily: "'Crimson Pro', serif" }}>
      <motion.div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse at center, rgba(88, 166, 255, 0.02) 0%, rgba(13, 17, 23, 0) 70%)" }}
      />
      <div className="absolute top-6 right-8 z-20">
        <ConversationHistory conversations={conversationHistory} />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-8">
        <AnimatePresence mode="wait">
          {(state === "idle" || state === "listening" || state === "thinking") && (
            <motion.div
              key="waveform-view"
              initial={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center justify-center"
            >
              <AnimatePresence>
                {transcript && state === "thinking" && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
                    className="mb-12 text-center max-w-2xl"
                  >
                    <motion.p className="text-xs mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>YOU ASKED</motion.p>
                    <motion.p className="text-xl" style={{ color: "#e6edf3" }}>"{transcript}"</motion.p>
                  </motion.div>
                )}
              </AnimatePresence>
              <motion.div onClick={onWaveformClick} className="cursor-pointer" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <SiriWaveform state={state} />
              </motion.div>
              <motion.p className="mt-6 text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                {!wsConnected && "CONNECTING..."}
                {wsConnected && state === "idle" && "TAP TO SPEAK"}
                {state === "listening" && "LISTENING..."}
                {state === "thinking" && "ANALYZING..."}
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {state === "reasoning" && <AgenticReasoning reasoningSteps={reasoningSteps} />}
        </AnimatePresence>
        <AnimatePresence>
          {state === "speaking" && response && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="max-w-2xl w-full mt-8"
            >
              <div className="rounded-xl p-8 relative overflow-hidden" style={{
                background: "rgba(22, 27, 34, 0.4)",
                backdropFilter: "blur(40px)",
                border: "1px solid rgba(88, 166, 255, 0.12)",
              }}>
                <p className="text-sm leading-relaxed" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                  {response}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Text Input Fallback */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl w-full mt-8"
        >
          <div className="flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter" && textInput.trim() && onTextSubmit) {
                  onTextSubmit(textInput.trim());
                  setTextInput("");
                }
              }}
              placeholder="Or type your query here..."
              className="flex-1 px-4 py-3 rounded-lg text-sm"
              style={{
                background: "rgba(22, 27, 34, 0.6)",
                border: "1px solid rgba(88, 166, 255, 0.2)",
                color: "#e6edf3",
                fontFamily: "'Crimson Pro', serif",
              }}
              disabled={!wsConnected || state !== "idle"}
            />
            <motion.button
              onClick={() => {
                if (textInput.trim() && onTextSubmit) {
                  onTextSubmit(textInput.trim());
                  setTextInput("");
                }
              }}
              disabled={!textInput.trim() || !wsConnected || state !== "idle"}
              className="px-6 py-3 rounded-lg text-sm font-medium"
              style={{
                background: wsConnected && textInput.trim() && state === "idle" ? "rgba(88, 166, 255, 0.2)" : "rgba(139, 148, 158, 0.1)",
                border: "1px solid rgba(88, 166, 255, 0.3)",
                color: wsConnected && textInput.trim() && state === "idle" ? "#58a6ff" : "#8b949e",
                fontFamily: "'Space Mono', monospace",
                cursor: wsConnected && textInput.trim() && state === "idle" ? "pointer" : "not-allowed",
              }}
              whileHover={wsConnected && textInput.trim() && state === "idle" ? { scale: 1.05 } : {}}
              whileTap={wsConnected && textInput.trim() && state === "idle" ? { scale: 0.95 } : {}}
            >
              Send
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
