"use client";

import { motion } from "framer-motion";
import { ReasoningStep } from "@/types";

interface ReasoningStepsProps {
  steps: ReasoningStep[];
}

export default function ReasoningSteps({ steps }: ReasoningStepsProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">What I Checked</h2>
      
      <div className="space-y-3">
        {steps.map((step, index) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-start gap-3"
          >
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-xs font-medium text-blue-600">{index + 1}</span>
            </div>
            <p className="text-sm text-gray-700 pt-0.5">{step.content}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
