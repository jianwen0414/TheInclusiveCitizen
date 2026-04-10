/**
 * Shared Genkit instance for The Inclusive Citizen.
 * Import `ai` from this module in all tool and flow files.
 * Never call genkit({...}) a second time — the registry is process-global.
 */
import "dotenv/config";
import { genkit } from "genkit";
import { vertexAI } from "@genkit-ai/vertexai";

export const ai = genkit({
  plugins: [
    vertexAI({
      projectId: process.env.GOOGLE_CLOUD_PROJECT ?? "",
      location: process.env.VERTEX_AI_LOCATION ?? "us-central1",
    }),
  ],
});
