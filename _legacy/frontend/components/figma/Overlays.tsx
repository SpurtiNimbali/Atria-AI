import { motion, AnimatePresence } from "framer-motion";
import { X, Check, GitBranch } from "lucide-react";

// --- Citation type (exported for App) ---
export interface Citation {
  id: string;
  name: string;
  type: "EHR" | "Guideline" | "Study";
  excerpt: string;
}

// --- ReasoningCompleteNotification ---
export function ReasoningCompleteNotification({ isVisible, message }: { isVisible: boolean; message: string }) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -100 }}
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
          className="fixed top-8 left-1/2 -translate-x-1/2 z-50"
        >
          <motion.div
            className="rounded-lg px-6 py-4 flex items-center gap-3"
            style={{
              background: "rgba(22, 27, 34, 0.95)",
              backdropFilter: "blur(40px)",
              border: "1px solid rgba(88, 166, 255, 0.3)",
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.5)",
              fontFamily: "'Crimson Pro', serif",
            }}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <motion.div
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ background: "rgba(63, 185, 80, 0.15)", border: "1px solid rgba(63, 185, 80, 0.3)" }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            >
              <Check className="w-4 h-4" style={{ color: "#3fb950" }} />
            </motion.div>
            <div>
              <p className="text-sm" style={{ color: "#e6edf3", fontWeight: 500 }}>{message}</p>
              <p className="text-xs mt-0.5" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.3px" }}>AI is speaking...</p>
            </div>
            <motion.div
              className="absolute top-0 left-0 right-0 h-0.5 overflow-hidden rounded-t-lg"
              style={{ background: "rgba(88, 166, 255, 0.1)" }}
            >
              <motion.div
                className="h-full"
                style={{ background: "linear-gradient(90deg, transparent, #58a6ff, transparent)", width: "50%" }}
                animate={{ x: ["-100%", "300%"] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              />
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// --- CitationDrawer ---
export function CitationDrawer({
  isOpen,
  citation,
  onClose,
}: {
  isOpen: boolean;
  citation: Citation | null;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {isOpen && citation && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50"
            style={{ background: "rgba(0, 0, 0, 0.6)", backdropFilter: "blur(8px)" }}
          />
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
            className="fixed right-0 top-0 bottom-0 w-[480px] z-50"
            style={{
              background: "rgba(22, 27, 34, 0.98)",
              backdropFilter: "blur(40px)",
              borderLeft: "1px solid rgba(88, 166, 255, 0.2)",
              boxShadow: "-20px 0 60px rgba(0, 0, 0, 0.5), 0 0 1px rgba(88, 166, 255, 0.3) inset",
              fontFamily: "'Crimson Pro', serif",
            }}
          >
            <div className="p-6 border-b flex items-start justify-between" style={{ borderColor: "rgba(255, 255, 255, 0.1)" }}>
              <div className="flex-1">
                <div className="text-xs mb-2" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  {citation.type.toUpperCase()}
                </div>
                <h3 className="text-lg" style={{ color: "#e6edf3" }}>{citation.name}</h3>
              </div>
              <motion.button
                onClick={onClose}
                className="p-2 rounded-lg"
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "#8b949e",
                }}
                whileHover={{ background: "rgba(255, 255, 255, 0.1)", borderColor: "rgba(88, 166, 255, 0.3)", color: "#e6edf3" }}
                whileTap={{ scale: 0.95 }}
              >
                <X className="w-5 h-5" />
              </motion.button>
            </div>
            <div className="p-6 overflow-y-auto" style={{ maxHeight: "calc(100vh - 100px)" }}>
              <div
                className="rounded-lg p-6"
                style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(88, 166, 255, 0.15)" }}
              >
                <p className="text-sm leading-relaxed" style={{ color: "#c9d1d9" }}>{citation.excerpt}</p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// --- Outcome type & DecisionTreeModal ---
export interface Outcome {
  id: string;
  name: string;
  description: string;
  risks: string[];
  confidence: number;
}

export function DecisionTreeModal({
  isOpen,
  branchName,
  outcomes,
  onClose,
  onOutcomeClick,
}: {
  isOpen: boolean;
  branchName: string;
  outcomes: Outcome[];
  onClose: () => void;
  onOutcomeClick: (outcomeId: string) => void;
}) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50"
            style={{ background: "rgba(0, 0, 0, 0.7)", backdropFilter: "blur(8px)" }}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-8"
          >
            <div
              className="w-full max-w-5xl max-h-[85vh] overflow-y-auto rounded-xl relative"
              style={{
                background: "#161b22",
                border: "1px solid rgba(88, 166, 255, 0.2)",
                boxShadow: "0 20px 80px rgba(0, 0, 0, 0.6)",
                fontFamily: "'Crimson Pro', serif",
              }}
            >
              <div
                className="p-6 border-b sticky top-0 z-10 flex items-start justify-between"
                style={{ borderColor: "rgba(255, 255, 255, 0.1)", background: "#161b22" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <GitBranch className="w-5 h-5" style={{ color: "#58a6ff" }} />
                    <h3 className="text-lg" style={{ fontFamily: "'Space Mono', monospace", color: "#e6edf3" }}>Decision Tree</h3>
                  </div>
                  <p className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.3px" }}>{branchName}</p>
                </div>
                <motion.button
                  onClick={onClose}
                  className="p-2 rounded-lg"
                  style={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#8b949e",
                  }}
                  whileHover={{ background: "rgba(255, 255, 255, 0.1)", color: "#e6edf3" }}
                  whileTap={{ scale: 0.95 }}
                >
                  <X className="w-5 h-5" />
                </motion.button>
              </div>
              <div className="p-8">
                <div className="flex flex-col items-center">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-lg p-4 relative"
                    style={{
                      background: "rgba(22, 27, 34, 0.8)",
                      border: "1px solid rgba(88, 166, 255, 0.3)",
                      boxShadow: "0 0 20px rgba(88, 166, 255, 0.1)",
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: "#58a6ff" }} />
                      <p className="text-sm" style={{ fontFamily: "'Space Mono', monospace", color: "#e6edf3" }}>
                        {branchName.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                      </p>
                    </div>
                  </motion.div>
                  <div className="relative w-full flex justify-center" style={{ height: "120px", marginTop: "20px" }}>
                    <motion.div
                      className="absolute w-4 h-4 rounded-full"
                      style={{
                        top: "0",
                        left: "50%",
                        transform: "translateX(-50%)",
                        background: "#161b22",
                        border: "2px solid rgba(88, 166, 255, 0.5)",
                        zIndex: 10,
                      }}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3 }}
                    >
                      <motion.div
                        className="absolute inset-0 rounded-full"
                        style={{ border: "2px solid rgba(88, 166, 255, 0.3)" }}
                        animate={{ scale: [1, 1.8, 1.8], opacity: [0.6, 0, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                      />
                    </motion.div>
                    <svg className="absolute inset-0 w-full h-full" style={{ overflow: "visible" }} viewBox="0 0 100 100" preserveAspectRatio="none">
                      {outcomes.map((_, index) => {
                        const totalOutcomes = outcomes.length;
                        const startX = 50, startY = 0;
                        const endX = totalOutcomes === 3 ? 20 + index * 30 : (100 / (totalOutcomes + 1)) * (index + 1);
                        const endY = 100, controlY = 50;
                        return (
                          <motion.path
                            key={index}
                            d={`M ${startX} ${startY} Q ${startX} ${controlY}, ${endX} ${endY}`}
                            fill="none"
                            stroke="rgba(88, 166, 255, 0.3)"
                            strokeWidth="2"
                            vectorEffect="non-scaling-stroke"
                            initial={{ pathLength: 0, opacity: 0 }}
                            animate={{ pathLength: 1, opacity: 1 }}
                            transition={{ delay: 0.5 + index * 0.1, duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
                          />
                        );
                      })}
                    </svg>
                  </div>
                  <div className="grid grid-cols-3 gap-6 w-full">
                    {outcomes.map((outcome, index) => (
                      <motion.button
                        key={outcome.id}
                        onClick={() => onOutcomeClick(outcome.id)}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8 + index * 0.1 }}
                        className="rounded-lg p-5 text-left cursor-pointer relative"
                        style={{
                          background: "rgba(22, 27, 34, 0.8)",
                          border: "1px solid rgba(88, 166, 255, 0.2)",
                        }}
                        whileHover={{
                          scale: 1.03,
                          borderColor: "rgba(88, 166, 255, 0.5)",
                          boxShadow: "0 8px 32px rgba(88, 166, 255, 0.15)",
                        }}
                        whileTap={{ scale: 0.97 }}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className="w-3 h-3 rounded-full mt-1" style={{ background: "#56d4dd" }} />
                          <h4 className="text-sm flex-1" style={{ color: "#e6edf3", fontWeight: 500 }}>{outcome.name}</h4>
                        </div>
                        <p className="text-xs mb-4 leading-relaxed pl-6" style={{ color: "#8b949e" }}>{outcome.description}</p>
                        <div className="mb-4 pl-6">
                          <p className="text-xs mb-2" style={{ fontFamily: "'Space Mono', monospace", color: "#d29922", letterSpacing: "0.3px" }}>RISKS TO MONITOR</p>
                          <div className="space-y-1.5">
                            {outcome.risks.map((risk, riskIndex) => (
                              <div key={riskIndex} className="flex items-start gap-2">
                                <span className="text-xs mt-0.5" style={{ color: "#d29922" }}>•</span>
                                <span className="text-xs leading-relaxed" style={{ color: "#8b949e" }}>{risk}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="pl-6">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.3px" }}>CONFIDENCE</span>
                            <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#58a6ff", fontWeight: 600 }}>{outcome.confidence}%</span>
                          </div>
                          <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: "rgba(88, 166, 255, 0.1)" }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ background: "#58a6ff" }}
                              initial={{ width: 0 }}
                              animate={{ width: `${outcome.confidence}%` }}
                              transition={{ duration: 1, delay: 1 + index * 0.1, ease: [0.25, 0.1, 0.25, 1] }}
                            />
                          </div>
                        </div>
                        <motion.div
                          className="absolute bottom-2 right-2 text-xs"
                          style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}
                          initial={{ opacity: 0 }}
                          whileHover={{ opacity: 1 }}
                        >
                          Click to expand →
                        </motion.div>
                      </motion.button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
