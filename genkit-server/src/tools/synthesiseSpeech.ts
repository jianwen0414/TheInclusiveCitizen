/**
 * Genkit tool: synthesiseSpeech
 * Calls POST /api/synthesise on the FastAPI backend.
 * Mirrors backend/tools/synthesise_speech.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const SynthesiseSpeechInputSchema = z.object({
  text: z.string(),
  language: z.string().default("en"),
  speed: z.number().default(1.0),
});

export const SynthesiseSpeechOutputSchema = z.object({
  audio_base64: z.string(),
  content_type: z.string().default("audio/mp3"),
});

export type SynthesiseSpeechInput = z.infer<typeof SynthesiseSpeechInputSchema>;
export type SynthesiseSpeechOutput = z.infer<typeof SynthesiseSpeechOutputSchema>;

export const synthesiseSpeechTool = ai.defineTool(
  {
    name: "synthesise_speech",
    description:
      "Convert text to speech using Google Cloud TTS (Neural2 > Wavenet > Standard " +
      "tier fallback). Returns base64-encoded MP3 audio and content type. " +
      "Speaking rate is persona-aware: elderly=0.75×, rural=0.9×, migrant=1.0×.",
    inputSchema: SynthesiseSpeechInputSchema,
    outputSchema: SynthesiseSpeechOutputSchema,
  },
  async (input: SynthesiseSpeechInput): Promise<SynthesiseSpeechOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/synthesise`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`synthesise_speech failed: ${resp.status} ${await resp.text()}`);
    }
    return SynthesiseSpeechOutputSchema.parse(await resp.json());
  }
);
