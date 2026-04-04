export interface TimelineCommit {
  id: string;
  title: string;
  summary: string;
  timestamp: string;
  citations: number[];
}

export interface Citation {
  id: number;
  resource_type: string;
  resource_id: string;
  snippet: string;
  timestamp: string;
  score?: number;
}

export interface ReasoningStep {
  id: string;
  emoji?: string;
  step?: string;
  content: string;
  timestamp: string;
}

export interface Document {
  doc_id: number;
  resource_type: string;
  resource_id: string;
  text: string;
  score: number;
  timestamp: string;
}

export interface WSMessage {
  type: "reasoning_step" | "response" | "timeline_commit" | "citations" | "error" | "ack" | "document_retrieved" | "branch_created" | "tool_start" | "tool_complete" | "text_chunk" | "response_complete";
  emoji?: string;
  step?: string;
  content?: string;
  title?: string;
  summary?: string;
  citations?: Citation[];
  message?: string;
  doc_id?: number;
  resource_type?: string;
  resource_id?: string;
  text?: string;
  score?: number;
  timestamp?: string;
  branch?: any;
  timeline?: any[];
  safety_analysis?: any;
  tree?: any;
  documents_reviewed?: number;
  tool?: string;
  result?: any;
  full_text?: string;
}
