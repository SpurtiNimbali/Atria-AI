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

function AgenticReasoning() {
  const [currentStep, setCurrentStep] = useState(0);
  const [phase, setPhase] = useState<"question" | "answer" | "transition">("question");

  useEffect(() => {
    const questionDuration = 800;
    const answerDuration = 1600;
    const transitionDuration = 600;

    if (phase === "question") {
      const t = setTimeout(() => setPhase("answer"), questionDuration);
      return () => clearTimeout(t);
    }
    if (phase === "answer") {
      const t = setTimeout(() => setPhase("transition"), answerDuration);
      return () => clearTimeout(t);
    }
    if (phase === "transition") {
      const t = setTimeout(() => {
        setCurrentStep((currentStep + 1) % reasoningSteps.length);
        setPhase("question");
      }, transitionDuration);
      return () => clearTimeout(t);
    }
  }, [currentStep, phase]);

  const step = reasoningSteps[currentStep];

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
            style={{ background: step.color }}
            animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
          <AnimatePresence mode="wait">
            <motion.p
              key={currentStep}
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              transition={{ duration: 0.3 }}
              className="text-xs"
              style={{ fontFamily: "'Space Mono', monospace", color: step.color, letterSpacing: "0.5px" }}
            >
              {step.agent.toUpperCase()}
            </motion.p>
          </AnimatePresence>
        </div>
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {(phase === "question" || phase === "answer") && (
              <motion.div
                key={`question-${currentStep}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex items-start gap-2">
                  <span className="text-xs mt-1" style={{ color: "#8b949e", fontFamily: "'Space Mono', monospace" }}>Q:</span>
                  <p className="text-sm font-medium flex-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                    {step.question}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence mode="wait">
            {phase === "answer" && (
              <motion.div
                key={`answer-${currentStep}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              >
                <div className="flex items-start gap-2">
                  <span className="text-xs mt-1" style={{ color: step.color, fontFamily: "'Space Mono', monospace" }}>A:</span>
                  <p className="text-sm flex-1 leading-relaxed" style={{ color: "#c9d1d9", fontFamily: "'Crimson Pro', serif" }}>
                    {step.answer}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-1.5 mt-6">
          {reasoningSteps.map((_, index) => (
            <motion.div
              key={index}
              className="h-1 rounded-full"
              style={{ flex: 1, background: index === currentStep ? step.color : "rgba(139, 148, 158, 0.2)" }}
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
  onWaveformClick: () => void;
  conversationHistory?: ConversationItem[];
}

export function VoiceInterface({
  state,
  transcript,
  onWaveformClick,
  conversationHistory = [],
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
                {state === "idle" && "TAP TO SPEAK"}
                {state === "listening" && "LISTENING..."}
                {state === "thinking" && "ANALYZING..."}
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {state === "reasoning" && <AgenticReasoning />}
        </AnimatePresence>
      </div>
    </div>
  );
}
