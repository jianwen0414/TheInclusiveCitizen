# Firebase Genkit Python SDK — Notes & Limitations

This document records findings from integrating `genkit==0.5.2` into The Inclusive Citizen
backend. It is intended as a reference for anyone extending or debugging the Genkit layer.

---

## Package Names

| Purpose | PyPI package | Import path |
|---------|-------------|-------------|
| Core framework | `genkit` | `from genkit import Genkit, ActionRunContext` |
| Gemini + Vertex AI plugin | `genkit-plugin-google-genai` | `from genkit.plugins.google_genai import VertexAI` |
| Vertex AI Model Garden (3rd-party models) | `genkit-plugin-vertex-ai` | `from genkit.plugins.vertex_ai import ModelGardenPlugin` |

> **Important:** `genkit-plugin-vertex-ai` is for Model Garden (Anthropic Claude, Llama, Mistral
> via Vertex). It is **not** the package for Gemini on Vertex AI. For Gemini on GCP use
> `genkit-plugin-google-genai` with the `VertexAI` class.

---

## Dependency Constraints Added by `genkit`

The following pins in `requirements.txt` were updated to satisfy genkit's transitive dependencies:

| Package | Before | After |
|---------|--------|-------|
| `uvicorn` | `==0.30.0` | `>=0.34.0,<1.0` |
| `pydantic` | `>=2.0,<3.0` | `>=2.10.5,<3.0` |

genkit also requires `starlette>=0.46.1` and `sse-starlette>=2.2.1` (both pulled in transitively).

---

## API Reference (Python SDK vs JS/TS SDK)

### Flows

**Python:**
```python
@ai.flow()
async def my_flow(input: MyInput, ctx: ActionRunContext) -> MyOutput:
    ctx.send_chunk("progress string")   # side-channel streaming
    ...
    return MyOutput(...)
```

**JS/TS equivalent:**
```ts
ai.defineFlow({ name: "myFlow", inputSchema: ..., outputSchema: ... }, async (input, streamingCallback) => {
    streamingCallback?.("progress string");
    ...
});
```

Key differences:
- Python uses a decorator (`@ai.flow()`); JS/TS uses `defineFlow()`.
- Python streaming uses `ctx: ActionRunContext` second parameter + `ctx.send_chunk()`.
- Python flow name defaults to the function name; set explicitly if needed.

### Calling a Flow

**Non-streaming (used in /api/query):**
```python
result = await inclusive_citizen_query_flow(QueryFlowInput(...))
# result is QueryResponse directly — no wrapper object
```

**Streaming (future frontend SSE):**
```python
stream_response = inclusive_citizen_query_flow.stream(QueryFlowInput(...))
async for chunk in stream_response.stream:   # ctx.send_chunk() values
    yield f"data: {chunk}\n\n"
final_output = await stream_response.response
```

### Tools

**Python:**
```python
@ai.tool(name="my_tool", description="...")
async def my_tool(input: MyInput) -> MyOutput:   # sync def also works
    ...
```

**JS/TS equivalent:**
```ts
ai.defineTool({ name: "myTool", description: "...", inputSchema: ..., outputSchema: ... }, async (input) => { ... });
```

Key differences:
- Python uses `@ai.tool(name=..., description=...)` decorator; JS/TS uses `defineTool()`.
- Tools can be `def` or `async def`; always call with `await tool(input)` from a flow.
- The `@ai.tool()` decorator makes the function awaitable regardless.

### Calling Tools from Within a Flow

```python
result = await my_tool(MyInput(field=value))
```

Calling through the decorated `Tool` object routes through Genkit's action system and
creates a named trace span in the Dev UI.

### Non-Genkit Steps in Traces (`ai.run()`)

To make an arbitrary code step appear as a named span in traces without defining a full tool:
```python
result = await ai.run("step-name", lambda: some_synchronous_function())
```

This is an alternative to `@ai.tool()` for pipeline steps that don't need LLM-callable schemas.

---

## Known Limitations vs JS/TS SDK (as of 0.5.2)

1. **Firebase App Check not available.** The JS/TS SDK has built-in App Check support.
   The Python SDK uses API key middleware via `genkit.plugin_api.api_key()` instead.
   Not needed for this project (internal GCP auth).

