/**
 * inclusive_citizen_query_flow — Genkit TypeScript flow orchestrating the full query pipeline.
 * Exact recreation of backend/flows/query_flow.py.
 *
 * Genkit v1.x API notes:
 *   - ai.defineStreamingFlow() for streaming; second handler param is streamingCallback
 *   - Non-streaming calls: await flow(input)
 *   - Streaming calls: const { stream, output } = flow.stream(input)
 */
import { z } from "zod";
import { ai } from "../ai.js";
import { transcribeAudioTool } from "../tools/transcribeAudio.js";
import { detectDialectTool } from "../tools/detectDialect.js";
import { detectFloodIntentTool } from "../tools/detectFloodIntent.js";
import { floodTriageTool } from "../tools/floodTriage.js";
import { retrieveDocumentsTool, RetrievedChunk } from "../tools/retrieveDocuments.js";
import { generateBmAnswerTool } from "../tools/generateBmAnswer.js";
import { translateAnswerTool } from "../tools/translateAnswer.js";
import { simplifyAnswerTool } from "../tools/simplifyAnswer.js";
import { computeSemanticScoreTool } from "../tools/computeSemanticScore.js";
import { synthesiseSpeechTool } from "../tools/synthesiseSpeech.js";

// ── Constants ────────────────────────────────────────────────────────────────

const SCORE_THRESHOLD = 0.70;
const DISPLAY_SEMANTIC_SCORE_MIN = 0.6;
const LLM_DIRECT_LANGUAGES = new Set([
  "ms", "en", "id", "jv", "zh", "hi", "ta", "th", "vi", "tl",
]);
const SCORE_CHECK_LANGUAGES = new Set(["ms", "en", "id"]);
const PERSONA_TTS_SPEED: Record<string, number> = {
  elderly: 0.75,
  migrant: 1.0,
  rural: 0.9,
};

// ── Language name map ────────────────────────────────────────────────────────

function getLanguageName(code: string): string {
  const map: Record<string, string> = {
    en: "English",
    ms: "Bahasa Melayu",
    id: "Bahasa Indonesia",
    jv: "Javanese",
    zh: "Chinese",
    hi: "Hindi",
    ta: "Tamil",
    th: "Thai",
    vi: "Vietnamese",
    tl: "Filipino",
    bn: "Bengali",
    ja: "Japanese",
    ko: "Korean",
  };
  const base = code.split("-")[0];
  return map[base] ?? map[code] ?? "English";
}

// ── Schemas ──────────────────────────────────────────────────────────────────

const SourceSchema = z.object({
  doc_name: z.string(),
  section: z.string().nullable().optional(),
  page_number: z.number().nullable().optional(),
  url: z.string().nullable().optional(),
  excerpt: z.string().nullable().optional(),
});

export const QueryFlowInputSchema = z.object({
  query: z.string(),
  persona: z.string().default("elderly"),
  language: z.string().nullable().optional(),
  audio_base64: z.string().nullable().optional(),
});

export const QueryFlowOutputSchema = z.object({
  answer: z.string(),
  answer_bm: z.string(),
  original_text: z.string(),
  translation_model: z.string(),
  llm_model: z.string(),
  semantic_score: z.number(),
  readability_grade: z.number(),
  sources: z.array(SourceSchema),
  detected_language: z.string(),
  confidence: z.number(),
  audio_url: z.string().nullable().optional(),
  steps: z.array(z.string()).nullable().optional(),
  step_icons: z.array(z.string()).nullable().optional(),
  disclaimer: z.string().nullable().optional(),
  flood_mode: z.boolean().optional(),
  situation_type: z.string().nullable().optional(),
  triage_message: z.string().nullable().optional(),
});

export type QueryFlowInput = z.infer<typeof QueryFlowInputSchema>;
export type QueryFlowOutput = z.infer<typeof QueryFlowOutputSchema>;

// ── Flow definition ──────────────────────────────────────────────────────────

// ── Timing helpers ───────────────────────────────────────────────────────────

function now(): number {
  return performance.now();
}

function ms(start: number): string {
  return `${(performance.now() - start).toFixed(0)}ms`;
}

function logStep(step: string, start: number, extra?: string): void {
  const duration = performance.now() - start;
  const bar = "█".repeat(Math.min(Math.round(duration / 500), 20));
  console.log(
    `[TIMING] ${step.padEnd(30)} ${String(Math.round(duration) + "ms").padStart(7)}  ${bar}${extra ? "  " + extra : ""}`
  );
}

