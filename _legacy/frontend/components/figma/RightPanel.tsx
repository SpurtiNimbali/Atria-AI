import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { FileText, Calendar, AlertCircle } from "lucide-react";

// --- CarePlanDocument ---
function CarePlanDocument() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="p-6 space-y-6"
    >
      <div
        className="p-6 rounded-xl relative overflow-hidden"
        style={{
          background: "rgba(13, 17, 23, 0.8)",
          border: "1px solid rgba(88, 166, 255, 0.3)",
          backdropFilter: "blur(10px)",
        }}
      >
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg" style={{ background: "rgba(88, 166, 255, 0.15)", border: "1px solid rgba(88, 166, 255, 0.4)" }}>
            <FileText size={24} style={{ color: "#58a6ff" }} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg mb-1" style={{ fontFamily: "'Space Mono', monospace", color: "#e6edf3" }}>Discharge Instructions</h3>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Post-Operative Care & Patient Education</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-1">
              <Calendar size={14} style={{ color: "#8b949e" }} />
              <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e" }}>Feb 15, 2026</span>
            </div>
          </div>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{
          background: "rgba(248, 81, 73, 0.1)",
          border: "1px solid rgba(248, 81, 73, 0.3)",
          backdropFilter: "blur(10px)",
        }}
      >
        <div className="flex items-start gap-3">
          <AlertCircle size={20} style={{ color: "#f85149", marginTop: "2px" }} />
          <div>
            <h4 className="text-sm font-semibold mb-2" style={{ color: "#f85149", fontFamily: "'Space Mono', monospace" }}>URGENT: WHEN TO SEEK IMMEDIATE CARE</h4>
            <ul className="text-sm space-y-1.5" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
              <li>• Severe chest pain or difficulty breathing</li>
              <li>• Sudden weakness, numbness, or confusion</li>
              <li>• Uncontrolled bleeding or drainage from surgical site</li>
              <li>• Fever above 101.5°F (38.6°C)</li>
              <li>• Signs of allergic reaction (rash, swelling, severe itching)</li>
            </ul>
          </div>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}
      >
        <h4 className="text-sm font-semibold mb-3" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>MEDICATIONS</h4>
        <div className="space-y-4">
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Iron Sulfate 325mg</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Take one tablet twice daily with food. Continue for 3 months or until hemoglobin normalizes. May cause dark stools (normal side effect).</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Omeprazole 20mg</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Take one capsule daily in the morning, 30 minutes before breakfast. Protects stomach lining and reduces iron-related GI irritation.</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Pain Management</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Acetaminophen 500mg every 6 hours as needed for pain. Do not exceed 3000mg in 24 hours. Avoid NSAIDs (ibuprofen, aspirin) for 2 weeks post-transfusion.</p>
          </div>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}
      >
        <h4 className="text-sm font-semibold mb-3" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>ACTIVITY & LIFESTYLE</h4>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Physical Activity</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Rest for 48 hours post-discharge. Gradually resume light activities. Avoid heavy lifting (&gt;10 lbs) for 1 week. Listen to your body and stop if you feel dizzy or fatigued.</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Diet</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Focus on iron-rich foods: lean red meat, poultry, fish, leafy greens, beans, and fortified cereals. Take iron supplements with vitamin C (orange juice) for better absorption. Avoid dairy products within 2 hours of iron intake.</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Hydration</p>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Drink 8-10 glasses of water daily. Adequate hydration supports recovery and helps prevent constipation from iron supplements.</p>
          </div>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}
      >
        <h4 className="text-sm font-semibold mb-3" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>WOUND CARE</h4>
        <div className="space-y-3">
          <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Keep IV site clean and dry for 24 hours. Small bruising is normal. Watch for signs of infection: increased redness, warmth, swelling, or pus drainage.</p>
          <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>You may shower after 24 hours. Pat the area dry gently. Do not soak in baths, hot tubs, or swimming pools for 3 days.</p>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}
      >
        <h4 className="text-sm font-semibold mb-3" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>FOLLOW-UP APPOINTMENTS</h4>
        <div className="space-y-3">
          <div className="p-3 rounded-lg" style={{ background: "rgba(88, 166, 255, 0.1)", border: "1px solid rgba(88, 166, 255, 0.2)" }}>
            <div className="flex justify-between items-start mb-1">
              <span className="text-sm font-semibold" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Lab Work (CBC)</span>
              <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#58a6ff" }}>1 WEEK</span>
            </div>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Schedule within 7 days to check hemoglobin and hematocrit levels. Fasting not required.</p>
          </div>
          <div className="p-3 rounded-lg" style={{ background: "rgba(88, 166, 255, 0.1)", border: "1px solid rgba(88, 166, 255, 0.2)" }}>
            <div className="flex justify-between items-start mb-1">
              <span className="text-sm font-semibold" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>Primary Care Visit</span>
              <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#58a6ff" }}>2 WEEKS</span>
            </div>
            <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}>Follow-up with Dr. Martinez to review lab results and assess recovery progress.</p>
          </div>
        </div>
      </div>

      <div
        className="p-5 rounded-xl relative overflow-hidden"
        style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}
      >
        <h4 className="text-sm font-semibold mb-3" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>ADDITIONAL RESOURCES</h4>
        <div className="space-y-2">
          <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}><span style={{ color: "#e6edf3" }}>24/7 Nurse Hotline:</span> (555) 123-4567</p>
          <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}><span style={{ color: "#e6edf3" }}>Patient Portal:</span> portal.hospital.org</p>
          <p className="text-sm" style={{ color: "#8b949e", fontFamily: "'Crimson Pro', serif" }}><span style={{ color: "#e6edf3" }}>Pharmacy:</span> (555) 789-0123</p>
        </div>
      </div>

      <div className="p-4 rounded-xl text-center" style={{ background: "rgba(88, 166, 255, 0.05)", border: "1px solid rgba(88, 166, 255, 0.2)" }}>
        <p className="text-xs" style={{ color: "#8b949e", fontFamily: "'Space Mono', monospace" }}>Generated by Clinical Intelligence System • Document ID: DIS-2026-0215-001</p>
      </div>
    </motion.div>
  );
}

