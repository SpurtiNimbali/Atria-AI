import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";
import { ChevronDown, ChevronUp, X } from "lucide-react";

// --- CitationChip ---
interface CitationChipProps {
  label: string;
  type: "EHR" | "Guideline" | "Study";
  onClick: () => void;
}

function CitationChip({ label, type, onClick }: CitationChipProps) {
  const getTypeColor = () => {
    switch (type) {
      case "EHR":
        return { bg: "rgba(88, 166, 255, 0.1)", border: "rgba(88, 166, 255, 0.3)", text: "#58a6ff" };
      case "Guideline":
        return { bg: "rgba(86, 212, 221, 0.1)", border: "rgba(86, 212, 221, 0.3)", text: "#56d4dd" };
      case "Study":
        return { bg: "rgba(188, 140, 255, 0.1)", border: "rgba(188, 140, 255, 0.3)", text: "#bc8cff" };
    }
  };
  const colors = getTypeColor();
  return (
    <motion.button
      onClick={onClick}
      className="px-3 py-1.5 rounded-md text-xs cursor-pointer"
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        color: colors.text,
        fontFamily: "'Space Mono', monospace",
        letterSpacing: "0.3px",
      }}
      whileHover={{ scale: 1.05, borderColor: colors.text, boxShadow: `0 0 15px ${colors.border}` }}
      whileTap={{ scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      {label}
    </motion.button>
  );
}

// --- Vitals ---
interface VitalData {
  label: string;
  value: string;
  trend: "up" | "down" | "stable";
  meaning: string;
  confidence: number;
}

interface VitalsProps {
  status: "Stable" | "Monitoring" | "Critical";
  summary: string;
  vitals: VitalData[];
  confidenceDrivers: { dataRecency: string; sensorFidelity: string; ehrInfluence: string };
  onCitationClick: (citationId: string) => void;
}

