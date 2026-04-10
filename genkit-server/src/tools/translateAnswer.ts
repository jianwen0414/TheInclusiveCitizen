/**
 * Genkit tool: translateAnswer
 * Calls POST /api/translate on the FastAPI backend.
 * Mirrors backend/tools/translate_answer.py
 *
 * Note: /api/translate returns { translated_text, model_used } but the flow
 * expects { translated_text, translation_model }. We remap model_used here.
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const TranslateAnswerInputSchema = z.object({
  text: z.string(),
  source_lang: z.string().default("en"),
  target_lang: z.string().default("ms"),
});

export const TranslateAnswerOutputSchema = z.object({
  translated_text: z.string(),
  translation_model: z.string(),
});

export type TranslateAnswerInput = z.infer<typeof TranslateAnswerInputSchema>;
export type TranslateAnswerOutput = z.infer<typeof TranslateAnswerOutputSchema>;

export const translateAnswerTool = ai.defineTool(
  {
    name: "translate_answer",
    description:
      "Translate an answer to the target language using Google Cloud TLLM (Tier 1) " +
      "or NLLB-200 (Tier 2 fallback for low-resource languages). " +
      "Only invoked when the LLM cannot generate reliably in the target language directly.",
    inputSchema: TranslateAnswerInputSchema,
    outputSchema: TranslateAnswerOutputSchema,
  },
  async (input: TranslateAnswerInput): Promise<TranslateAnswerOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`translate_answer failed: ${resp.status} ${await resp.text()}`);
    }
    const data = await resp.json() as { translated_text: string; model_used: string };
    return {
      translated_text: data.translated_text,
      translation_model: data.model_used,
    };
  }
);
