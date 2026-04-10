/**
 * Genkit tool: generateBmAnswer
 * Calls POST /api/generate on the FastAPI backend.
 * Mirrors backend/tools/generate_bm_answer.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const GenerateBmAnswerInputSchema = z.object({
  context: z.string(),
  query: z.string(),
  target_lang: z.string().default("ms"),
  dialect_code: z.string().default("ms"),
});

export const GenerateBmAnswerOutputSchema = z.object({
  answer: z.string(),
  llm_model: z.string(),
});

export type GenerateBmAnswerInput = z.infer<typeof GenerateBmAnswerInputSchema>;
export type GenerateBmAnswerOutput = z.infer<typeof GenerateBmAnswerOutputSchema>;

export const generateBmAnswerTool = ai.defineTool(
  {
    name: "generate_bm_answer",
    description:
      "Generate a grounded answer in the user's target language using Gemini 2.0 Flash " +
      "(primary) or SEA-LION v4 BM specialist (fallback for Malay dialects). " +
      "Returns the answer text and the model ID that produced it.",
    inputSchema: GenerateBmAnswerInputSchema,
    outputSchema: GenerateBmAnswerOutputSchema,
  },
  async (input: GenerateBmAnswerInput): Promise<GenerateBmAnswerOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`generate_bm_answer failed: ${resp.status} ${await resp.text()}`);
    }
    return GenerateBmAnswerOutputSchema.parse(await resp.json());
  }
);
