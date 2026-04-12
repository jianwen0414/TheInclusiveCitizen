/**
 * Genkit tool: floodTriage
 * Pure logic — no API call. Maps a flood situation type to:
 *   - triage_prompt: question to surface to the user (informational)
 *   - retrieval_filter: doc_type values for Vertex AI Search filtering
 *   - system_context: injected into the LLM prompt as additional instruction
 */
import { z } from "zod";
import { ai } from "../ai.js";

const SituationTypeSchema = z.enum([
  "active_emergency",
  "post_flood_relief",
  "general_info",
]);

export const FloodTriageInputSchema = z.object({
  situation_type: SituationTypeSchema,
});

export const FloodTriageOutputSchema = z.object({
  triage_prompt: z.string(),
  retrieval_filter: z.array(z.string()),
  system_context: z.string(),
});

export type FloodTriageInput = z.infer<typeof FloodTriageInputSchema>;
export type FloodTriageOutput = z.infer<typeof FloodTriageOutputSchema>;

type SituationType = z.infer<typeof SituationTypeSchema>;

const TRIAGE_MAP: Record<SituationType, FloodTriageOutput> = {
  active_emergency: {
    triage_prompt:
      "Are you currently in a flood situation and need immediate help, or do you need " +
      "information about emergency contacts and procedures?",
    retrieval_filter: ["flood_emergency", "flood_alert"],
    system_context:
      "The user may be in an active flood emergency. Prioritise immediate safety actions, " +
      "evacuation procedures, and emergency contact numbers. Be concise and direct.",
  },
  post_flood_relief: {
    triage_prompt:
      "Are you looking for information about flood relief aid, damage claims, or recovery assistance?",
    retrieval_filter: ["flood_relief", "flood_emergency"],
    system_context:
      "The user is seeking post-flood assistance. Focus on JKM aid eligibility, " +
      "application procedures, and recovery steps.",
  },
  general_info: {
    triage_prompt: "",
    retrieval_filter: ["flood_emergency", "flood_relief", "flood_alert"],
    system_context: "Provide general flood preparedness and response information.",
  },
};

export const floodTriageTool = ai.defineTool(
  {
    name: "flood_triage",
    description:
      "Returns the triage prompt, Vertex AI Search doc_type filter, and system context " +
      "for a given flood situation type. Pure logic — no network call.",
    inputSchema: FloodTriageInputSchema,
    outputSchema: FloodTriageOutputSchema,
  },
  async (input: FloodTriageInput): Promise<FloodTriageOutput> => {
    return TRIAGE_MAP[input.situation_type];
  }
);
