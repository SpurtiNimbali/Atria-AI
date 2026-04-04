import { motion } from "motion/react";
import { CitationChip } from "./CitationChip";

interface ReasoningCardProps {
  agent: string;
  summary: string;
  confidence: number;
  delay: number;
  citations?: Array<{ label: string; type: "EHR" | "Guideline" | "Study" }>;
  onCitationClick: (citationId: string) => void;
}

export function ReasoningCard({ agent, summary, confidence, delay, citations = [], onCitationClick }: ReasoningCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ 
        duration: 0.4, 
        delay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      className="rounded-lg p-5 relative overflow-hidden"
      style={{
        background: "rgba(22, 27, 34, 0.8)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(88, 166, 255, 0.15)",
        fontFamily: "'Crimson Pro', serif",
        maxWidth: "560px",
        width: "100%",
      }}
    >
      <div className="relative z-10">
        {/* Agent Label */}
        <motion.div
          className="mb-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.1 }}
        >
          <div
            className="inline-block px-2.5 py-1 rounded text-xs"
            style={{
              background: "rgba(88, 166, 255, 0.1)",
              border: "1px solid rgba(88, 166, 255, 0.2)",
              color: "#58a6ff",
              fontFamily: "'Space Mono', monospace",
              letterSpacing: "0.3px",
            }}
          >
            {agent}
          </div>
        </motion.div>

        {/* Summary */}
        <motion.p 
          className="text-base leading-relaxed mb-4"
          style={{ color: "#e6edf3", fontWeight: 400 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.15 }}
        >
          {summary}
        </motion.p>

        {/* Confidence */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <span 
              className="text-xs"
              style={{ 
                fontFamily: "'Space Mono', monospace",
                color: "#8b949e",
                letterSpacing: "0.3px"
              }}
            >
              CONFIDENCE
            </span>
            <motion.span
              className="text-xs"
              style={{ 
                fontFamily: "'Space Mono', monospace",
                color: "#58a6ff",
                fontWeight: 600
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: delay + 0.2 }}
            >
              {confidence}%
            </motion.span>
          </div>

          {/* Progress bar */}
          <div 
            className="w-full h-1 rounded-full overflow-hidden"
            style={{ 
              background: "rgba(88, 166, 255, 0.1)",
            }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{ 
                background: "#58a6ff",
              }}
              initial={{ width: 0 }}
              animate={{ width: `${confidence}%` }}
              transition={{ 
                duration: 0.8, 
                delay: delay + 0.25,
                ease: [0.25, 0.1, 0.25, 1]
              }}
            />
          </div>
        </div>

        {/* Citations */}
        {citations.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: delay + 0.3 }}
            className="flex flex-wrap gap-2"
          >
            {citations.map((citation, index) => (
              <CitationChip
                key={index}
                label={citation.label}
                type={citation.type}
                onClick={() => onCitationClick(`${agent}-${index}`)}
              />
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}