// --- Timeline (exported) ---
export interface TimelineCommit {
  id: string;
  time: string;
  title: string;
  summary: string;
  isBranch?: boolean;
  branchName?: string;
}

export interface TimelineProps {
  commits: TimelineCommit[];
}

export function Timeline({ commits }: TimelineProps) {
  const [filter, setFilter] = useState<"all" | "careplan">("all");
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="w-96 h-full flex flex-col relative" style={{ background: "#161b22", borderLeft: "1px solid rgba(255, 255, 255, 0.1)" }}>
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "linear-gradient(180deg, rgba(88, 166, 255, 0.02) 0%, transparent 30%, transparent 70%, rgba(88, 166, 255, 0.02) 100%)" }}
      />
      <div className="p-6 border-b relative z-10" style={{ borderColor: "rgba(255, 255, 255, 0.1)" }}>
        <motion.h3
          className="text-base mb-4"
          style={{ fontFamily: "'Space Mono', monospace", color: "#e6edf3" }}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          Timeline • Commits
        </motion.h3>
        <div className="flex gap-2">
          <motion.button
            onClick={() => setFilter("all")}
            className="px-4 py-2 rounded-lg text-sm transition-all relative overflow-hidden"
            style={{
              background: filter === "all" ? "rgba(88, 166, 255, 0.15)" : "transparent",
              color: filter === "all" ? "#58a6ff" : "#8b949e",
              border: filter === "all" ? "1px solid rgba(88, 166, 255, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
              fontFamily: "'Space Mono', monospace",
            }}
            whileHover={{ scale: 1.05, borderColor: "rgba(88, 166, 255, 0.6)" }}
            whileTap={{ scale: 0.95 }}
          >
            {filter === "all" && (
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
            <span className="relative z-10">All</span>
          </motion.button>
          <motion.button
            onClick={() => setFilter("careplan")}
            className="px-4 py-2 rounded-lg text-sm transition-all relative overflow-hidden"
            style={{
              background: filter === "careplan" ? "rgba(88, 166, 255, 0.15)" : "transparent",
              color: filter === "careplan" ? "#58a6ff" : "#8b949e",
              border: filter === "careplan" ? "1px solid rgba(88, 166, 255, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
              fontFamily: "'Space Mono', monospace",
            }}
            whileHover={{ scale: 1.05, borderColor: "rgba(88, 166, 255, 0.6)" }}
            whileTap={{ scale: 0.95 }}
          >
            {filter === "careplan" && (
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
            <span className="relative z-10">CarePlan</span>
          </motion.button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto relative z-10">
        <AnimatePresence mode="wait">
          {filter === "all" ? (
            <motion.div
              key="timeline-view"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="p-6"
            >
              <div className="relative">
                <motion.div
                  className="absolute left-2 top-2 bottom-2 w-0.5"
                  style={{ background: "linear-gradient(180deg, rgba(88, 166, 255, 0.4), rgba(88, 166, 255, 0.1), rgba(88, 166, 255, 0.4))" }}
                  initial={{ scaleY: 0, originY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
                <motion.div
                  className="absolute left-2 w-0.5 h-20"
                  style={{ background: "linear-gradient(180deg, transparent, rgba(88, 166, 255, 0.8), transparent)" }}
                  animate={{ y: [0, 500], opacity: [0, 1, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                />
                <div className="space-y-6">
                  {commits.map((commit, index) => (
                    <motion.div
                      key={commit.id}
                      initial={{ opacity: 0, x: -30, scale: 0.95 }}
                      animate={{ opacity: 1, x: hoveredId === commit.id ? 12 : 0, scale: 1 }}
                      transition={{ duration: 0.4, delay: index * 0.08, ease: [0.25, 0.1, 0.25, 1] }}
                      onMouseEnter={() => setHoveredId(commit.id)}
                      onMouseLeave={() => setHoveredId(null)}
                      className="relative pl-10 cursor-pointer"
                    >
                      <motion.div
                        className="absolute left-0 w-5 h-5 rounded-full flex items-center justify-center"
                        style={{
                          background: commit.isBranch ? "linear-gradient(135deg, #56d4dd, #3fb950)" : "linear-gradient(135deg, #1f6feb, #58a6ff)",
                          border: "2px solid #161b22",
                          boxShadow: commit.isBranch ? "0 0 20px rgba(86, 212, 221, 0.4)" : "0 0 20px rgba(88, 166, 255, 0.4)",
                        }}
                        animate={{
                          scale: hoveredId === commit.id ? 1.3 : 1,
                          boxShadow:
                            hoveredId === commit.id
                              ? commit.isBranch
                                ? "0 0 30px rgba(86, 212, 221, 0.8)"
                                : "0 0 30px rgba(88, 166, 255, 0.8)"
                              : commit.isBranch
                                ? "0 0 20px rgba(86, 212, 221, 0.4)"
                                : "0 0 20px rgba(88, 166, 255, 0.4)",
                        }}
                        transition={{ duration: 0.2 }}
                      >
                        <motion.div
                          className="w-2 h-2 rounded-full bg-white"
                          animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                        />
                      </motion.div>
                      <motion.div
                        className="rounded-xl p-4 relative overflow-hidden group"
                        style={{
                          background: hoveredId === commit.id ? "rgba(22, 27, 34, 0.8)" : "rgba(13, 17, 23, 0.6)",
                          border:
                            hoveredId === commit.id
                              ? commit.isBranch
                                ? "1px solid rgba(86, 212, 221, 0.4)"
                                : "1px solid rgba(88, 166, 255, 0.4)"
                              : "1px solid rgba(255, 255, 255, 0.1)",
                          fontFamily: "'Crimson Pro', serif",
                          backdropFilter: "blur(10px)",
                          boxShadow:
                            hoveredId === commit.id
                              ? commit.isBranch
                                ? "0 8px 32px rgba(86, 212, 221, 0.15)"
                                : "0 8px 32px rgba(88, 166, 255, 0.15)"
                              : "none",
                        }}
                        transition={{ duration: 0.3 }}
                      >
                        {hoveredId === commit.id && (
                          <motion.div
                            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                            initial={{ x: "-100%" }}
                            animate={{ x: "200%" }}
                            transition={{ duration: 0.8, ease: "easeInOut" }}
                          />
                        )}
                        <div className="flex items-start justify-between mb-2 relative z-10">
                          <span className="text-xs" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e" }}>{commit.time}</span>
                          {commit.isBranch && (
                            <motion.span
                              className="px-2.5 py-1 rounded-md text-xs flex items-center gap-1.5"
                              style={{
                                background: "rgba(86, 212, 221, 0.15)",
                                color: "#56d4dd",
                                border: "1px solid rgba(86, 212, 221, 0.4)",
                                fontFamily: "'Space Mono', monospace",
                                boxShadow: "0 0 15px rgba(86, 212, 221, 0.2)",
                              }}
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: index * 0.08 + 0.2 }}
                              whileHover={{ scale: 1.05, boxShadow: "0 0 20px rgba(86, 212, 221, 0.4)" }}
                            >
                              <motion.span animate={{ rotate: [0, 10, -10, 0] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}>🌿</motion.span>
                              {commit.branchName}
                            </motion.span>
                          )}
                        </div>
                        <h4 className="text-sm mb-1.5 relative z-10" style={{ color: "#e6edf3" }}>{commit.title}</h4>
                        <p className="text-xs relative z-10" style={{ color: "#8b949e" }}>{commit.summary}</p>
                      </motion.div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div key="careplan-view" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <CarePlanDocument />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
