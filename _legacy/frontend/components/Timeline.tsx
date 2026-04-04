"use client";

import { motion } from "framer-motion";
import { TimelineCommit, Citation } from "@/types";

interface TimelineProps {
  commits: TimelineCommit[];
  onCitationClick: (citation: Citation) => void;
}

export default function Timeline({ commits, onCitationClick }: TimelineProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-[calc(100vh-200px)] overflow-y-auto">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        Timeline
      </h2>

      {commits.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="w-12 h-12 text-gray-300 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <p className="text-sm text-gray-500">No interactions yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {commits.map((commit, index) => (
            <motion.div
              key={commit.id}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="border-l-2 border-blue-500 pl-4 pb-4"
            >
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-blue-500 -ml-[25px] mt-1.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 text-sm">{commit.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(commit.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>

              <p className="text-sm text-gray-700 mb-2">{commit.summary}</p>

              {commit.citations.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {commit.citations.map((citationId) => (
                    <span
                      key={citationId}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 cursor-pointer hover:bg-blue-200"
                    >
                      [{citationId}]
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
