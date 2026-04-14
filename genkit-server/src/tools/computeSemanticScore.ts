/**
 * Genkit tool: computeSemanticScore
 * Calls POST /api/score on the FastAPI backend.
 * Mirrors backend/tools/compute_semantic_score.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const ComputeSemanticScoreInputSchema = z.object({
  source_text: z.string(),       // LLM-generated answer before simplification (target language)
  simplified_text: z.string(),   // simplified answer after simplification (same target language)
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
      "Compute simplification fidelity: cosine similarity between the LLM-generated " +
      "answer (before simplification) and the simplified answer (after simplification) " +
      "using paraphrase-multilingual-MiniLM-L12-v2. Both inputs are in the same target " +
      "language, making scoring language-agnostic. Returns a score between 0.0 and 1.0. " +
      "Scores below 0.70 for ms/en/id trigger a conservative simplification retry.",
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
