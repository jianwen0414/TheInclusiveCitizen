/**
 * Genkit tool: simplifyAnswer
 * Calls POST /api/simplify on the FastAPI backend.
 * Mirrors backend/tools/simplify_answer.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const SimplifyAnswerInputSchema = z.object({
  text: z.string(),
  language: z.string().default("English"),
  conservative: z.boolean().default(false),
  enrich_hijri: z.boolean().default(false),
});

export const SimplifyAnswerOutputSchema = z.object({
  simplified_text: z.string(),
  readability_grade: z.number(),
});

export type SimplifyAnswerInput = z.infer<typeof SimplifyAnswerInputSchema>;
export type SimplifyAnswerOutput = z.infer<typeof SimplifyAnswerOutputSchema>;

export const simplifyAnswerTool = ai.defineTool(
  {
    name: "simplify_answer",
    description:
      "Simplify an answer to a Grade 5–7 reading level using spaCy NER for jargon " +
      "extraction and an LLM rewrite pass. The conservative mode only restructures " +
      "sentences without altering meaning, used for the semantic-score retry pass. " +
      "Optionally annotates Gregorian dates with their Hijri equivalents inline.",
    inputSchema: SimplifyAnswerInputSchema,
    outputSchema: SimplifyAnswerOutputSchema,
  },
  async (input: SimplifyAnswerInput): Promise<SimplifyAnswerOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`simplify_answer failed: ${resp.status} ${await resp.text()}`);
    }
    return SimplifyAnswerOutputSchema.parse(await resp.json());
  }
);
