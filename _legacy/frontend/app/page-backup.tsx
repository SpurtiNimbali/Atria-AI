"use client";

// Minimal working version to test
export default function Home() {
  return (
    <div style={{ 
      width: "100vw", 
      height: "100vh", 
      background: "#0d1117", 
      color: "#e6edf3",
      padding: "20px",
      fontFamily: "'Crimson Pro', serif"
    }}>
      <h1 style={{ color: "#58a6ff" }}>EHR Copilot</h1>
      <p>Testing basic render...</p>
      <p style={{ color: "#8b949e" }}>If you see this, React is working!</p>
    </div>
  );
}
