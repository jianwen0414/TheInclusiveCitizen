#!/usr/bin/env python3
"""
Bulk ingest all PDFs from a local folder into Vertex AI Search.

Usage:
    python scripts/bulk_ingest.py [--folder seed_docs] [--base-url http://localhost:8000]

Requirements:
    - The FastAPI backend must be running with Vertex AI Search credentials configured.
    - Run: pip install httpx (or use the backend venv which already has it)

Each PDF is POSTed to POST /api/ingest with doc_type=government_guide.
The script prints the status for each file. Re-running is safe — the ingestor
uses upsert (ON CONFLICT doc_name) so already-ingested documents are updated
in Supabase metadata and re-queued in Discovery Engine (INCREMENTAL mode).

Ingestion is asynchronous on the Vertex AI Search side: documents become
searchable 5–30 minutes after this script completes.
"""

import argparse
import sys
from pathlib import Path

import httpx


def ingest_pdf(base_url: str, pdf_path: Path, doc_type: str = "government_guide") -> dict:
    """POST a single PDF file to /api/ingest and return the parsed JSON response."""
    with open(pdf_path, "rb") as f:
        response = httpx.post(
            f"{base_url}/api/ingest",
            files={"file": (pdf_path.name, f, "application/pdf")},
            data={"doc_type": doc_type},
            timeout=60.0,
        )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk ingest PDF files from a local folder into Vertex AI Search"
    )
    parser.add_argument(
        "--folder",
        default="seed_docs",
        help="Path to folder containing PDF files (default: seed_docs)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="FastAPI backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--doc-type",
        default="government_guide",
        help="Document type tag stored in Supabase metadata (default: government_guide)",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {folder}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s) in {folder}. Ingesting via {args.base_url} ...")
    print()

    success = 0
    failed = 0

    for pdf in pdfs:
        print(f"  [{pdfs.index(pdf) + 1}/{len(pdfs)}] {pdf.name} ... ", end="", flush=True)
        try:
            result = ingest_pdf(args.base_url, pdf, doc_type=args.doc_type)
            status = result.get("status", "?")
            note = result.get("indexing_note", "")
            print(f"OK ({status})")
            if note:
                # Print the first 140 chars of the note to keep output readable
                print(f"         {note[:140]}")
            success += 1
        except httpx.HTTPStatusError as exc:
            print(f"FAILED (HTTP {exc.response.status_code}: {exc.response.text[:120]})")
            failed += 1
        except Exception as exc:
            print(f"FAILED ({exc})")
            failed += 1

    print()
    print(f"Done. {success} succeeded, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
