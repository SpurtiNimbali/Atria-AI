import { motion } from "motion/react";
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, BarChart3 } from "lucide-react";

interface FormattedResponseProps {
  response: string;
  reasoningSteps?: any[];
  toolResults?: any[];
}

export function FormattedResponse({ response, reasoningSteps = [], toolResults = [] }: FormattedResponseProps) {
  // Parse response into structured sections
  const parseResponse = (text: string) => {
    const sections: Array<{ type: string; content: string; data?: any }> = [];
    
    // Split by common patterns
    const lines = text.split('\n').filter(l => l.trim());
    let currentSection: { type: string; content: string; items?: string[] } | null = null;
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // Detect sections
      if (trimmed.match(/^(looking at|so looking at|okay, so|here's what|for her|based on)/i)) {
        if (currentSection) sections.push(currentSection);
        currentSection = { type: "analysis", content: trimmed, items: [] };
      } else if (trimmed.match(/^(the|in studies|usually|typically)/i) && trimmed.length > 20) {
        if (currentSection) {
          currentSection.items?.push(trimmed);
        } else {
          sections.push({ type: "fact", content: trimmed });
        }
      } else if (trimmed.startsWith('-') || trimmed.startsWith('•')) {
        if (currentSection) {
          currentSection.items = currentSection.items || [];
          currentSection.items.push(trimmed.substring(1).trim());
        }
      } else if (trimmed.length > 0) {
        if (currentSection) {
          currentSection.content += ' ' + trimmed;
        } else {
          sections.push({ type: "text", content: trimmed });
        }
      }
    }
    
    if (currentSection) sections.push(currentSection);
    
    return sections.length > 0 ? sections : [{ type: "text", content: text }];
  };

  const sections = parseResponse(response);
  
  // Extract data for visualizations from tool results
  const labData = toolResults.find(r => r.tool === "analyze_lab_trends")?.result;
  const riskData = toolResults.find(r => r.tool === "predict_treatment_risk")?.result;
  const interactionData = toolResults.find(r => r.tool === "check_drug_interactions")?.result;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl w-full space-y-6"
    >
      {/* Main Response Sections */}
      <div className="space-y-6">
        {sections.map((section, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="rounded-xl p-6"
            style={{
              background: "rgba(22, 27, 34, 0.4)",
              border: "1px solid rgba(88, 166, 255, 0.12)",
            }}
          >
            {section.type === "analysis" && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 size={16} style={{ color: "#58a6ff" }} />
                  <span className="text-xs font-semibold" style={{ color: "#58a6ff", fontFamily: "'Space Mono', monospace" }}>
                    ANALYSIS
                  </span>
                </div>
                <p className="text-base leading-relaxed mb-3" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                  {section.content}
                </p>
                {section.items && section.items.length > 0 && (
                  <ul className="space-y-2 ml-4">
                    {section.items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span style={{ color: "#58a6ff" }}>•</span>
                        <span className="text-sm leading-relaxed" style={{ color: "#c9d1d9", fontFamily: "'Crimson Pro', serif" }}>
                          {item}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            
            {section.type === "fact" && (
              <div className="flex items-start gap-3">
                <CheckCircle size={18} style={{ color: "#3fb950", marginTop: "2px" }} />
                <p className="text-base leading-relaxed" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                  {section.content}
                </p>
              </div>
            )}
            
            {section.type === "text" && (
              <p className="text-base leading-relaxed" style={{ color: "#e6edf3", fontFamily: "'Crimson Pro', serif" }}>
                {section.content}
              </p>
            )}
          </motion.div>
        ))}
      </div>

      {/* Data Visualizations */}
      {labData && labData.recent_values && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-6"
          style={{
            background: "rgba(22, 27, 34, 0.4)",
            border: "1px solid rgba(88, 166, 255, 0.12)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} style={{ color: "#3fb950" }} />
            <span className="text-xs font-semibold" style={{ color: "#3fb950", fontFamily: "'Space Mono', monospace" }}>
              LAB TREND
            </span>
          </div>
          <div className="space-y-2">
            {labData.recent_values.slice(-5).map((lab: any, i: number) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-sm" style={{ color: "#c9d1d9" }}>{lab.date || 'Recent'}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 rounded-full" style={{ background: "rgba(139, 148, 158, 0.2)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: lab.value < 10 ? "#f85149" : lab.value < 12 ? "#d29922" : "#3fb950" }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(lab.value / 15) * 100}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5 }}
                    />
                  </div>
                  <span className="text-sm font-medium w-16 text-right" style={{ color: "#e6edf3" }}>
                    {lab.value} {lab.unit || 'g/dL'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {riskData && riskData.risk_score !== undefined && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-6"
          style={{
            background: "rgba(22, 27, 34, 0.4)",
            border: "1px solid rgba(88, 166, 255, 0.12)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={16} style={{ color: riskData.risk_score > 0.7 ? "#f85149" : riskData.risk_score > 0.4 ? "#d29922" : "#3fb950" }} />
            <span className="text-xs font-semibold" style={{ color: riskData.risk_score > 0.7 ? "#f85149" : riskData.risk_score > 0.4 ? "#d29922" : "#3fb950", fontFamily: "'Space Mono', monospace" }}>
              RISK ASSESSMENT
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: "#c9d1d9" }}>Risk Score</span>
              <span className="text-lg font-semibold" style={{ color: riskData.risk_score > 0.7 ? "#f85149" : riskData.risk_score > 0.4 ? "#d29922" : "#3fb950" }}>
                {(riskData.risk_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-3 rounded-full" style={{ background: "rgba(139, 148, 158, 0.2)" }}>
              <motion.div
                className="h-full rounded-full"
                style={{ background: riskData.risk_score > 0.7 ? "#f85149" : riskData.risk_score > 0.4 ? "#d29922" : "#3fb950" }}
                initial={{ width: 0 }}
                animate={{ width: `${riskData.risk_score * 100}%` }}
                transition={{ duration: 0.8 }}
              />
            </div>
            {riskData.risk_level && (
              <p className="text-sm" style={{ color: "#8b949e" }}>{riskData.risk_level.toUpperCase()} risk</p>
            )}
          </div>
        </motion.div>
      )}

      {interactionData && interactionData.interactions && interactionData.interactions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-6"
          style={{
            background: "rgba(22, 27, 34, 0.4)",
            border: "1px solid rgba(248, 81, 73, 0.2)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={16} style={{ color: "#f85149" }} />
            <span className="text-xs font-semibold" style={{ color: "#f85149", fontFamily: "'Space Mono', monospace" }}>
              DRUG INTERACTIONS
            </span>
          </div>
          <div className="space-y-3">
            {interactionData.interactions.slice(0, 3).map((interaction: any, i: number) => (
              <div key={i} className="p-3 rounded-lg" style={{ background: "rgba(248, 81, 73, 0.1)" }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium" style={{ color: "#e6edf3" }}>
                    {interaction.drug_pair || 'Unknown'}
                  </span>
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      background: interaction.severity === "major" ? "rgba(248, 81, 73, 0.2)" : "rgba(210, 153, 34, 0.2)",
                      color: interaction.severity === "major" ? "#f85149" : "#d29922",
                    }}
                  >
                    {interaction.severity?.toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>
                {interaction.effect && (
                  <p className="text-sm" style={{ color: "#c9d1d9" }}>{interaction.effect}</p>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
