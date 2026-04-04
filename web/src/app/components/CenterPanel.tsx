import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, Clock } from "lucide-react";

// --- ConversationItem (exported for App) ---
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

// --- AgenticReasoning ---
interface ReasoningStep {
  agent: string;
  question: string;
  answer: string;
  color: string;
}

const reasoningSteps: ReasoningStep[] = [
  { agent: "Knowledge Graph Agent", question: "What is the patient's allergy profile?", answer: "Patient has documented Penicillin allergy (severe reaction 2019). No known cross-reactivity with cephalosporins or beta-lactam alternatives.", color: "#58a6ff" },
  { agent: "Drug Interaction Agent", question: "Does Medication B interact with current medications?", answer: "Checking omeprazole 20mg QD... No significant CYP450 interactions detected. Medication B safe to co-administer. Monitor for minor GI effects.", color: "#56d4dd" },
  { agent: "Lab Trend Agent", question: "What are the hemoglobin trends?", answer: "Pre-transfusion: 7.2 g/dL → Post-transfusion: 9.1 g/dL (improvement 26%). Current trend positive. Target >10 g/dL within 2 weeks achievable.", color: "#3fb950" },
  { agent: "Dosing Calculator Agent", question: "What is the appropriate dose for 65kg patient?", answer: "Standard dosing: 500mg BID. Patient weight 65kg within normal range. Renal function normal (eGFR 87). No dose adjustment required.", color: "#d29922" },
  { agent: "Evidence Synthesis Agent", question: "What does the literature say about this approach?", answer: "Meta-analysis (N=2,847): Medication B shows 84% efficacy in penicillin-allergic cohorts. Safety profile favorable. Recommended as first-line alternative.", color: "#8b949e" },
];

interface AgenticReasoningProps {
  reasoningSummary?: string;
  reasoningSteps?: Array<{
    id: string;
    emoji?: string;
    step: string;
    content: string;
    tool?: string;
    params?: any;
  }>;
}

function AgenticReasoning({ reasoningSummary, reasoningSteps = [] }: AgenticReasoningProps) {
  // Group steps by tool - only change card when tool changes!
  // Clean up duplicates and back-and-forth
  const toolGroups = reasoningSteps.reduce((groups: any[], step) => {
    const colors = ["#58a6ff", "#56d4dd", "#3fb950", "#d29922", "#8b949e", "#bc8cff", "#f85149", "#a5a5ff"];
    const currentTool = step.tool || "processing";
    
    // Find if this tool already has a group
    const existingGroup = groups.find(g => g.tool === currentTool);
    
    if (existingGroup) {
      // Only add if query is not duplicate
      const query = step.query || "";
      if (query && !existingGroup.queries.includes(query)) {
        existingGroup.queries.push(query);
      }
      // Only add content if not duplicate
      if (step.content && !existingGroup.contents.includes(step.content)) {
        existingGroup.contents.push(step.content);
      }
    } else {
      // Create new tool group
      groups.push({
        emoji: step.emoji || "⚙️",
        tool: currentTool,
        queries: [step.query || ""].filter(q => q),
        contents: [step.content].filter(c => c),
        color: colors[groups.length % colors.length],
      });
    }
    
    return groups;
  }, []);

  if (toolGroups.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="max-w-3xl w-full"
    >
      <div
        className="rounded-2xl p-5 relative overflow-hidden"
        style={{
          background: "rgba(13, 17, 23, 0.7)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(88, 166, 255, 0.2)",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
          maxHeight: "400px",
          overflowY: "auto",
        }}
      >
        {/* Top accent line */}
        <div className="absolute top-0 left-0 right-0 h-0.5" style={{ background: "linear-gradient(90deg, transparent, #58a6ff, transparent)" }} />
        
        {/* Header */}
        <div className="flex items-center gap-2 mb-4 pb-2 border-b" style={{ borderColor: "rgba(88, 166, 255, 0.15)" }}>
          <motion.div 
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#58a6ff" }}
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <p className="text-[10px] font-semibold uppercase" style={{ color: "#58a6ff", letterSpacing: "1px" }}>
            Reasoning · {toolGroups.length} {toolGroups.length === 1 ? 'Tool' : 'Tools'}
          </p>
        </div>
        
        {/* Tool cards - clean cards with full info */}
        <div className="space-y-3">
          {toolGroups.map((tool: any, idx: number) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.04, duration: 0.2 }}
              className="rounded-lg overflow-hidden"
              style={{
                background: "rgba(22, 27, 34, 0.5)",
                border: `1px solid ${tool.color}20`,
              }}
            >
              {/* Tool header */}
              <div className="flex items-center gap-2 px-3 py-2 border-b" style={{ borderColor: `${tool.color}15` }}>
                <span className="text-base">{tool.emoji}</span>
                <span 
                  className="text-xs font-semibold uppercase tracking-wide"
                  style={{ color: tool.color }}
                >
                  {tool.tool.replace(/_/g, " ")}
                </span>
                <div 
                  className="w-1.5 h-1.5 rounded-full ml-auto"
                  style={{ background: tool.color }}
                />
              </div>
              
              {/* Content */}
              <div className="px-3 py-2.5">
                {/* Queries */}
                {tool.queries.length > 0 && (
                  <div className="mb-2 space-y-1">
                    {tool.queries.map((query: string, qIdx: number) => (
                      <motion.div
                        key={qIdx}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: idx * 0.04 + 0.05 }}
                        className="flex items-start gap-1.5"
                      >
                        <span className="text-xs mt-0.5" style={{ color: tool.color }}>→</span>
                        <p className="text-sm leading-snug" style={{ color: "#8b949e" }}>
                          "{query}"
                        </p>
                      </motion.div>
                    ))}
                  </div>
                )}
                
                {/* Results - show all */}
                {tool.contents.length > 0 && (
                  <div className="space-y-1.5">
                    {tool.contents.map((content: string, cIdx: number) => (
                      <motion.p 
                        key={cIdx}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: idx * 0.04 + 0.1 }}
                        className="text-sm leading-relaxed"
                        style={{ color: "#c9d1d9" }}
                      >
                        {content}
                      </motion.p>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
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
        {isOpen && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
            animate={{ x: ["-100%", "200%"] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
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
  response?: string;
  onWaveformClick: () => void;
  conversationHistory?: ConversationItem[];
  wsConnected?: boolean;
  reasoningSteps?: Array<{
    id: string;
    emoji?: string;
    step: string;
    content: string;
    tool?: string;
    params?: any;
  }>;
}

export function VoiceInterface({
  state,
  transcript,
  reasoningSummary,
  response,
  onWaveformClick,
  conversationHistory = [],
  reasoningSteps = [],
}: VoiceInterfaceProps) {
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
                {transcript && (state === "thinking" || state === "reasoning" || state === "speaking") && (
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
                {state === "idle" && "TAP TO SPEAK"}
                {state === "listening" && "LISTENING... TAP TO STOP & SEND"}
                {state === "thinking" && "ANALYZING..."}
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence mode="wait">
          {state === "reasoning" && (reasoningSummary || reasoningSteps.length > 0) && (
            <AgenticReasoning reasoningSummary={reasoningSummary} reasoningSteps={reasoningSteps} />
          )}
          {state === "speaking" && response && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="p-6 rounded-lg"
              style={{ backgroundColor: "#161b22", border: "1px solid #30363d" }}
            >
              <div className="text-sm font-medium mb-2" style={{ color: "#58a6ff" }}>
                ATRIA AI Response
              </div>
              <div className="text-base leading-relaxed" style={{ color: "#c9d1d9" }}>
                {response}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
