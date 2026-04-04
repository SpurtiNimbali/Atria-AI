"use client";

import { useState } from "react";

export default function DebugPage() {
  const [error, setError] = useState<string | null>(null);

  return (
    <div style={{ padding: "20px", background: "#0d1117", color: "#e6edf3", minHeight: "100vh" }}>
      <h1>Debug Page</h1>
      <p>If you see this, React is working!</p>
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      <button 
        onClick={() => {
          try {
            // Test imports
            import("@/components/figma/LeftPanel").then(() => {
              console.log("✅ LeftPanel import works");
            }).catch((e) => {
              console.error("❌ LeftPanel import failed:", e);
              setError(`LeftPanel: ${e.message}`);
            });
            
            import("@/components/figma/CenterPanelIntegrated").then(() => {
              console.log("✅ CenterPanelIntegrated import works");
            }).catch((e) => {
              console.error("❌ CenterPanelIntegrated import failed:", e);
              setError(`CenterPanelIntegrated: ${e.message}`);
            });
            
            import("@/components/figma/RightPanel").then(() => {
              console.log("✅ RightPanel import works");
            }).catch((e) => {
              console.error("❌ RightPanel import failed:", e);
              setError(`RightPanel: ${e.message}`);
            });
            
            import("@/components/figma/Overlays").then(() => {
              console.log("✅ Overlays import works");
            }).catch((e) => {
              console.error("❌ Overlays import failed:", e);
              setError(`Overlays: ${e.message}`);
            });
          } catch (e: any) {
            setError(`Import test failed: ${e.message}`);
          }
        }}
        style={{ padding: "10px", background: "#58a6ff", color: "#0d1117", border: "none", borderRadius: "4px", cursor: "pointer" }}
      >
        Test Imports
      </button>
    </div>
  );
}
