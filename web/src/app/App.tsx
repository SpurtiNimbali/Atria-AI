import { useState, useEffect, useRef, useCallback } from "react";
import { PatientContext } from "./components/LeftPanel";
import { VoiceInterface, ConversationItem } from "./components/CenterPanel";
import { FormattedResponse } from "./components/FormattedResponse";
import { Timeline, TimelineCommit } from "./components/RightPanel";
import {
  CitationDrawer,
  DecisionTreeModal,
  ReasoningCompleteNotification,
  type Citation,
  type Outcome,
} from "./components/Overlays";

type VoiceState = "idle" | "listening" | "thinking" | "reasoning" | "speaking";

// Split deploy: set VITE_BACKEND_URL to the API origin only, e.g. https://xxx.up.railway.app
// (not the Vercel UI URL). A common mistake is pasting both → breaks fetch + WebSocket.
function normalizeSplitDeployBackendUrl(raw: string): string {
  let s = raw.trim().replace(/\/$/, "");
  if (!s) return s;
  if (!/^https?:\/\//i.test(s)) s = `https://${s}`;
  try {
    const u = new URL(s);
    if (u.pathname && u.pathname !== "/") {
      const first = u.pathname.replace(/^\//, "").split("/")[0] || "";
      if (
        first.includes(".") &&
        (first.endsWith(".up.railway.app") || first.includes("railway.app") || /^api[-.]/.test(first))
      ) {
        return `${u.protocol}//${first}`;
      }
    }
    return `${u.protocol}//${u.host}`;
  } catch {
    return raw.replace(/\/$/, "");
  }
}

// Split deploy: set VITE_BACKEND_URL. Same-origin (Docker nginx / TLS reverse proxy): leave unset in prod build.
const getBackendUrl = () => {
  const v = import.meta.env.VITE_BACKEND_URL as string | undefined;
  if (typeof v === "string" && v.trim().length > 0) {
    return normalizeSplitDeployBackendUrl(v);
  }
  if (import.meta.env.DEV) {
    return "http://localhost:8000";
  }
  return "";
};

const getBackendWsUrl = () => {
  const v = import.meta.env.VITE_BACKEND_URL as string | undefined;
  if (typeof v === "string" && v.trim().length > 0) {
    const httpBase = normalizeSplitDeployBackendUrl(v);
    return httpBase.replace(/^https:\/\//i, "wss://").replace(/^http:\/\//i, "ws://");
  }
  if (import.meta.env.DEV) {
    return "ws://localhost:8000";
  }
  const proto = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = typeof window !== "undefined" ? window.location.host : "";
  return `${proto}//${host}`;
};

export default function App() {
  const [patientId, setPatientId] = useState("synthetic-001");
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [wsConnected, setWsConnected] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState<any[]>([]);
  const [reasoningSummary, setReasoningSummary] = useState<string>("");
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState("");
  const [conversationHistory, setConversationHistory] = useState<ConversationItem[]>([]);
  const [commits, setCommits] = useState<TimelineCommit[]>([
    { id: "3", time: "10:15 AM", title: "Initial assessment", summary: "Patient stable, monitoring vitals", isBranch: false },
    { id: "2", time: "11:30 AM", title: "Blood transfusion started", summary: "Second unit initiated", isBranch: false },
    { id: "1", time: "12:45 PM", title: "Blood work completed", summary: "Hemoglobin improved to 9.1", isBranch: false },
  ]);
  const [citations, setCitations] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [citationDrawerOpen, setCitationDrawerOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [toolResults, setToolResults] = useState<any[]>([]); // Track tool results for visualizations
  const [reasoningCycles, setReasoningCycles] = useState<Array<{ query: string; tools: string[]; result: any }>>([]); // Track iterative cycles
  const [dashboardData, setDashboardData] = useState<any>(null); // Dashboard data from Elasticsearch

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const stepCounterRef = useRef(0);
  const wsConnectedRef = useRef(false);
  const transcriptRef = useRef<string>("");
  const voiceStateRef = useRef<VoiceState>("idle");
  const queryInProgressRef = useRef(false); // Prevent duplicate query sends

  const rawPatient = dashboardData?.patient;
  const hasPatientName =
    rawPatient &&
    typeof rawPatient === "object" &&
    typeof (rawPatient as { name?: unknown }).name === "string" &&
    (rawPatient as { name: string }).name.trim().length > 0;
  const patientData = hasPatientName
    ? {
        ...(rawPatient as object),
        mrn: (rawPatient as { mrn?: string }).mrn || patientId,
        status: (rawPatient as { status?: string }).status || "Stable",
      }
    : {
        // Deliberate placeholder: when real ES-backed `patient.name` appears, ingest is working.
        name: "Emily Marie Johnson",
        mrn: patientId,
        status: "Stable",
      };

  // Fetch dashboard data on mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch(`${getBackendUrl()}/patients/${patientId}/dashboard`);
        if (!response.ok) {
          const snippet = (await response.text()).slice(0, 400);
          console.warn(
            "Dashboard API not OK — Elasticsearch ingest may be missing or API error. Status:",
            response.status,
            snippet || ""
          );
          return;
        }
        const data = await response.json();
        if (data?.patient && typeof data.patient === "object" && !Object.keys(data.patient).length) {
          console.warn(
            "Dashboard returned empty patient — index may be empty. Set Railway AUTO_INGEST_SYNTHETIC_DEMO=1 or POST /patients/synthetic-001/refresh on the API."
          );
        }
        setDashboardData(data);

        if (data.patient) {
          setPatientId(data.patient.mrn || patientId);
        }

        if (data.timeline && data.timeline.length > 0) {
          const timelineCommits = data.timeline.slice(0, 10).map((event: any, idx: number) => {
            const date = new Date(event.timestamp);
            const timeString = date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
            return {
              id: `timeline-${idx}`,
              time: timeString,
              title: event.title || event.action,
              summary: event.summary || "",
              isBranch: false,
            };
          });
          setCommits(timelineCommits);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    };
    
    fetchDashboardData();
  }, [patientId]);

  // Define sendQuery BEFORE it's used in useEffect - use ref to avoid circular dependency
  const sendQuery = useCallback((query: string) => {
    if (!query.trim() || !wsConnectedRef.current) {
      console.warn("Cannot send query:", { query: query.trim(), connected: wsConnectedRef.current });
      return;
    }

    // Prevent duplicate queries
    if (queryInProgressRef.current) {
      console.log("⏳ Query already in progress, ignoring duplicate");
      return;
    }

    // ALWAYS stop audio when a new query comes in
    if (synthRef.current) {
      synthRef.current.cancel();
    }

    console.log("Sending query:", query);
    queryInProgressRef.current = true;
    setResponse("");
    setReasoningSteps([]);
    setReasoningSummary("");
    setDocuments([]);
    setToolResults([]); // Clear tool results for new query
    setReasoningCycles([]); // Clear reasoning cycles for new query
    setVoiceState("thinking");
    voiceStateRef.current = "thinking";

    wsRef.current?.send(
      JSON.stringify({
        type: "voice_transcript",
        patient_id: patientId,
        transcript: query.trim(),
      })
    );
  }, [patientId]);

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

          // Update transcript ref immediately
          if (final) {
            const newTranscript = final.trim();
            transcriptRef.current = newTranscript;
            setTranscript(newTranscript);
            setVoiceState("thinking");
            voiceStateRef.current = "thinking";
          } else if (interim) {
            // Show interim results
            const currentTranscript = transcriptRef.current || "";
            const displayTranscript = currentTranscript + " " + interim;
            setTranscript(displayTranscript.trim());
          }
        };

        recognitionRef.current.onend = () => {
          // Use ref to get latest transcript value (fixes stale closure bug)
          const currentTranscript = transcriptRef.current;
          console.log("Recognition ended, transcript:", currentTranscript);
          
          if (currentTranscript.trim()) {
            // Don't set to idle here - sendQuery will set to thinking
            sendQuery(currentTranscript);
          } else {
            // No transcript captured, go back to idle
            setVoiceState("idle");
            voiceStateRef.current = "idle";
          }
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error("Speech recognition error:", event.error);
          setVoiceState("idle");
          voiceStateRef.current = "idle";
        };
      }

      // Initialize speech synthesis
      synthRef.current = window.speechSynthesis;
    }
  }, [sendQuery]);

  // Update refs when state changes
  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let pingInterval: NodeJS.Timeout | null = null;

    const connect = () => {
      try {
        ws = new WebSocket(`${getBackendWsUrl()}/ws`);

        ws.onopen = () => {
          console.log("✅ WebSocket connected");
          wsConnectedRef.current = true;
          setWsConnected(true);
          
          // Send ping every 30 seconds to keep connection alive
          pingInterval = setInterval(() => {
            if (ws?.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "ping" }));
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case "reasoning_step":
              if (message.content) {
                stepCounterRef.current += 1;
                
                setReasoningSteps((prev) => {
                  // Get tool info from message or most recent tool_start
                  const toolInfo = message.tool || prev[prev.length - 1]?.tool || "";
                  const params = message.params || prev[prev.length - 1]?.params || {};
                  
                  // Extract query from params
                  const query = params.query || params.proposed_drug || params.lab_type || params.intervention || "";
                  
                  return [
                    ...prev,
                    {
                      id: `step-${stepCounterRef.current}-${Date.now()}`,
                      emoji: message.emoji || "⚙️",
                      step: message.step || "Processing",
                      content: message.content,
                      timestamp: new Date().toISOString(),
                      tool: toolInfo,
                      params: params,
                      query: query,
                    },
                  ];
                });
                // Update reasoning summary for AgenticReasoning component
                const newSummary = `${message.step || "Processing"}: ${message.content}`;
                setReasoningSummary((prev) => 
                  prev ? `${prev}\n${newSummary}` : newSummary
                );
                // ALWAYS show reasoning when steps come in (user NEEDS to see this)
                // Force transition to reasoning state regardless of current state
                setVoiceState("reasoning");
                voiceStateRef.current = "reasoning";
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
                // Keep in reasoning state to show thinking process
                // Don't transition to speaking yet - user needs to see the tools being called
              }
              break;

            case "response_complete":
              if (message.full_text) {
                setResponse(message.full_text);
                
                // Query is complete - allow next query
                queryInProgressRef.current = false;
                
                // Add to conversation history immediately (only once per query)
                const now = new Date();
                const timeString = now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
                const reasoningText = reasoningSteps.map((s) => s.content).join(" ");
                
                setConversationHistory((prev) => [
                  ...prev,
                  {
                    id: `conv-${Date.now()}`,
                    timestamp: timeString,
                    question: transcriptRef.current,
                    reasoning: reasoningText,
                    answer: message.full_text,
                  },
                ]);
                
                // Add ONE timeline commit for this question session
                setCommits((prev) => [
                  {
                    id: Date.now().toString(),
                    time: timeString,
                    title: `Question: ${transcriptRef.current.substring(0, 40)}${transcriptRef.current.length > 40 ? '...' : ''}`,
                    summary: `Asked about patient care - ${reasoningSteps.length} tools used`,
                    isBranch: false,
                  },
                  ...prev,
                ]);
                
                // Show completion notification
                setShowNotification(true);
                setNotificationMessage("Analysis complete");
                setTimeout(() => setShowNotification(false), 2000);
                
                // Transition to speaking state to show the response
                setVoiceState("speaking");
                voiceStateRef.current = "speaking";
                
                // Clear transcript but keep response for display
                setTranscript("");
                transcriptRef.current = "";
                
                // Speak the response aloud using ElevenLabs TTS
                if (typeof window !== "undefined" && message.full_text) {
                  // Cancel any ongoing speech from previous query
                  if (synthRef.current) {
                    synthRef.current.cancel();
                  }
                  
                  console.log("🔊 Calling ElevenLabs TTS:", message.full_text);
                  
                  // Call backend TTS endpoint
                  fetch(`${getBackendUrl()}/tts`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text: message.full_text })
                  })
                    .then(response => {
                      if (!response.ok) {
                        throw new Error(`TTS API error: ${response.status}`);
                      }
                      return response.blob();
                    })
                    .then(blob => {
                      const audioUrl = URL.createObjectURL(blob);
                      const audio = new Audio(audioUrl);
                      
                      // When audio starts playing
                      audio.onplay = () => {
                        console.log("🎤 Speech started");
                        setVoiceState("speaking");
                        voiceStateRef.current = "speaking";
                      };
                      
                      // When audio ends, transition back to idle
                      audio.onended = () => {
                        console.log("✅ Speech finished - ready for next query");
                        URL.revokeObjectURL(audioUrl); // Clean up
                        setVoiceState("idle");
                        voiceStateRef.current = "idle";
                        setResponse("");
                        setReasoningSteps([]);
                        setReasoningSummary("");
                      };
                      
                      audio.onerror = (error) => {
                        console.error("❌ Audio playback error:", error);
                        URL.revokeObjectURL(audioUrl); // Clean up
                        // Still transition to idle on error so user can ask another question
                        setVoiceState("idle");
                        voiceStateRef.current = "idle";
                        setResponse("");
                        setReasoningSteps([]);
                        setReasoningSummary("");
                      };
                      
                      // Start playing
                      audio.play();
                    })
                    .catch(error => {
                      console.error("❌ TTS error:", error);
                      // Transition to idle on error
                      setVoiceState("idle");
                      voiceStateRef.current = "idle";
                      setResponse("");
                      setReasoningSteps([]);
                      setReasoningSummary("");
                    });
                }
              }
              break;

            case "timeline_commit":
              // Only add timeline commits for procedures or healthcare plans (not regular queries)
              if (message.title && message.summary) {
                const title = message.title.toLowerCase();
                const summary = message.summary.toLowerCase();
                
                // Check if this is about a procedure or healthcare plan
                const isProcedureOrPlan = 
                  title.includes("procedure") ||
                  title.includes("plan") ||
                  title.includes("treatment") ||
                  title.includes("surgery") ||
                  title.includes("therapy") ||
                  title.includes("intervention") ||
                  summary.includes("procedure") ||
                  summary.includes("care plan") ||
                  summary.includes("treatment plan") ||
                  summary.includes("discharge plan");
                
                if (isProcedureOrPlan) {
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
              }
              break;

            case "citations":
              if (message.citations) {
                setCitations(message.citations);
              }
              break;

            case "tool_start":
              stepCounterRef.current += 1;
              const params = message.params || {};
              // Extract query from params for display
              const query = params.query || params.proposed_drug || params.lab_type || params.intervention || params.primary_entity || params.condition || "";
              const toolStartStep = {
                id: `tool-${stepCounterRef.current}-${Date.now()}`,
                emoji: "⚙️",
                step: `Using: ${message.tool}`,
                content: `Calling ${message.tool}...`,
                timestamp: new Date().toISOString(),
                tool: message.tool,
                params: params,
                query: query, // Add query for display
              };
              setReasoningSteps((prev) => [...prev, toolStartStep]);
              // Update reasoning summary
              const toolStartSummary = `${toolStartStep.step}: ${toolStartStep.content}`;
              setReasoningSummary((prev) => 
                prev ? `${prev}\n${toolStartSummary}` : toolStartSummary
              );
              // ALWAYS show reasoning when tools are called (user NEEDS to see this)
              // Force transition to reasoning state regardless of current state
              setVoiceState("reasoning");
              voiceStateRef.current = "reasoning";
              break;

            case "tool_complete":
              // Track tool results for visualizations and iterative display
              if (message.tool && message.result) {
                setToolResults((prev) => [
                  ...prev,
                  {
                    tool: message.tool,
                    result: message.result,
                    timestamp: new Date().toISOString(),
                  },
                ]);
                
                // Update reasoning cycles - track query → tool → result pattern
                setReasoningCycles((prev) => {
                  const lastCycle = prev[prev.length - 1];
                  if (lastCycle && lastCycle.tools.includes(message.tool)) {
                    // Update existing cycle
                    return prev.map((cycle, idx) =>
                      idx === prev.length - 1
                        ? { ...cycle, result: { ...cycle.result, [message.tool]: message.result } }
                        : cycle
                    );
                  } else {
                    // New tool in current cycle or new cycle
                    if (lastCycle && !lastCycle.result) {
                      // Add to current cycle
                      return prev.map((cycle, idx) =>
                        idx === prev.length - 1
                          ? {
                              ...cycle,
                              tools: [...cycle.tools, message.tool],
                              result: { ...cycle.result, [message.tool]: message.result },
                            }
                          : cycle
                      );
                    } else {
                      // Start new cycle
                      return [
                        ...prev,
                        {
                          query: transcriptRef.current || "Current query",
                          tools: [message.tool],
                          result: { [message.tool]: message.result },
                        },
                      ];
                    }
                  }
                });
              }
              break;

            case "error":
              console.error("Error from server:", message.message);
              // Reset query flag on error to allow retry
              queryInProgressRef.current = false;
              setVoiceState("idle");
              voiceStateRef.current = "idle";
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
          wsConnectedRef.current = false;
          setWsConnected(false);
          setVoiceState("idle");
          voiceStateRef.current = "idle";
          
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
          wsConnectedRef.current = false;
          setWsConnected(false);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
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

  const handleWaveformClick = () => {
    if (!wsConnectedRef.current) {
      alert("Not connected to backend. Please ensure the gateway is running.");
      return;
    }

    // ALWAYS stop audio ONLY when user clicks record (not when query is sent)
    if (synthRef.current && voiceState === "idle") {
      synthRef.current.cancel(); // Stop speech synthesis when user clicks record
    }

    if (voiceState === "idle") {
      // Clear all state for new query
      setTranscript("");
      transcriptRef.current = "";
      setResponse("");
      setReasoningSteps([]);
      setReasoningSummary("");
      setDocuments([]);
      setCitations([]);
      queryInProgressRef.current = false; // Reset flag for new query
      setVoiceState("listening");
      voiceStateRef.current = "listening";
      
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.error("Failed to start recognition:", e);
          // Fallback to text input
          const text = prompt("Enter your query:");
          if (text) {
            transcriptRef.current = text;
            setTranscript(text);
            sendQuery(text);
          } else {
            setVoiceState("idle");
            voiceStateRef.current = "idle";
          }
        }
      } else {
        // Fallback to text input
        const text = prompt("Enter your query:");
        if (text) {
          transcriptRef.current = text;
          setTranscript(text);
          sendQuery(text);
        } else {
          setVoiceState("idle");
          voiceStateRef.current = "idle";
        }
      }
    } else if (voiceState === "listening") {
      // Stop listening if currently listening
      recognitionRef.current?.stop();
      setVoiceState("idle");
      voiceStateRef.current = "idle";
    } else if (voiceState === "thinking" || voiceState === "reasoning") {
      // Don't allow interruption during processing - system is working on current query
      // User needs to wait for current query to complete
      console.log("⏳ Please wait for current query to complete");
      return;
    } else if (voiceState === "speaking") {
      // User wants to interrupt the speaking and ask a follow-up
      // Stop speech and start listening for new question
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      setResponse("");
      setReasoningSteps([]);
      setReasoningSummary("");
      queryInProgressRef.current = false; // Reset flag for new query
      setVoiceState("listening");
      voiceStateRef.current = "listening";
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.error("Failed to start recognition:", e);
        }
      }
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

  // Removed duplicate conversation history logic - now handled in response_complete case

  const decisionOutcomes: Outcome[] = [
    {
      id: "outcome-1",
      name: "Standard Dosing Protocol",
      description: "Begin with manufacturer-recommended dosing (500mg BID). Most conservative approach with established safety profile.",
      risks: ["Slower symptom resolution", "May require dosage adjustment", "Extended monitoring period"],
      confidence: 87,
    },
  ];

  const handleOutcomeClick = (outcomeId: string) => {
    console.log("Outcome clicked:", outcomeId);
  };

  return (
    <div className="w-screen h-screen flex overflow-hidden" style={{ background: "#0d1117", fontFamily: "'Crimson Pro', serif" }}>
      <PatientContext patient={patientData} dashboardData={dashboardData} onCitationClick={handleCitationClick} />
      <VoiceInterface
        state={voiceState}
        transcript={transcript}
        reasoningSummary={reasoningSummary}
        response={response}
        onWaveformClick={handleWaveformClick}
        conversationHistory={conversationItems}
        reasoningSteps={reasoningSteps}
      />
      <Timeline commits={timelineCommits} />
      <ReasoningCompleteNotification isVisible={showNotification} message={notificationMessage} />
      <DecisionTreeModal
        isOpen={false}
        branchName="medication-b-pathway"
        outcomes={decisionOutcomes}
        onClose={() => {}}
        onOutcomeClick={handleOutcomeClick}
      />
      <CitationDrawer isOpen={citationDrawerOpen} citation={selectedCitation} onClose={() => setCitationDrawerOpen(false)} />
    </div>
  );
}
