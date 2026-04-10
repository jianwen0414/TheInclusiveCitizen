/**
 * Genkit tool: transcribeAudio
 * Calls POST /api/transcribe on the FastAPI backend (multipart form upload).
 * Mirrors backend/tools/transcribe_audio.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const TranscribeAudioInputSchema = z.object({
  audio_base64: z.string(),
  audio_format: z.string().default("webm"),
});

export const TranscribeAudioOutputSchema = z.object({
  text: z.string(),
  detected_language: z.string(),
});

export type TranscribeAudioInput = z.infer<typeof TranscribeAudioInputSchema>;
export type TranscribeAudioOutput = z.infer<typeof TranscribeAudioOutputSchema>;

export const transcribeAudioTool = ai.defineTool(
  {
    name: "transcribe_audio",
    description:
      "Transcribe base64-encoded audio to text using Google Cloud STT v2 chirp_3. " +
      "Returns the transcript and the detected ISO language code.",
    inputSchema: TranscribeAudioInputSchema,
    outputSchema: TranscribeAudioOutputSchema,
  },
  async (input: TranscribeAudioInput): Promise<TranscribeAudioOutput> => {
    // Decode base64 → binary → FormData
    const audioBytes = Buffer.from(input.audio_base64, "base64");
    const formData = new FormData();
    const blob = new Blob([audioBytes], { type: `audio/${input.audio_format}` });
    formData.append("file", blob, `audio.${input.audio_format}`);

    const resp = await fetch(`${FASTAPI_BASE_URL}/api/transcribe`, {
      method: "POST",
      body: formData,
    });
    if (!resp.ok) {
      throw new Error(`transcribe_audio failed: ${resp.status} ${await resp.text()}`);
    }
    return TranscribeAudioOutputSchema.parse(await resp.json());
  }
);
