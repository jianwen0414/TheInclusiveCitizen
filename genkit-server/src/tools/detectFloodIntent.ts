/**
 * Genkit tool: detectFloodIntent
 * Calls POST /api/detect-flood-intent on the FastAPI backend.
 * Returns safe defaults on any error so it never blocks the main pipeline.
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const DetectFloodIntentInputSchema = z.object({
  query: z.string(),
  detected_language: z.string(),
});

export const DetectFloodIntentOutputSchema = z.object({
  is_flood_related: z.boolean(),
  situation_type: z
    .enum(["active_emergency", "post_flood_relief", "general_info"])
    .nullable(),
  confidence: z.number(),
});

export type DetectFloodIntentInput = z.infer<typeof DetectFloodIntentInputSchema>;
export type DetectFloodIntentOutput = z.infer<typeof DetectFloodIntentOutputSchema>;

export const detectFloodIntentTool = ai.defineTool(
  {
    name: "detect_flood_intent",
    description:
      "Classify whether a user query is related to floods, flood emergency, or flood relief. " +
      "Returns is_flood_related, situation_type, and confidence. " +
      "Always returns safe defaults on failure — never throws.",
    inputSchema: DetectFloodIntentInputSchema,
    outputSchema: DetectFloodIntentOutputSchema,
  },
  async (input: DetectFloodIntentInput): Promise<DetectFloodIntentOutput> => {
    try {
      const resp = await fetch(`${FASTAPI_BASE_URL}/api/detect-flood-intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!resp.ok) {
        return { is_flood_related: false, situation_type: null, confidence: 0.0 };
      }
      return DetectFloodIntentOutputSchema.parse(await resp.json());
    } catch {
      return { is_flood_related: false, situation_type: null, confidence: 0.0 };
    }
  }
);
