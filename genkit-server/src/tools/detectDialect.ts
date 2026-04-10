/**
 * Genkit tool: detectDialect
 * Calls POST /api/detect-dialect on the FastAPI backend.
 * Mirrors backend/tools/detect_dialect.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const DetectDialectInputSchema = z.object({
  query: z.string(),
  language_hint: z.string().nullable().optional(),
});

export const DetectDialectOutputSchema = z.object({
  detected_language: z.string(),
  target_lang: z.string(),
});

export type DetectDialectInput = z.infer<typeof DetectDialectInputSchema>;
export type DetectDialectOutput = z.infer<typeof DetectDialectOutputSchema>;

export const detectDialectTool = ai.defineTool(
  {
    name: "detect_dialect",
    description:
      "Detect the language and Malay sub-dialect of a query string. " +
      "Returns an ISO language code (e.g. 'ms', 'ms-kelantanese', 'jv', 'en') as " +
      "detected_language, and the base language code as target_lang.",
    inputSchema: DetectDialectInputSchema,
    outputSchema: DetectDialectOutputSchema,
  },
  async (input: DetectDialectInput): Promise<DetectDialectOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/detect-dialect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`detect_dialect failed: ${resp.status} ${await resp.text()}`);
    }
    return DetectDialectOutputSchema.parse(await resp.json());
  }
);
