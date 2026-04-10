/**
 * Genkit tool: computeSemanticScore
 * Calls POST /api/score on the FastAPI backend.
 * Mirrors backend/tools/compute_semantic_score.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const ComputeSemanticScoreInputSchema = z.object({
  original_bm_text: z.string(),
  translated_simplified_text: z.string(),
});

export const ComputeSemanticScoreOutputSchema = z.object({
  score: z.number(),
});

export type ComputeSemanticScoreInput = z.infer<typeof ComputeSemanticScoreInputSchema>;
export type ComputeSemanticScoreOutput = z.infer<typeof ComputeSemanticScoreOutputSchema>;

export const computeSemanticScoreTool = ai.defineTool(
  {
    name: "compute_semantic_score",
    description:
      "Compute cross-lingual semantic similarity between the original BM source chunk " +
      "and the final translated + simplified answer using " +
      "paraphrase-multilingual-MiniLM-L12-v2. Returns a cosine similarity score " +
      "between 0.0 and 1.0. Scores below 0.45 for ms/en/id trigger a conservative " +
      "simplification retry.",
    inputSchema: ComputeSemanticScoreInputSchema,
    outputSchema: ComputeSemanticScoreOutputSchema,
  },
  async (input: ComputeSemanticScoreInput): Promise<ComputeSemanticScoreOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`compute_semantic_score failed: ${resp.status} ${await resp.text()}`);
    }
    return ComputeSemanticScoreOutputSchema.parse(await resp.json());
  }
);
