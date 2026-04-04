"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { VoiceInterface, VoiceState, ConversationItem } from "@/components/figma/CenterPanelIntegrated";
import { PatientContext } from "@/components/figma/LeftPanel";
import { Timeline, TimelineCommit } from "@/components/figma/RightPanel";
import {
  CitationDrawer,
  ReasoningCompleteNotification,
  type Citation,
} from "@/components/figma/Overlays";
import { TimelineCommit as TimelineCommitType, Citation as CitationType, ReasoningStep, Document, WSMessage } from "@/types";

export default function Home() {
  const [patientId, setPatientId] = useState("synthetic-001");
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [wsConnected, setWsConnected] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState("");
  const [conversationHistory, setConversationHistory] = useState<ConversationItem[]>([]);
  const [commits, setCommits] = useState<TimelineCommit[]>([]);
  const [citations, setCitations] = useState<CitationType[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [citationDrawerOpen, setCitationDrawerOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const stepCounterRef = useRef(0);

  const patientData = { name: "Emily Marie Johnson", mrn: patientId, status: "Stable" };

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = "en-US";

        recognitionRef.current.onresult = (event: any) => {
          let interim = "";
          let final = "";

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptText = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              final += transcriptText;
            } else {
              interim += transcriptText;
            }
          }

          if (final) {
            setTranscript(final);
            setVoiceState("thinking");
          }
        };

        recognitionRef.current.onend = () => {
          if (transcript.trim()) {
            sendQuery(transcript);
          }
          setVoiceState("idle");
        };
      }
    }
  }, [transcript]);

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let pingInterval: NodeJS.Timeout | null = null;

    const connect = () => {
      try {
        ws = new WebSocket("ws://localhost:8000/ws");

        ws.onopen = () => {
          console.log("✅ WebSocket connected");
          setWsConnected(true);
          
          // Send ping every 30 seconds to keep connection alive
          pingInterval = setInterval(() => {
            if (ws?.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "ping" }));
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
      const message: WSMessage = JSON.parse(event.data);

      switch (message.type) {
        case "reasoning_step":
          if (message.content) {
            stepCounterRef.current += 1;
            setReasoningSteps((prev) => [
              ...prev,
              {
                id: `step-${stepCounterRef.current}-${Date.now()}`,
                emoji: message.emoji,
                step: message.step,
                content: message.content,
                timestamp: new Date().toISOString(),
              },
            ]);
            if (voiceState === "thinking") {
              setVoiceState("reasoning");
            }
          }
          break;

        case "document_retrieved":
          if (message.doc_id && message.resource_type && message.text) {
            setDocuments((prev) => [
              ...prev,
              {
                doc_id: message.doc_id,
                resource_type: message.resource_type,
                resource_id: message.resource_id || "",
                text: message.text,
                score: message.score || 0,
                timestamp: message.timestamp || new Date().toISOString(),
              },
            ]);
            // Convert to citation
            setCitations((prev) => [
              ...prev,
              {
                id: message.doc_id,
                resource_type: message.resource_type,
                resource_id: message.resource_id || "",
                snippet: message.text.substring(0, 200),
                timestamp: message.timestamp || new Date().toISOString(),
                score: message.score || 0,
              },
            ]);
          }
          break;

        case "text_chunk":
          if (message.text) {
            setResponse((prev) => prev + message.text);
            if (voiceState === "reasoning") {
              setVoiceState("speaking");
            }
          }
          break;

        case "response_complete":
          if (message.full_text) {
            setResponse(message.full_text);
            setVoiceState("speaking");
            setShowNotification(true);
            setNotificationMessage("Analysis complete");
            setTimeout(() => setShowNotification(false), 3000);
          }
          break;

        case "timeline_commit":
          if (message.title && message.summary) {
            const now = new Date();
            const timeString = now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
            setCommits((prev) => [
              {
                id: Date.now().toString(),
                time: timeString,
                title: message.title!,
                summary: message.summary!,
                isBranch: false,
              },
              ...prev,
            ]);
          }
          break;

        case "citations":
          if (message.citations) {
            setCitations(message.citations);
          }
          break;

        case "tool_start":
          stepCounterRef.current += 1;
          setReasoningSteps((prev) => [
            ...prev,
            {
              id: `tool-${stepCounterRef.current}-${Date.now()}`,
              emoji: "⚙️",
              step: `Using: ${message.tool}`,
              content: `Calling ${message.tool}...`,
              timestamp: new Date().toISOString(),
            },
          ]);
          if (voiceState === "thinking") {
            setVoiceState("reasoning");
          }
          break;

        case "tool_complete":
          stepCounterRef.current += 1;
          setReasoningSteps((prev) => [
            ...prev,
            {
              id: `tool-complete-${stepCounterRef.current}-${Date.now()}`,
              emoji: "✅",
              step: `Completed: ${message.tool}`,
              content: `Got results from ${message.tool}`,
              timestamp: new Date().toISOString(),
            },
          ]);
          break;

        case "error":
          console.error("Error from server:", message.message);
          setVoiceState("idle");
          break;

        case "ack":
          console.log("Server acknowledged:", message.message);
          break;
        
        case "pong":
          // Keepalive response
          break;
      }
    };

    ws.onclose = (event) => {
      console.log("WebSocket disconnected", event.code, event.reason);
      setWsConnected(false);
      setVoiceState("idle");
      
      // Clear ping interval
      if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
      }
      
      // Reconnect after 3 seconds if not a normal closure
      if (event.code !== 1000) {
        reconnectTimeout = setTimeout(() => {
          console.log("🔄 Attempting to reconnect...");
          connect();
        }, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setWsConnected(false);
    };

    wsRef.current = ws;
      } catch (error) {
        console.error("Failed to create WebSocket connection:", error);
        setWsConnected(false);
      }
    };

    // Initial connection
    connect();

    return () => {
      // Cleanup
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, "Component unmounting");
      }
    };
  }, []); // Empty deps - only run once on mount

  const sendQuery = (query: string) => {
    if (!query.trim() || !wsConnected) return;

    setResponse("");
    setReasoningSteps([]);
    setDocuments([]);
    setVoiceState("thinking");

    wsRef.current?.send(
      JSON.stringify({
        type: "voice_transcript",
        patient_id: patientId,
        transcript: query.trim(),
      })
    );
  };

  const handleWaveformClick = () => {
    if (!wsConnected) {
      alert("Not connected to backend. Please ensure the gateway is running.");
      return;
    }

    if (voiceState === "idle") {
      setTranscript("");
      setResponse("");
      setReasoningSteps([]);
      setVoiceState("listening");
      
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.error("Failed to start recognition:", e);
          // Fallback to text input
          const text = prompt("Enter your query:");
          if (text) {
            setTranscript(text);
            sendQuery(text);
          } else {
            setVoiceState("idle");
          }
        }
      } else {
        // Fallback to text input
        const text = prompt("Enter your query:");
        if (text) {
          setTranscript(text);
          sendQuery(text);
        } else {
          setVoiceState("idle");
        }
      }
    } else if (voiceState === "listening") {
      recognitionRef.current?.stop();
      setVoiceState("idle");
    }
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations.find((c) => c.id.toString() === citationId);
    if (citation) {
      setSelectedCitation({
        id: citationId,
        name: `${citation.resource_type} - ${citation.resource_id}`,
        type: citation.resource_type.includes("Guideline") ? "Guideline" : citation.resource_type.includes("Study") ? "Study" : "EHR",
        excerpt: citation.snippet,
      });
      setCitationDrawerOpen(true);
    }
  };

  // Convert commits to Timeline format
  const timelineCommits: TimelineCommit[] = commits.map((commit) => ({
    id: commit.id,
    time: commit.time,
    title: commit.title,
    summary: commit.summary,
    isBranch: commit.isBranch || false,
    branchName: commit.branchName,
  }));

  // Convert conversation history
  const conversationItems: ConversationItem[] = conversationHistory;

  // Update conversation history when response completes
  useEffect(() => {
    if (voiceState === "speaking" && response && transcript) {
      const reasoningText = reasoningSteps.map((s) => s.content).join(" ");
      const now = new Date();
      const timeString = now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
      
      setConversationHistory((prev) => [
        ...prev,
        {
          id: `conv-${Date.now()}`,
          timestamp: timeString,
          question: transcript,
          reasoning: reasoningText,
          answer: response,
        },
      ]);

      // Reset for next query
      setTimeout(() => {
        setVoiceState("idle");
        setTranscript("");
        setResponse("");
        setReasoningSteps([]);
      }, 5000);
    }
  }, [voiceState, response, transcript, reasoningSteps]);

  // Debug: Log render
  useEffect(() => {
    console.log("Page mounted", { voiceState, wsConnected, reasoningSteps: reasoningSteps.length });
  }, []);

  return (
    <div className="w-full h-screen flex overflow-hidden" style={{ background: "#0d1117", fontFamily: "'Crimson Pro', serif", minHeight: "100vh" }}>
      {/* Debug indicator - always visible */}
      <div style={{ position: "fixed", top: "10px", right: "10px", padding: "10px", background: wsConnected ? "#3fb950" : "#f85149", color: "white", zIndex: 9999, borderRadius: "4px" }}>
        {wsConnected ? "✅ Connected" : "❌ Not Connected"}
      </div>
      <PatientContext patient={patientData} onCitationClick={handleCitationClick} />
      <VoiceInterface
        state={voiceState}
        transcript={transcript}
        onWaveformClick={handleWaveformClick}
        onTextSubmit={sendQuery}
        conversationHistory={conversationItems}
        reasoningSteps={reasoningSteps}
        response={response}
        wsConnected={wsConnected}
      />
      <Timeline commits={timelineCommits} />
      <ReasoningCompleteNotification isVisible={showNotification} message={notificationMessage} />
      <CitationDrawer isOpen={citationDrawerOpen} citation={selectedCitation} onClose={() => setCitationDrawerOpen(false)} />
    </div>
  );
}
