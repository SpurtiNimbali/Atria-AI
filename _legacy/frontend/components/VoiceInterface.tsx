"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TimelineCommit, Citation, ReasoningStep, WSMessage, Document } from "@/types";

interface VoiceInterfaceProps {
  patientId: string;
  onNewCommit: (commit: TimelineCommit) => void;
  onNewCitations: (citations: Citation[]) => void;
  onNewReasoningStep: (step: ReasoningStep) => void;
  onClearReasoningSteps: () => void;
  onNewDocument: (doc: Document) => void;
}

export default function VoiceInterface({
  patientId,
  onNewCommit,
  onNewCitations,
  onNewReasoningStep,
  onClearReasoningSteps,
  onNewDocument,
}: VoiceInterfaceProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [micPermission, setMicPermission] = useState<"granted" | "denied" | "prompt">("prompt");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [isSafari, setIsSafari] = useState(false);

  const recognitionRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const stepCounterRef = useRef<number>(0); // Counter for unique step IDs

  // Detect Safari
  useEffect(() => {
    if (typeof navigator !== "undefined") {
      const userAgent = navigator.userAgent.toLowerCase();
      const isSafariBrowser = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
      setIsSafari(isSafariBrowser);
      
      if (isSafariBrowser) {
        setError("⚠️ Safari doesn't support voice input reliably. Please use Chrome or Edge for voice, or use the text input below.");
      }
    }
  }, []);

  // Check microphone permission
  useEffect(() => {
    if (typeof navigator !== "undefined" && navigator.permissions) {
      navigator.permissions.query({ name: "microphone" as PermissionName }).then((result) => {
        setMicPermission(result.state as any);
        result.onchange = () => {
          setMicPermission(result.state as any);
        };
      }).catch(() => {
        // Safari doesn't support permissions API well
        console.log("Permissions API not available");
      });
    }
  }, []);

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setError("Speech recognition not supported. Please use Chrome or Edge.");
        return;
      }

      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = "en-US";

        recognitionRef.current.onstart = () => {
          console.log("✅ Speech recognition started successfully");
          setError(null);
          setStatusMessage("🎤 Microphone active - speak now!");
        };

        recognitionRef.current.onresult = (event: any) => {
          console.log("🎯 Speech detected! Results:", event.results.length);
          setStatusMessage("👂 I hear you! Keep talking...");
          
          let interim = "";
          let final = "";

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptText = event.results[i][0].transcript;
            console.log(`Result ${i}: "${transcriptText}" (final: ${event.results[i].isFinal})`);
            
            if (event.results[i].isFinal) {
              final += transcriptText;
            } else {
              interim += transcriptText;
            }
          }

          if (final) {
            console.log("✅ Final transcript:", final);
            setTranscript((prev) => (prev + " " + final).trim());
            setStatusMessage("✅ Got it! Say more or click to finish...");
          }
          setInterimTranscript(interim);
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error("Speech recognition error:", event.error);
          
          if (event.error === "not-allowed" || event.error === "permission-denied") {
            setError("Microphone permission denied. Please allow microphone access in your browser settings.");
            setMicPermission("denied");
          } else if (event.error === "no-speech") {
            setError("No speech detected. Please try speaking again.");
          } else if (event.error === "network") {
            setError("Network error. Please check your connection.");
          } else {
            setError(`Speech recognition error: ${event.error}`);
          }
          
          setIsListening(false);
        };

        recognitionRef.current.onaudiostart = () => {
          console.log("🔊 Audio capture started - mic is working!");
          setStatusMessage("🔊 Microphone is listening...");
        };

        recognitionRef.current.onaudioend = () => {
          console.log("🔇 Audio capture ended");
          setStatusMessage("Processing...");
        };

        recognitionRef.current.onsoundstart = () => {
          console.log("🎵 Sound detected!");
        };

        recognitionRef.current.onspeechstart = () => {
          console.log("🗣️ Speech detected!");
          setStatusMessage("🗣️ I hear you speaking...");
        };

        recognitionRef.current.onspeechend = () => {
          console.log("🛑 Speech ended");
        };

        recognitionRef.current.onend = () => {
          console.log("Speech recognition ended");
          setStatusMessage("");
          if (isListening) {
            try {
              console.log("🔄 Restarting recognition...");
              recognitionRef.current.start();
            } catch (e) {
              console.error("Failed to restart recognition:", e);
              setIsListening(false);
            }
          }
        };
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isListening]);

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      console.log("WebSocket connected");
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const message: WSMessage = JSON.parse(event.data);

      switch (message.type) {
        case "reasoning_step":
          if (message.content) {
            const emoji = message.emoji || "";
            const step = message.step || "";
            const displayContent = step ? `${emoji} ${step}${message.content ? ': ' + message.content : ''}` : message.content;
            stepCounterRef.current += 1; // Increment counter
            onNewReasoningStep({
              id: `step-${stepCounterRef.current}-${Date.now()}`, // Unique ID
              emoji: message.emoji,
              step: message.step,
              content: displayContent || "",
              timestamp: new Date().toISOString(),
            });
          }
          break;

        case "document_retrieved":
          if (message.doc_id && message.resource_type && message.text) {
            onNewDocument({
              doc_id: message.doc_id,
              resource_type: message.resource_type,
              resource_id: message.resource_id || "",
              text: message.text,
              score: message.score || 0,
              timestamp: message.timestamp || new Date().toISOString(),
            });
          }
          break;

        case "response":
          if (message.content) {
            setResponse(message.content);
            speak(message.content);
          }
          break;

        case "timeline_commit":
          if (message.title && message.summary) {
            onNewCommit({
              id: Date.now().toString(),
              title: message.title,
              summary: message.summary,
              timestamp: new Date().toISOString(),
              citations: message.citations || [],
            });
          }
          break;

        case "citations":
          if (message.citations) {
            onNewCitations(message.citations);
          }
          break;

        case "error":
          console.error("Error from server:", message.message);
          setError(message.message || "An error occurred");
          break;

        case "ack":
          console.log("Server acknowledged:", message.message);
          break;
        
        case "tool_start":
          // Show tool execution in reasoning steps
          if (message.tool) {
            stepCounterRef.current += 1;
            onNewReasoningStep({
              id: `tool-start-${stepCounterRef.current}-${Date.now()}`,
              emoji: "⚙️",
              step: `Using: ${message.tool}`,
              content: `Calling ${message.tool}...`,
              timestamp: new Date().toISOString(),
            });
          }
          break;
        
        case "tool_complete":
          // Show tool completion
          if (message.tool) {
            stepCounterRef.current += 1;
            const resultPreview = JSON.stringify(message.result).substring(0, 100);
            onNewReasoningStep({
              id: `tool-complete-${stepCounterRef.current}-${Date.now()}`,
              emoji: "✅",
              step: `Completed: ${message.tool}`,
              content: `Got results from ${message.tool}`,
              timestamp: new Date().toISOString(),
            });
          }
          break;
        
        case "text_chunk":
          // Stream response text as it comes in
          if (message.text) {
            setResponse((prev) => prev + message.text);
          }
          break;
        
        case "response_complete":
          // Final response is complete
          if (message.full_text) {
            setResponse(message.full_text);
            speak(message.full_text);
          }
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setWsConnected(false);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [onNewCommit, onNewCitations, onNewReasoningStep, onNewDocument]);

  const toggleListening = () => {
    if (isListening) {
      console.log("🛑 Stopping speech recognition...");
      recognitionRef.current?.stop();
      setIsListening(false);
      setStatusMessage("");
      
      // Send transcript if we have one
      if (transcript.trim()) {
        console.log("📤 Sending transcript:", transcript);
        sendTranscript();
      }
    } else {
      if (!recognitionRef.current) {
        setError("Speech recognition not available. Please use Chrome or Edge browser.");
        return;
      }
      
      console.log("🎤 Starting speech recognition...");
      console.log("Browser:", navigator.userAgent);
      
      try {
        setError(null);
        setStatusMessage("Starting microphone...");
        recognitionRef.current.start();
        setIsListening(true);
        setTranscript("");
        setInterimTranscript("");
        setResponse("");
        onClearReasoningSteps();
        
        console.log("✅ Recognition start() called successfully");
      } catch (e: any) {
        console.error("❌ Failed to start recognition:", e);
        setError(`Failed to start microphone: ${e.message}. Please check permissions and try again.`);
        setIsListening(false);
        setStatusMessage("");
      }
    }
  };

  const sendTranscript = () => {
    if (!transcript.trim() || !wsConnected) return;

    // Clear previous response and reasoning steps
    setResponse("");
    onClearReasoningSteps();

    wsRef.current?.send(
      JSON.stringify({
        type: "voice_transcript",
        patient_id: patientId,
        transcript: transcript.trim(),
      })
    );

    setIsListening(false);
    recognitionRef.current?.stop();
  };

  const speak = async (text: string) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }

      setIsSpeaking(true);
      
      // Call backend TTS endpoint
      const response = await fetch("http://localhost:8000/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`TTS error: ${response.statusText}`);
      }

      // Convert response to Blob and play audio
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        console.error("Audio playback error");
      };

      audio.play().catch((err) => {
        setIsSpeaking(false);
        console.error("Failed to play audio:", err);
      });
    } catch (error) {
      setIsSpeaking(false);
      console.error("TTS error:", error);
    }
  };

  const stopSpeaking = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsSpeaking(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              wsConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-600">
            {wsConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
        {micPermission === "denied" && (
          <div className="flex items-center gap-2 text-red-500 text-xs">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Mic Denied
          </div>
        )}
      </div>

      {/* Safari Warning Banner */}
      {isSafari && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg"
        >
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-orange-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-bold text-orange-800">Safari doesn't support voice input</p>
              <p className="text-sm text-orange-700 mt-1">
                Safari has limited Web Speech API support and will show "audio task aborted" errors.
              </p>
              <div className="mt-2 flex items-center gap-2 text-sm">
                <span className="text-orange-700">✅ Solution:</span>
                <span className="text-orange-800 font-medium">Use Chrome or Edge for voice</span>
                <span className="text-orange-600">or</span>
                <span className="text-orange-800 font-medium">use the text input below ⬇️</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Error Display */}
      {error && !isSafari && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg"
        >
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              {micPermission === "denied" && (
                <button
                  onClick={() => window.location.reload()}
                  className="mt-2 text-xs text-red-600 hover:text-red-800 underline"
                >
                  Reload and allow microphone
                </button>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Microphone Button */}
      <div className="flex flex-col items-center justify-center mb-8">
        <motion.button
          onClick={toggleListening}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-colors ${
            isListening
              ? "bg-red-500 hover:bg-red-600"
              : "bg-blue-500 hover:bg-blue-600"
          }`}
          whileTap={{ scale: 0.95 }}
        >
          <AnimatePresence>
            {isListening && (
              <motion.div
                className="absolute inset-0 rounded-full bg-red-400 pulse-ring"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1.2 }}
                exit={{ opacity: 0 }}
              />
            )}
          </AnimatePresence>

          <svg
            className="w-12 h-12 text-white relative z-10"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        </motion.button>

        <div className="mt-4 text-center">
          <p className="text-sm font-medium text-gray-700">
            {isListening ? "Listening..." : "Click to speak"}
          </p>
          {statusMessage && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs text-blue-600 mt-1"
            >
              {statusMessage}
            </motion.p>
          )}
        </div>
      </div>

      {/* Transcript Display */}
      <div className="mb-6">
        <div className="bg-gray-50 rounded-lg p-4 min-h-[100px]">
          {transcript || interimTranscript ? (
            <p className="text-gray-900">
              {transcript}
              <span className="text-gray-400">{interimTranscript}</span>
            </p>
          ) : (
            <div className="text-center text-gray-400 py-6">
              <p className="text-sm">
                {isListening 
                  ? "Listening... start speaking" 
                  : "Your transcript will appear here"}
              </p>
            </div>
          )}
        </div>

        {transcript && !isListening && (
          <motion.button
            onClick={sendTranscript}
            className="mt-3 w-full bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg font-medium"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Send Query
          </motion.button>
        )}
      </div>

      {/* Text Input - Prominently Featured */}
      <div className={`mb-6 ${isSafari ? "bg-blue-50 border-2 border-blue-300 rounded-xl p-4" : ""}`}>
        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 border-t border-gray-300" />
          <span className={`text-sm font-medium ${isSafari ? "text-blue-700" : "text-gray-600"}`}>
            {isSafari ? "💬 Text Input (Works in Safari!)" : "Or type your query"}
          </span>
          <div className="flex-1 border-t border-gray-300" />
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && transcript.trim() && wsConnected && sendTranscript()}
            placeholder="Type your clinical query... (e.g., What are the patient's conditions?)"
            className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
            disabled={isListening}
            autoFocus={isSafari}
          />
          <button
            onClick={sendTranscript}
            disabled={!transcript.trim() || !wsConnected}
            className="px-8 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors shadow-sm hover:shadow-md"
          >
            Send
          </button>
        </div>
        {isSafari && (
          <p className="mt-2 text-xs text-blue-600 text-center">
            💡 Try: "What are the patient's current conditions?" or "What is the patient's blood pressure?"
          </p>
        )}
      </div>

      {/* Response Display */}
      {response && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-50 rounded-lg p-4"
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-semibold text-blue-900">Response:</h3>
            {isSpeaking && (
              <button
                onClick={stopSpeaking}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Stop
              </button>
            )}
          </div>
          <p className="text-gray-800 whitespace-pre-wrap">{response}</p>
        </motion.div>
      )}
    </div>
  );
}