function Vitals({ status, summary, vitals, confidenceDrivers, onCitationClick }: VitalsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const getStatusColor = () => {
    switch (status) {
      case "Stable":
        return { bg: "rgba(63, 185, 80, 0.1)", border: "rgba(63, 185, 80, 0.3)", text: "#3fb950" };
      case "Monitoring":
        return { bg: "rgba(210, 153, 34, 0.1)", border: "rgba(210, 153, 34, 0.3)", text: "#d29922" };
      case "Critical":
        return { bg: "rgba(248, 81, 73, 0.1)", border: "rgba(248, 81, 73, 0.3)", text: "#f85149" };
    }
  };
  const statusColors = getStatusColor();
  const getTrendIcon = (trend: string) => (trend === "up" ? "↑" : trend === "down" ? "↓" : "→");

  return (
    <motion.div
      className="rounded-xl relative overflow-hidden flex-shrink-0"
      style={{
        background: "rgba(22, 27, 34, 0.8)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.1, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left cursor-pointer"
        whileHover={{ background: "rgba(22, 27, 34, 0.9)" }}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="text-sm mb-2" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
              VITALS
            </h4>
            <div className="flex items-center gap-2">
              <div
                className="px-3 py-1 rounded-md text-xs flex items-center gap-2"
                style={{
                  background: statusColors.bg,
                  border: `1px solid ${statusColors.border}`,
                  color: statusColors.text,
                  fontFamily: "'Space Mono', monospace",
                }}
              >
                {status !== "Stable" && (
                  <motion.div
                    className="w-2 h-2 rounded-full"
                    style={{ background: statusColors.text }}
                    animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  />
                )}
                {status}
              </div>
            </div>
          </div>
          <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.3 }}>
            <ChevronDown className="w-5 h-5" style={{ color: "#8b949e" }} />
          </motion.div>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {vitals.slice(0, 4).map((vital, index) => (
            <div key={index}>
              <span style={{ color: "#8b949e", fontSize: "12px" }}>{vital.label}</span>
              <div style={{ color: "#e6edf3", fontFamily: "'Space Mono', monospace" }}>{vital.value}</div>
            </div>
          ))}
        </div>
        <p className="text-sm mt-3" style={{ color: "#8b949e" }}>{summary}</p>
      </motion.button>
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden border-t"
            style={{ borderColor: "rgba(255, 255, 255, 0.1)" }}
          >
            <div className="p-6 space-y-6">
              <div className="space-y-4">
                {vitals.map((vital, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="rounded-lg p-4"
                    style={{ background: "rgba(13, 17, 23, 0.6)", border: "1px solid rgba(255, 255, 255, 0.05)" }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm" style={{ color: "#8b949e" }}>{vital.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-lg" style={{ color: "#e6edf3", fontFamily: "'Space Mono', monospace" }}>
                          {vital.value}
                        </span>
                        <span
                          className="text-sm"
                          style={{
                            color:
                              vital.trend === "up" ? "#3fb950" : vital.trend === "down" ? "#f85149" : "#8b949e",
                          }}
                        >
                          {getTrendIcon(vital.trend)}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm mb-2" style={{ color: "#c9d1d9" }}>{vital.meaning}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs" style={{ color: "#8b949e" }}>Confidence:</span>
                      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(88, 166, 255, 0.1)" }}>
                        <motion.div
                          className="h-full rounded-full"
                          style={{ background: "linear-gradient(90deg, #1f6feb, #58a6ff)" }}
                          initial={{ width: 0 }}
                          animate={{ width: `${vital.confidence}%` }}
                          transition={{ duration: 1, delay: index * 0.1 + 0.2 }}
                        />
                      </div>
                      <span className="text-xs" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>
                        {vital.confidence}%
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
              <div>
                <h5 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  CONFIDENCE DRIVERS
                </h5>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span style={{ color: "#8b949e" }}>Data Recency</span>
                    <span style={{ color: "#e6edf3" }}>{confidenceDrivers.dataRecency}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: "#8b949e" }}>Sensor Fidelity</span>
                    <span style={{ color: "#e6edf3" }}>{confidenceDrivers.sensorFidelity}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: "#8b949e" }}>EHR Influence</span>
                    <span style={{ color: "#e6edf3" }}>{confidenceDrivers.ehrInfluence}</span>
                  </div>
                </div>
              </div>
              <div>
                <h5 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  DATA SOURCES
                </h5>
                <div className="flex flex-wrap gap-2">
                  <CitationChip label="Patient Monitor" type="EHR" onClick={() => onCitationClick("ehr-monitor")} />
                  <CitationChip label="Lab Results" type="EHR" onClick={() => onCitationClick("ehr-lab")} />
                  <CitationChip label="Clinical Guidelines" type="Guideline" onClick={() => onCitationClick("guideline-vitals")} />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// --- Treatment ---
interface TreatmentProps {
  name: string;
  description: string;
  rationale: string;
  alternatives: string[];
  patientFactors: string[];
  evidenceSupport: string;
  confidence: number;
  onCitationClick: (citationId: string) => void;
}

function Treatment({
  name,
  description,
  rationale,
  alternatives,
  patientFactors,
  evidenceSupport,
  confidence,
  onCitationClick,
}: TreatmentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      className="rounded-xl relative overflow-hidden flex-shrink-0"
      style={{
        background: "rgba(22, 27, 34, 0.8)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left cursor-pointer"
        whileHover={{ background: "rgba(22, 27, 34, 0.9)" }}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ background: "#56d4dd" }} />
            <h4 className="text-sm" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
              TREATMENT
            </h4>
          </div>
          <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.3 }}>
            <ChevronDown className="w-5 h-5" style={{ color: "#8b949e" }} />
          </motion.div>
        </div>
        <p className="text-base mb-1" style={{ color: "#e6edf3" }}>{name}</p>
        <p className="text-sm" style={{ color: "#8b949e" }}>{description}</p>
      </motion.button>
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden border-t"
            style={{ borderColor: "rgba(255, 255, 255, 0.1)" }}
          >
            <div className="p-6 space-y-6">
              <div>
                <h5 className="text-sm mb-2" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  DECISION RATIONALE
                </h5>
                <p className="text-sm leading-relaxed" style={{ color: "#c9d1d9" }}>{rationale}</p>
              </div>
              <div>
                <h5 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  ALTERNATIVES CONSIDERED
                </h5>
                <div className="space-y-2">
                  {alternatives.map((alt, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-start gap-2 text-sm"
                    >
                      <span style={{ color: "#8b949e" }}>•</span>
                      <span style={{ color: "#c9d1d9" }}>{alt}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  PATIENT-SPECIFIC FACTORS
                </h5>
                <div className="space-y-2">
                  {patientFactors.map((factor, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-start gap-2 text-sm"
                    >
                      <span style={{ color: "#8b949e" }}>•</span>
                      <span style={{ color: "#c9d1d9" }}>{factor}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="text-sm mb-2" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  EVIDENCE SUPPORT
                </h5>
                <p className="text-sm leading-relaxed mb-3" style={{ color: "#c9d1d9" }}>{evidenceSupport}</p>
                <div className="flex flex-wrap gap-2">
                  <CitationChip label="AHA Guidelines 2024" type="Guideline" onClick={() => onCitationClick("guideline-aha")} />
                  <CitationChip label="NEJM Study" type="Study" onClick={() => onCitationClick("study-nejm")} />
                  <CitationChip label="Patient History" type="EHR" onClick={() => onCitationClick("ehr-history")} />
                </div>
              </div>
              <div>
                <h5 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                  CONFIDENCE ASSESSMENT
                </h5>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "rgba(88, 166, 255, 0.1)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: "linear-gradient(90deg, #1f6feb, #58a6ff)" }}
                      initial={{ width: 0 }}
                      animate={{ width: `${confidence}%` }}
                      transition={{ duration: 1.2, ease: [0.25, 0.1, 0.25, 1] }}
                    />
                  </div>
                  <span className="text-sm" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace", fontWeight: 600 }}>
                    {confidence}%
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// --- RecoveryPlan ---
interface RecoveryPlanProps {
  plan: string;
  estimatedTime: string;
  confidence: number;
  rationale: string;
  onCitationClick: (citationId: string) => void;
}

function RecoveryPlan({ plan, estimatedTime, confidence, rationale, onCitationClick }: RecoveryPlanProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showReasoningFlow, setShowReasoningFlow] = useState(false);

  const reasoningNodes = [
    {
      title: "Patient Inputs",
      items: [
        "Current hemoglobin: 9.1 g/dL (improving)",
        "Recent transfusion: 2 units completed",
        "Vital signs stable",
        "No active bleeding identified",
      ],
    },
    {
      title: "Risk Stratification",
      items: [
        "Low risk for re-bleeding",
        "Hemodynamically stable",
        "Adequate response to transfusion",
        "No underlying coagulopathy",
      ],
    },
    {
      title: "Treatment Pathway Selected",
      items: [
        "Continue observation protocol",
        "Monitor hemoglobin q6h",
        "Maintain IV access",
        "Advance diet as tolerated",
      ],
    },
  ];

  const supportingReasons = [
    "Patient showing consistent improvement in hemoglobin levels",
    "Vital signs remain within normal parameters",
    "No evidence of ongoing blood loss",
    "Similar cases show 24-48h recovery timeline",
  ];

  const risks = [
    "Potential for delayed re-bleeding (5-8% risk)",
    "Transfusion-related complications (monitored)",
    "Need for additional intervention if Hgb drops below 8.0",
  ];

  return (
    <>
      <motion.div
        className="rounded-xl relative overflow-hidden flex-shrink-0"
        style={{
          background: "rgba(22, 27, 34, 0.8)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <motion.button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full p-6 text-left cursor-pointer"
          whileHover={{ background: "rgba(22, 27, 34, 0.9)" }}
        >
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
              RECOVERY PLAN
            </h4>
            <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.3 }}>
              <ChevronDown className="w-5 h-5" style={{ color: "#8b949e" }} />
            </motion.div>
          </div>
          <p className="text-base mb-2" style={{ color: "#e6edf3" }}>{plan}</p>
          <div className="flex items-center gap-4 text-sm">
            <div>
              <span style={{ color: "#8b949e" }}>Est. Time: </span>
              <span style={{ color: "#e6edf3" }}>{estimatedTime}</span>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>Confidence: </span>
              <span style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>{confidence}%</span>
            </div>
          </div>
        </motion.button>
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
              className="overflow-hidden border-t"
              style={{ borderColor: "rgba(255, 255, 255, 0.1)" }}
            >
              <div className="p-5 space-y-4">
                <p className="text-sm leading-relaxed" style={{ color: "#c9d1d9" }}>{rationale}</p>
                <motion.button
                  onClick={() => setShowReasoningFlow(true)}
                  className="w-full px-4 py-3 rounded-lg text-sm"
                  style={{
                    background: "rgba(88, 166, 255, 0.1)",
                    border: "1px solid rgba(88, 166, 255, 0.3)",
                    color: "#58a6ff",
                    fontFamily: "'Space Mono', monospace",
                    letterSpacing: "0.3px",
                  }}
                  whileHover={{
                    background: "rgba(88, 166, 255, 0.15)",
                    borderColor: "rgba(88, 166, 255, 0.5)",
                    boxShadow: "0 0 20px rgba(88, 166, 255, 0.2)",
                  }}
                  whileTap={{ scale: 0.98 }}
                >
                  View Reasoning Model
                </motion.button>
                <div className="flex flex-wrap gap-2">
                  <CitationChip label="Recovery Protocol" type="Guideline" onClick={() => onCitationClick("guideline-recovery")} />
                  <CitationChip label="Patient Data" type="EHR" onClick={() => onCitationClick("ehr-patient")} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {showReasoningFlow && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowReasoningFlow(false)}
              className="fixed inset-0 z-50"
              style={{ background: "rgba(0, 0, 0, 0.7)", backdropFilter: "blur(12px)" }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
              className="fixed inset-0 z-50 flex items-center justify-center p-8"
            >
              <div
                className="w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-2xl p-8 relative"
                style={{
                  background: "rgba(22, 27, 34, 0.98)",
                  backdropFilter: "blur(40px)",
                  border: "1px solid rgba(88, 166, 255, 0.2)",
                  boxShadow: "0 20px 80px rgba(0, 0, 0, 0.6), 0 0 1px rgba(88, 166, 255, 0.3) inset",
                  fontFamily: "'Crimson Pro', serif",
                }}
              >
                <div className="flex items-start justify-between mb-8">
                  <h3 className="text-2xl" style={{ color: "#e6edf3" }}>Clinical Reasoning Model</h3>
                  <motion.button
                    onClick={() => setShowReasoningFlow(false)}
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
                <div className="space-y-6">
                  {reasoningNodes.map((node, index) => (
                    <div key={index}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.15 }}
                        className="rounded-xl p-6"
                        style={{ background: "rgba(13, 17, 23, 0.8)", border: "1px solid rgba(88, 166, 255, 0.2)" }}
                      >
                        <h4 className="text-sm mb-4" style={{ fontFamily: "'Space Mono', monospace", color: "#58a6ff", letterSpacing: "0.5px" }}>
                          {node.title}
                        </h4>
                        <div className="space-y-2">
                          {node.items.map((item, itemIndex) => (
                            <div key={itemIndex} className="flex items-start gap-2 text-sm">
                              <span style={{ color: "#8b949e" }}>•</span>
                              <span style={{ color: "#c9d1d9" }}>{item}</span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                      {index < reasoningNodes.length - 1 && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: index * 0.15 + 0.1 }}
                          className="flex justify-center my-3"
                        >
                          <div className="text-2xl" style={{ color: "rgba(88, 166, 255, 0.4)" }}>↓</div>
                        </motion.div>
                      )}
                    </div>
                  ))}
                </div>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="mt-8 rounded-xl p-6"
                  style={{ background: "rgba(63, 185, 80, 0.1)", border: "1px solid rgba(63, 185, 80, 0.2)" }}
                >
                  <h4 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#3fb950", letterSpacing: "0.5px" }}>
                    SUPPORTING FACTORS
                  </h4>
                  <div className="space-y-2">
                    {supportingReasons.map((reason, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        <span style={{ color: "#3fb950" }}>✓</span>
                        <span style={{ color: "#c9d1d9" }}>{reason}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="mt-4 rounded-xl p-6"
                  style={{ background: "rgba(210, 153, 34, 0.1)", border: "1px solid rgba(210, 153, 34, 0.2)" }}
                >
                  <h4 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#d29922", letterSpacing: "0.5px" }}>
                    RISKS & CONSIDERATIONS
                  </h4>
                  <div className="space-y-2">
                    {risks.map((risk, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        <span style={{ color: "#d29922" }}>⚠</span>
                        <span style={{ color: "#c9d1d9" }}>{risk}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="mt-6">
                  <h4 className="text-sm mb-3" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e", letterSpacing: "0.5px" }}>
                    OVERALL CONFIDENCE
                  </h4>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "rgba(88, 166, 255, 0.1)" }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: "linear-gradient(90deg, #1f6feb, #58a6ff)" }}
                        initial={{ width: 0 }}
                        animate={{ width: `${confidence}%` }}
                        transition={{ duration: 1.5, ease: [0.25, 0.1, 0.25, 1] }}
                      />
                    </div>
                    <span className="text-lg" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace", fontWeight: 600 }}>
                      {confidence}%
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <CitationChip label="Clinical Protocol" type="Guideline" onClick={() => onCitationClick("guideline-protocol")} />
                    <CitationChip label="Evidence Base" type="Study" onClick={() => onCitationClick("study-evidence")} />
                    <CitationChip label="Patient Records" type="EHR" onClick={() => onCitationClick("ehr-records")} />
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

// --- PatientContext (exported) ---
export interface PatientContextProps {
  patient: { name: string; mrn: string; status: string };
  dashboardData?: any;
  onCitationClick: (citationId: string) => void;
}

export function PatientContext({ patient, dashboardData, onCitationClick }: PatientContextProps) {
  // Use dashboard data if available, otherwise use defaults
  const vitalsFromData = dashboardData?.vitals || [];
  const vitalsData = {
    status: "Stable" as const,
    summary: "All parameters within acceptable ranges, trending positive",
    vitals: vitalsFromData.length > 0
      ? vitalsFromData.map((v: any) => ({
          label: v.type === "HR" ? "Heart Rate" : v.type === "BP" ? "Blood Pressure" : v.type === "SpO2" ? "SpO₂" : "Temperature",
          value: `${v.value} ${v.unit || ""}`,
          trend: "stable" as const,
          meaning: `Taken at ${new Date(v.taken_at).toLocaleTimeString()}`,
          confidence: 95
        }))
      : [
          { label: "Heart Rate", value: "78 bpm", trend: "stable" as const, meaning: "Normal sinus rhythm, well-controlled", confidence: 95 },
          { label: "Blood Pressure", value: "118/76", trend: "stable" as const, meaning: "Optimal pressure, no intervention needed", confidence: 92 },
          { label: "SpO₂", value: "98%", trend: "stable" as const, meaning: "Excellent oxygen saturation on room air", confidence: 98 },
          { label: "Temperature", value: "98.4°F", trend: "stable" as const, meaning: "Afebrile, no signs of infection", confidence: 96 },
        ],
    confidenceDrivers: { dataRecency: "< 5 minutes", sensorFidelity: "High (FDA-cleared)", ehrInfluence: "Moderate (historical)" },
  };

  const treatmentData = {
    name: "Post-transfusion recovery",
    description: "Observation protocol with hemoglobin monitoring",
    rationale:
      "Patient responded well to 2-unit transfusion with hemoglobin improving from 7.2 to 9.1 g/dL. Vitals remain stable with no signs of active bleeding. Evidence supports conservative management with close monitoring rather than aggressive intervention at this stage.",
    alternatives: [
      "Additional transfusion (deferred - Hgb adequate)",
      "Immediate endoscopy (not indicated - stable vitals)",
      "ICU admission (unnecessary - hemodynamically stable)",
    ],
    patientFactors: [
      "Known Penicillin allergy - alternative prophylaxis selected",
      "History of GERD - proton pump inhibitor continued",
      "Age 52 - good baseline health, low surgical risk",
      "No anticoagulant use - reduced bleeding risk",
    ],
    evidenceSupport:
      "AHA 2024 guidelines recommend conservative approach for hemodynamically stable patients with Hgb >8.0 g/dL. NEJM study (2023) showed similar outcomes between observation and immediate intervention in this cohort.",
    confidence: 87,
  };

  const recoveryPlanData = {
    plan: "24-48 hour observation with serial monitoring",
    estimatedTime: "24-48 hours",
    confidence: 85,
    rationale:
      "Based on current trajectory and evidence from similar cases, patient is expected to maintain stable hemoglobin levels and can safely transition to discharge within 24-48 hours with appropriate outpatient follow-up.",
  };

  return (
    <div className="w-96 h-full p-8 flex flex-col gap-6 overflow-y-auto relative" style={{ fontFamily: "'Crimson Pro', serif", scrollBehavior: "smooth" }}>
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "linear-gradient(180deg, rgba(88, 166, 255, 0.02) 0%, transparent 50%)" }}
      />
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="rounded-xl p-6 relative overflow-hidden flex-shrink-0"
        style={{
          background: "rgba(22, 27, 34, 0.8)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <div className="flex items-start justify-between mb-3 relative z-10">
          <div>
            <h3 className="text-lg mb-1" style={{ color: "#e6edf3" }}>{patient.name}</h3>
            <p className="text-sm" style={{ fontFamily: "'Space Mono', monospace", color: "#8b949e" }}>MRN-{patient.mrn}</p>
            {dashboardData?.patient && (
              <div className="mt-2 space-y-1 text-xs" style={{ color: "#8b949e" }}>
                {dashboardData.patient.dob && <p>DOB: {dashboardData.patient.dob}</p>}
                {dashboardData.patient.sex && <p>Sex: {dashboardData.patient.sex}</p>}
                {dashboardData.patient.language_pref && <p>Language: {dashboardData.patient.language_pref}</p>}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className="w-2.5 h-2.5 rounded-full relative"
              style={{ background: "#3fb950" }}
            >
              {[0, 1].map((i) => (
                <motion.div
                  key={i}
                  className="absolute inset-0 rounded-full"
                  style={{ border: "2px solid #3fb950" }}
                  animate={{ scale: [1, 2.5, 2.5], opacity: [0.8, 0, 0] }}
                  transition={{ duration: 2, delay: i * 1, repeat: Infinity, ease: "easeOut" }}
                />
              ))}
            </motion.div>
            <span className="text-xs" style={{ color: "#8b949e" }}>{patient.status}</span>
          </div>
        </div>
      </motion.div>
      <Vitals {...vitalsData} onCitationClick={onCitationClick} />
      <Treatment {...treatmentData} onCitationClick={onCitationClick} />
      <RecoveryPlan {...recoveryPlanData} onCitationClick={onCitationClick} />
    </div>
  );
}
