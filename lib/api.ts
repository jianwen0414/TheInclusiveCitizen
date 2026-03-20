/**
 * API client for The Inclusive Citizen backend.
 * Maps to all endpoints defined in PRD Section 7.1 (Table 10).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────

export interface QueryRequest {
  query: string;
  persona: string;
  language?: string | null;
}

export interface Source {
  doc_name: string;
  section?: string | null;
  page_number?: number | null;
  url?: string | null;
  excerpt?: string | null;
}

export interface QueryResponse {
  answer: string;
  answer_bm: string;
  original_text: string;
  translation_model: string;
  semantic_score: number;
  readability_grade: number;
  sources: Source[];
  detected_language: string;
  confidence: number;
  audio_url?: string | null;
  steps?: string[] | null;
  step_icons?: string[] | null;
  disclaimer?: string | null;
}

export interface TranscribeResponse {
  text: string;
  detected_language: string;
}

export interface SynthesiseResponse {
  audio_base64: string;
  content_type: string;
}

export interface TranslateResponse {
  translated_text: string;
  model_used: string;
}

export interface HealthResponse {
  status: string;
  services: Record<string, string>;
}

export interface ExtractStepsRequest {
  answer: string;
  language: string;
}

export interface ExtractStepsResponse {
  steps: string[];
  step_icons: string[];
}

// ── API Functions ─────────────────────────────────────

export async function queryBackend(req: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Query failed: ${err}`);
  }
  return res.json();
}

export async function transcribeAudio(audioBlob: Blob): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");

  const res = await fetch(`${API_BASE}/api/transcribe`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Transcription failed: ${err}`);
  }
  return res.json();
}

export async function synthesiseSpeech(
  text: string,
  language: string,
  speed: number = 1.0
): Promise<SynthesiseResponse> {
  const res = await fetch(`${API_BASE}/api/synthesise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language, speed }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Synthesis failed: ${err}`);
  }
  return res.json();
}

export async function translateText(
  text: string,
  sourceLang: string,
  targetLang: string
): Promise<TranslateResponse> {
  const res = await fetch(`${API_BASE}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Translation failed: ${err}`);
  }
  return res.json();
}

export async function ingestDocument(
  file: File,
  docType: string = "government_guide"
): Promise<{ status: string; doc_name: string; chunks_created: number }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("doc_type", docType);

  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Ingestion failed: ${err}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function extractStepsApi(req: ExtractStepsRequest): Promise<ExtractStepsResponse> {
  const res = await fetch(`${API_BASE}/api/extract-steps`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Step extraction failed: ${err}`);
  }
  return res.json();
}