2. **`compute_semantic_score` is synchronous and CPU-bound.** The `sentence-transformers`
   `.encode()` call runs on the event loop. Current mitigation: called directly in an
   `async def` tool wrapper (acceptable for low concurrency). Future improvement:
   ```python
   import asyncio
   score = await asyncio.to_thread(
       _compute_semantic_score, original_bm_text, translated_simplified_text
   )
   ```

3. **`dotpromptz-handlebars` has no Windows wheels (CRITICAL).** The dependency chain
   `genkit` → `dotpromptz>=0.1.5` → `dotpromptz-handlebars>=0.1.8` fails on Windows because
   `dotpromptz-handlebars` is a Rust-compiled extension and its 0.1.8 release only ships
   macOS and Linux wheels. `pip install` on Windows reports:
   ```
   Could not find a version that satisfies the requirement dotpromptz-handlebars>=0.1.8
   (from versions: 0.1.2, 0.1.3)
   ```
   **Workarounds:**
   - **WSL (recommended):** Run the backend inside WSL — Linux wheels install cleanly.
   - **Build from source:** Install Rust (`winget install Rustlang.Rustup`) then
     `pip install --no-binary dotpromptz-handlebars -r requirements.txt`.
   - **Production:** Deploy on Linux (standard); this only affects Windows dev environments.

4. **No `uvloop` on Windows.** genkit lists `uvloop>=0.21.0` with
   `; sys_platform != 'win32'`, so it is skipped automatically on Windows (dev environment).
   No action needed.

4. **Genkit reflection server starts on port 4000 in dev mode.** Set `GENKIT_ENV=dev` to
   enable it. If port 4000 is busy the reflection server silently fails — FastAPI on 8000
   is unaffected.

5. **Plugin naming inconsistency.** The JS/TS package is `@genkit-ai/google-genai`; the
   Python package is `genkit-plugin-google-genai`. The import path `genkit.plugins.google_genai`
   (underscores) differs from the package name (hyphens) — standard Python convention.

6. **Streaming frontend integration is not yet wired.** `ctx.send_chunk()` calls are
   instrumented in `inclusive_citizen_query_flow` but `/api/query` currently awaits the
   final result. To enable SSE streaming to the frontend:
   - Change the FastAPI endpoint to return `StreamingResponse`
   - Replace `await flow(input)` with `flow.stream(input)`
   - Iterate `stream_response.stream` and yield SSE events
   - Await `stream_response.response` for the final `QueryResponse`

7. **Tools registered as LLM-callable actions.** `@ai.tool()` registers the function in
   Genkit's registry as a tool the LLM can invoke via function calling. In this pipeline
   the tools are called programmatically from within the flow — not via `ai.generate()`.
   This is valid usage; the registered schema simply goes unused for LLM function calling.
   An alternative is `ai.run("step-name", callable)` for purely programmatic steps.

---

## Architecture Diagram

```
Frontend → POST /api/query
  └─ routers/query.py
       └─ inclusive_citizen_query_flow(QueryFlowInput)   [flows/query_flow.py]
            ├─ detect_dialect_tool        → services/dialect_detector.py
            ├─ retrieve_documents_tool    → services/rag_pipeline.py
            ├─ generate_bm_answer_tool    → services/llm_service.py
            ├─ [translate_answer_tool]    → services/translation_service.py
            ├─ simplify_answer_tool       → services/simplifier.py + hijri_service.py
            ├─ compute_semantic_score_tool → services/semantic_scorer.py
            ├─ [simplify_answer_tool retry] (if score < 0.45)
            └─ synthesise_speech_tool     → services/tts_service.py
            → QueryResponse (returned directly)

Standalone endpoints (unchanged):
  POST /api/transcribe  → services/stt_service.py  (direct)
  POST /api/translate   → services/translation_service.py  (direct)
  POST /api/synthesise  → services/tts_service.py  (direct)
```

---

## Running the Genkit Developer UI

```bash
# Install the Genkit CLI (one-time)
curl -sL cli.genkit.dev | bash

# Start the backend with Dev UI enabled
cd backend
GENKIT_ENV=dev genkit start -- uvicorn main:app --reload

# Open http://localhost:4000 in your browser
```

The Dev UI shows a full trace for every `inclusive_citizen_query_flow` invocation,
including each named tool step with its input, output, and latency.
