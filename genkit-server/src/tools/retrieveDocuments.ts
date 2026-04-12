/**
 * Genkit tool: retrieveDocuments
 * Calls POST /api/retrieve on the FastAPI backend.
 * Mirrors backend/tools/retrieve_documents.py
 */
import { z } from "zod";
import { ai } from "../ai.js";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://localhost:8000";

export const RetrievedChunkSchema = z.object({
  doc_name: z.string(),
  doc_type: z.string().nullable().optional(),
  page_number: z.number().nullable().optional(),
  chunk_text: z.string(),
  similarity: z.number(),
  metadata: z.record(z.unknown()).nullable().optional(),
});

export const RetrieveDocumentsInputSchema = z.object({
  query: z.string(),
  top_k: z.number().default(6),
  threshold: z.number().default(0.25),
  doc_type_filter: z.array(z.string()).nullable().optional(),
});

export const RetrieveDocumentsOutputSchema = z.object({
  chunks: z.array(RetrievedChunkSchema),
  context: z.string(),
  original_chunk_text: z.string(),
  confidence: z.number(),
});

export type RetrievedChunk = z.infer<typeof RetrievedChunkSchema>;
export type RetrieveDocumentsInput = z.infer<typeof RetrieveDocumentsInputSchema>;
export type RetrieveDocumentsOutput = z.infer<typeof RetrieveDocumentsOutputSchema>;

export const retrieveDocumentsTool = ai.defineTool(
  {
    name: "retrieve_documents",
    description:
      "Embed the query using gemini-embedding-001 and retrieve the top-k most " +
      "relevant document chunks from Supabase pgvector (cosine similarity ≥ threshold). " +
      "Returns an empty result (not an error) when no chunks meet the threshold.",
    inputSchema: RetrieveDocumentsInputSchema,
    outputSchema: RetrieveDocumentsOutputSchema,
  },
  async (input: RetrieveDocumentsInput): Promise<RetrieveDocumentsOutput> => {
    const resp = await fetch(`${FASTAPI_BASE_URL}/api/retrieve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!resp.ok) {
      throw new Error(`retrieve_documents failed: ${resp.status} ${await resp.text()}`);
    }
    return RetrieveDocumentsOutputSchema.parse(await resp.json());
  }
);
