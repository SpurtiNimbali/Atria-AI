"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Citation, Document } from "@/types";

interface PatientContextProps {
  patientId: string;
  citations: Citation[];
  documents: Document[];
  onCitationClick: (citation: Citation) => void;
}

export default function PatientContext({ patientId, citations, documents, onCitationClick }: PatientContextProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    // Disabled for now - using static synthetic data
    alert("Patient data is already loaded (10 chunks for synthetic-001). Just send a query!");
  };

  // Group citations by resource type
  const citationsByType = citations.reduce((acc, citation) => {
    if (!acc[citation.resource_type]) {
      acc[citation.resource_type] = [];
    }
    acc[citation.resource_type].push(citation);
    return acc;
  }, {} as Record<string, Citation[]>);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-[calc(100vh-200px)] overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Patient Context</h2>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400"
        >
          {isRefreshing ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          )}
        </button>
      </div>

      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm font-medium text-gray-700">Patient ID</p>
        <p className="text-lg font-mono text-gray-900">{patientId}</p>
      </div>

      {Object.keys(citationsByType).length === 0 ? (
        <div className="text-center py-8">
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-sm text-gray-500">No context loaded yet</p>
          <p className="text-xs text-gray-400 mt-1">Ask a question to see relevant records</p>
        </div>
      ) : (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Retrieved Records
          </h3>

          {Object.entries(citationsByType).map(([resourceType, typeCitations]) => (
            <motion.div
              key={resourceType}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border border-gray-200 rounded-lg p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-900">{resourceType}</h4>
                <span className="text-xs text-gray-500">{typeCitations.length}</span>
              </div>

              <div className="space-y-2">
                {typeCitations.slice(0, 3).map((citation) => (
                  <div
                    key={citation.id}
                    className="text-xs text-gray-600 bg-gray-50 p-2 rounded"
                  >
                    <p className="line-clamp-2">{citation.snippet}</p>
                    <p className="text-gray-400 mt-1">
                      {new Date(citation.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Documents Retrieved Section */}
      {documents.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
            📄 Documents Retrieved ({documents.length})
          </h3>
          
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {documents.map((doc) => (
              <motion.div
                key={doc.doc_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="border border-blue-200 rounded-lg p-3 bg-blue-50 hover:bg-blue-100 transition-colors cursor-pointer"
                onClick={() => {
                  // Convert document to citation format for modal
                  onCitationClick({
                    id: doc.doc_id,
                    resource_type: doc.resource_type,
                    resource_id: doc.resource_id,
                    snippet: doc.text,
                    timestamp: doc.timestamp,
                    score: doc.score
                  });
                }}
              >
                <div className="flex items-start justify-between mb-1">
                  <span className="text-xs font-medium text-blue-800 bg-blue-200 px-2 py-1 rounded">
                    {doc.resource_type}
                  </span>
                  <span className="text-xs text-blue-600">
                    Score: {doc.score.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-gray-700 line-clamp-3 mt-2">
                  {doc.text}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Key Facts Section */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
          Quick Facts
        </h3>
        
        <div className="space-y-2">
          {citationsByType.AllergyIntolerance && (
            <div className="flex items-start gap-2 text-sm">
              <span className="text-red-500">⚠️</span>
              <div>
                <p className="font-medium text-gray-900">Allergies</p>
                <p className="text-gray-600">{citationsByType.AllergyIntolerance.length} documented</p>
              </div>
            </div>
          )}

          {citationsByType.MedicationRequest && (
            <div className="flex items-start gap-2 text-sm">
              <span className="text-blue-500">💊</span>
              <div>
                <p className="font-medium text-gray-900">Medications</p>
                <p className="text-gray-600">{citationsByType.MedicationRequest.length} active</p>
              </div>
            </div>
          )}

          {citationsByType.Condition && (
            <div className="flex items-start gap-2 text-sm">
              <span className="text-orange-500">🏥</span>
              <div>
                <p className="font-medium text-gray-900">Conditions</p>
                <p className="text-gray-600">{citationsByType.Condition.length} documented</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
