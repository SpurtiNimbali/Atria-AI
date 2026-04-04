import { motion, AnimatePresence } from "motion/react";
import { GitBranch } from "lucide-react";

interface BranchCreationModalProps {
  isVisible: boolean;
  branchName: string;
  description: string;
  onClick: () => void;
}

export function BranchCreationModal({ isVisible, branchName, description, onClick }: BranchCreationModalProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 50, scale: 0.9 }}
          transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
          className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40"
        >
          <motion.button
            onClick={onClick}
            className="rounded-xl p-6 cursor-pointer relative overflow-hidden"
            style={{
              background: "rgba(22, 27, 34, 0.95)",
              backdropFilter: "blur(40px)",
              border: "1px solid rgba(88, 166, 255, 0.3)",
              boxShadow: "0 20px 60px rgba(0, 0, 0, 0.5), 0 0 1px rgba(88, 166, 255, 0.3) inset",
              fontFamily: "'Crimson Pro', serif",
              maxWidth: "520px",
              minWidth: "420px",
            }}
            whileHover={{
              scale: 1.03,
              borderColor: "rgba(88, 166, 255, 0.5)",
              boxShadow: "0 20px 60px rgba(88, 166, 255, 0.15), 0 0 1px rgba(88, 166, 255, 0.4) inset",
            }}
            whileTap={{ scale: 0.97 }}
          >
            {/* Animated glow border */}
            <motion.div
              className="absolute top-0 left-0 right-0 h-0.5 overflow-hidden"
              style={{
                background: "rgba(88, 166, 255, 0.1)",
              }}
            >
              <motion.div
                className="h-full"
                style={{
                  background: "linear-gradient(90deg, transparent, #58a6ff, transparent)",
                  width: "50%",
                }}
                animate={{
                  x: ["-100%", "300%"],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "linear",
                }}
              />
            </motion.div>

            {/* Header */}
            <div className="flex items-start gap-3 mb-4">
              <motion.div
                className="mt-0.5"
                animate={{
                  rotate: [0, 180, 360],
                  scale: [1, 1.1, 1],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <GitBranch className="w-5 h-5" style={{ color: "#58a6ff" }} />
              </motion.div>
              <div className="flex-1">
                <div className="flex items-baseline gap-2">
                  <h4 className="text-base" style={{ color: "#e6edf3", fontWeight: 500 }}>
                    New Branch Created
                  </h4>
                  <motion.div
                    className="w-2 h-2 rounded-full"
                    style={{ background: "#3fb950" }}
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [1, 0.6, 1],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />
                </div>
                <p 
                  className="text-xs mt-1"
                  style={{ 
                    fontFamily: "'Space Mono', monospace",
                    color: "#8b949e",
                    letterSpacing: "0.3px"
                  }}
                >
                  {branchName}
                </p>
              </div>
            </div>

            {/* Description */}
            <p className="text-sm leading-relaxed mb-4 pl-8" style={{ color: "#c9d1d9" }}>
              {description}
            </p>

            {/* Click prompt */}
            <div className="flex items-center justify-between pl-8 pt-3" style={{ borderTop: "1px solid rgba(255, 255, 255, 0.05)" }}>
              <span 
                className="text-xs"
                style={{ 
                  fontFamily: "'Space Mono', monospace",
                  color: "#58a6ff",
                  letterSpacing: "0.3px"
                }}
              >
                Click to view decision tree
              </span>
              <motion.span
                className="text-sm"
                style={{ color: "#58a6ff" }}
                animate={{ x: [0, 4, 0] }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                →
              </motion.span>
            </div>

            {/* Ambient glow */}
            <motion.div
              className="absolute -inset-4 rounded-xl"
              style={{
                background: "radial-gradient(ellipse at center, rgba(88, 166, 255, 0.15), transparent 70%)",
                filter: "blur(30px)",
                zIndex: -1,
              }}
              animate={{
                opacity: [0.3, 0.5, 0.3],
                scale: [1, 1.05, 1],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </motion.button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