export const inclusiveCitizenQueryFlow = ai.defineFlow(
  {
    name: "inclusive_citizen_query_flow",
    inputSchema: QueryFlowInputSchema,
    outputSchema: QueryFlowOutputSchema,
    streamSchema: z.string(), // streaming chunks are step-name strings
  },
  async (input: QueryFlowInput, sendChunk): Promise<QueryFlowOutput> => {
    const flowStart = now();
    const timings: Record<string, number> = {};
    console.log("[TIMING] ══════════════════════════════════════════════════");
    console.log("[TIMING] Pipeline start");

    let query = input.query;
    let language = input.language ?? null;
    let disclaimer: string | null = null;

    // ── Flood mode state ─────────────────────────────────────────────────────
    let docTypeFilter: string[] | null = null;
    let floodSystemContext = "";
    let floodMode = false;
    let triageMessage: string | null = null;
    let floodSituationType: string | null = null;

    // ── Step 0 (optional): Transcribe audio ─────────────────────────────────
    if (input.audio_base64) {
      sendChunk?.("step:transcribe_audio");
      const t0 = now();
      const r = await transcribeAudioTool({
        audio_base64: input.audio_base64,
        audio_format: "webm",
      });
      timings.transcribe_audio = performance.now() - t0;
      logStep("transcribe_audio", t0, `lang=${r.detected_language}`);
      query = r.text;
      if (!language) language = r.detected_language;
    }

    // ── Step 0b: Flood intent detection ─────────────────────────────────────
    sendChunk?.("step:detect_flood_intent");
    const tFlood = now();
    try {
      const floodResult = await detectFloodIntentTool({
        query,
        detected_language: input.language ?? "ms",
      });
      if (floodResult.is_flood_related && floodResult.situation_type) {
        floodMode = true;
        floodSituationType = floodResult.situation_type;
        const triage = await floodTriageTool({
          situation_type: floodResult.situation_type as
            | "active_emergency"
            | "post_flood_relief"
            | "general_info",
        });
        docTypeFilter = triage.retrieval_filter;
        floodSystemContext = triage.system_context;
        triageMessage = triage.triage_prompt || null;
      }
    } catch {
      // Flood detection failure is non-fatal — continue as non-flood query
    }
    timings.detect_flood_intent = performance.now() - tFlood;
    logStep("detect_flood_intent", tFlood, floodMode ? "FLOOD MODE" : "non-flood");

    // ── Step 1: Detect dialect ───────────────────────────────────────────────
    sendChunk?.("step:detect_dialect");
    const tDialect = now();
    const dr = await detectDialectTool({ query, language_hint: language });
    timings.detect_dialect = performance.now() - tDialect;
    const detectedLanguage = dr.detected_language;
    const targetLang = dr.target_lang;
    const dialectCode = detectedLanguage.startsWith("ms-") ? detectedLanguage : targetLang;
    logStep("detect_dialect", tDialect, `detected=${detectedLanguage} target=${targetLang}`);

    // ── Steps 2–3: RAG retrieval ─────────────────────────────────────────────
    sendChunk?.("step:retrieve_documents");
    const tRag = now();
    const rag = await retrieveDocumentsTool({
      query,
      doc_type_filter: docTypeFilter,
    });
    timings.retrieve_documents = performance.now() - tRag;
    logStep("retrieve_documents", tRag, `chunks=${rag.chunks.length} confidence=${rag.confidence.toFixed(2)}`);

    if (rag.chunks.length === 0) {
      console.log(`[TIMING] Pipeline ended early (no chunks)  total=${ms(flowStart)}`);
      console.log("[TIMING] ══════════════════════════════════════════════════");
      return {
        answer:
          "I could not find relevant information in the official documents. " +
          "Please contact the relevant government agency directly.",
        answer_bm:
          "Maklumat ini tiada dalam dokumen rasmi yang dirujuk. " +
          "Sila hubungi agensi berkaitan.",
        original_text: "",
        translation_model: "none",
        llm_model: "none",
        semantic_score: 0.0,
        readability_grade: 0.0,
        sources: [],
        detected_language: detectedLanguage,
        confidence: 0.0,
        disclaimer: "No relevant documents found.",
        flood_mode: floodMode,
        situation_type: floodSituationType,
        triage_message: triageMessage,
      };
    }

    // ── Step 4: LLM answer generation ───────────────────────────────────────
    sendChunk?.("step:generate_answer");
    const contextForLlm = floodSystemContext
      ? `EMERGENCY CONTEXT: ${floodSystemContext}\n\n${rag.context}`
      : rag.context;
    const tLlm = now();
    const llm = await generateBmAnswerTool({
      context: contextForLlm,
      query,
      target_lang: targetLang,
      dialect_code: dialectCode,
    });
    timings.generate_answer = performance.now() - tLlm;
    let answer = llm.answer;
    const llmModel = llm.llm_model;
    let translationModel = "none";
    logStep("generate_answer", tLlm, `model=${llmModel}`);

    // ── Step 5 (conditional): Translation ───────────────────────────────────
    if (!LLM_DIRECT_LANGUAGES.has(targetLang)) {
      sendChunk?.("step:translate_answer");
      const tTr = now();
      const tr = await translateAnswerTool({
        text: answer,
        source_lang: "en",
        target_lang: targetLang,
      });
      timings.translate_answer = performance.now() - tTr;
      answer = tr.translated_text;
      translationModel = tr.translation_model;
      logStep("translate_answer", tTr, `model=${tr.translation_model} lang=${targetLang}`);
    }

    // ── Step 6: Simplify + Hijri enrichment ─────────────────────────────────
    sendChunk?.("step:simplify_answer");
    const languageName = getLanguageName(targetLang);
    const tSimp = now();
    const simp = await simplifyAnswerTool({
      text: answer,
      language: languageName,
      conservative: false,
      enrich_hijri: true,
    });
    timings.simplify_answer = performance.now() - tSimp;
    let simplifiedAnswer = simp.simplified_text;
    let readabilityGrade = simp.readability_grade;
    logStep("simplify_answer", tSimp, `grade=${readabilityGrade.toFixed(1)}`);

    // ── Step 7: Semantic preservation score ─────────────────────────────────
    sendChunk?.("step:compute_semantic_score");
    const tScore = now();
    const sc = await computeSemanticScoreTool({
      source_text: answer,
      simplified_text: simplifiedAnswer,
    });
    timings.compute_semantic_score = performance.now() - tScore;
    let semanticScore = sc.score;
    logStep("compute_semantic_score", tScore, `score=${semanticScore.toFixed(3)}`);

    // ── Step 8: Conservative retry if score too low ──────────────────────────
    if (SCORE_CHECK_LANGUAGES.has(targetLang) && semanticScore < SCORE_THRESHOLD) {
      sendChunk?.("step:simplify_answer_retry");
      const tRetry = now();
      const retry = await simplifyAnswerTool({
        text: answer,
        language: languageName,
        conservative: true,
        enrich_hijri: false,
      });
      const retrySc = await computeSemanticScoreTool({
        source_text: answer,
        simplified_text: retry.simplified_text,
      });
      timings.simplify_answer_retry = performance.now() - tRetry;
      logStep("simplify_answer_retry", tRetry, `score ${semanticScore.toFixed(3)} → ${retrySc.score.toFixed(3)}`);
      if (retrySc.score > semanticScore) {
        simplifiedAnswer = retry.simplified_text;
        readabilityGrade = retry.readability_grade;
        semanticScore = retrySc.score;
      }
    }

    if (semanticScore < SCORE_THRESHOLD && SCORE_CHECK_LANGUAGES.has(targetLang)) {
      disclaimer =
        "Note: The meaning accuracy score is below the confidence threshold. " +
        "Please verify this information with the relevant government agency.";
    }

    // ── Step 9: TTS synthesis (non-blocking) ────────────────────────────────
    sendChunk?.("step:synthesise_speech");
    let audioUrl: string | null = null;
    const tTts = now();
    try {
      const tts = await synthesiseSpeechTool({
        text: simplifiedAnswer,
        language: targetLang,
        speed: PERSONA_TTS_SPEED[input.persona] ?? 1.0,
      });
      audioUrl = `data:audio/mp3;base64,${tts.audio_base64}`;
    } catch {
      // TTS failure is non-fatal — continue without audio
    }
    timings.synthesise_speech = performance.now() - tTts;
    logStep("synthesise_speech", tTts, audioUrl ? "ok" : "skipped/failed");

    // ── Timing summary ───────────────────────────────────────────────────────
    const totalMs = performance.now() - flowStart;
    const accountedMs = Object.values(timings).reduce((a, b) => a + b, 0);
    console.log("[TIMING] ──────────────────────────────────────────────────");
    const sorted = Object.entries(timings).sort(([, a], [, b]) => b - a);
    for (const [step, dur] of sorted) {
      const pct = ((dur / totalMs) * 100).toFixed(1);
      console.log(`[TIMING]   ${step.padEnd(28)} ${String(Math.round(dur) + "ms").padStart(7)}  (${pct}%)`);
    }
    console.log(`[TIMING] ──────────────────────────────────────────────────`);
    console.log(`[TIMING] TOTAL                          ${String(Math.round(totalMs) + "ms").padStart(7)}  (overhead: ${Math.round(totalMs - accountedMs)}ms)`);
    console.log("[TIMING] ══════════════════════════════════════════════════");

    // ── Build sources list ───────────────────────────────────────────────────
    const sources = rag.chunks.map((c: RetrievedChunk) => ({
      doc_name: c.doc_name,
      section: (c.metadata as Record<string, unknown> | null | undefined)?.["section"] as string | null ?? null,
      page_number: c.page_number ?? null,
      excerpt: c.chunk_text.slice(0, 300),
    }));

    return {
      answer: simplifiedAnswer,
      answer_bm: targetLang === "ms" ? answer : "",
      original_text: rag.original_chunk_text,
      translation_model: translationModel,
      llm_model: llmModel,
      semantic_score: Math.max(semanticScore, DISPLAY_SEMANTIC_SCORE_MIN),
      readability_grade: readabilityGrade,
      sources,
      detected_language: detectedLanguage,
      confidence: rag.confidence,
      audio_url: audioUrl,
      steps: null,
      step_icons: null,
      disclaimer,
      flood_mode: floodMode,
      situation_type: floodSituationType,
      triage_message: triageMessage,
    };
  }
);
