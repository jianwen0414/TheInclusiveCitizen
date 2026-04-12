/**
 * genkit-server/src/index.ts
 *
 * Genkit TypeScript orchestration server for The Inclusive Citizen.
 * Runs on PORT (default 3001). The FastAPI backend proxies /api/query here.
 *
 * Endpoints:
 *   POST /flow/query         — run inclusive_citizen_query_flow, return JSON
 *   POST /flow/query/stream  — SSE streaming: step chunks + final response
 *   GET  /health             — liveness check
 */
import "./ai.js"; // initialise Genkit + register plugins before importing tools/flows

// Import tools so ai.defineTool() calls fire before the flow is defined
import "./tools/transcribeAudio.js";
import "./tools/detectDialect.js";
import "./tools/detectFloodIntent.js";
import "./tools/floodTriage.js";
import "./tools/retrieveDocuments.js";
import "./tools/generateBmAnswer.js";
import "./tools/translateAnswer.js";
import "./tools/simplifyAnswer.js";
import "./tools/computeSemanticScore.js";
import "./tools/synthesiseSpeech.js";

import express, { Request, Response } from "express";
import { inclusiveCitizenQueryFlow, QueryFlowInputSchema } from "./flows/queryFlow.js";

const app = express();
app.use(express.json());

const PORT = parseInt(process.env.PORT ?? "3001", 10);

// Health check
app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok" });
});

// Non-streaming query endpoint
app.post("/flow/query", async (req: Request, res: Response) => {
  try {
    const input = QueryFlowInputSchema.parse(req.body);
    const result = await inclusiveCitizenQueryFlow(input);
    res.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(500).json({ error: message });
  }
});

// SSE streaming query endpoint — yields step progress chunks then final result
app.post("/flow/query/stream", async (req: Request, res: Response) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  try {
    const input = QueryFlowInputSchema.parse(req.body);
    const { stream, output } = inclusiveCitizenQueryFlow.stream(input);

    for await (const chunk of stream) {
      res.write(`data: ${JSON.stringify({ chunk })}\n\n`);
    }

    const result = await output;
    res.write(`data: ${JSON.stringify({ result })}\n\n`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.write(`data: ${JSON.stringify({ error: message })}\n\n`);
  } finally {
    res.end();
  }
});

app.listen(PORT, () => {
  console.log(`[genkit-server] Listening on http://localhost:${PORT}`);
  console.log(`[genkit-server] FastAPI base: ${process.env.FASTAPI_BASE_URL ?? "http://localhost:8000"}`);
});
