# ClusterSage

ClusterSage is a Python log-triage tool for distributed compute environments, with an initial emphasis on GPU-cluster style systems. In practical terms, it is a local pipeline for taking a directory of messy logs, turning each non-blank line into a structured record, normalizing unstable tokens, and storing the result in DuckDB so the run becomes easier to inspect.

The project is intentionally conservative. It is not trying to diagnose failures autonomously or replace engineering judgment. Its current job is to make raw logs more legible, more comparable, and easier to query so a human can see recurring patterns and inspect suspicious behavior with less manual cleanup.

This repository is meant to work in two roles at once:

- as a usable engineering tool for early incident and run analysis
- as a clean foundation for later research in log parsing, anomaly detection, incident grouping, and cluster debugging workflows

## Current Implemented Stage

The current implemented layer is **ingestion + normalization**.

Today, ClusterSage can:

- recursively load `.log` and `.txt` files from a directory
- skip blank lines and preserve the original line text
- infer lightweight metadata from filenames such as `trainer_node03.log`
- attempt to parse timestamps from common log formats at the start of a line
- infer coarse fields such as severity and bracketed component labels
- normalize unstable tokens using regex rules loaded from YAML
- persist the processed records into a simple DuckDB table
- run the full flow through a Typer CLI command

That is the first practical milestone for the project: get raw logs into a structured, inspectable form before moving on to higher-level grouping or ranking.

## What ClusterSage Is Trying To Solve

Raw infrastructure logs are often difficult to use directly:

- the same event appears many times with small textual variations
- identifiers such as IP addresses, UUIDs, ports, counters, job IDs, and paths create noise
- timestamps may be missing or inconsistent
- important lines are buried inside repetitive boilerplate
- evidence is spread across multiple files and components

In GPU and cluster environments, this problem gets sharper. A single run may involve scheduler logs, trainer logs, node-level logs, transport or interconnect messages, and device-specific traces. Even when the evidence is present, it is not naturally readable as a coherent incident.

ClusterSage starts by making that evidence easier to work with.

## Current Pipeline

The current pipeline is straightforward:

1. Recursively discover `.log` and `.txt` files under a target directory.
2. Read each file line by line.
3. Skip blank lines.
4. Infer `source` and `host` from filename patterns when possible.
5. Parse a timestamp from the start of the line when it matches a supported format.
6. Infer lightweight fields such as `severity` and `component` when obvious.
7. Normalize unstable tokens using ordered regex replacement rules from `configs/normalization.yaml`.
8. Persist the resulting records into DuckDB.

This is intentionally simple. The point of the current implementation is reliable data preparation, not sophisticated interpretation.

## Canonical Log Schema

Each processed log line is represented as a single record with the following high-level fields:

- `id`: stable per-record identifier
- `timestamp`: parsed timestamp when present, otherwise `null`
- `source`: coarse source inferred from the filename when possible
- `host`: host inferred from the filename when possible
- `job_id`: optional run or job identifier supplied through the CLI
- `severity`: coarse severity token such as `INFO`, `WARN`, or `ERROR`
- `component`: lightweight component label when it can be inferred
- `raw_text`: original log line
- `normalized_text`: canonicalized form of the same line
- `file_path`: path to the source file
- `line_number`: original line number within the file

This schema is deliberately narrow. It keeps the first storage layer inspectable while preserving enough context for later stages.

## Why Normalization Exists

Normalization is the step that makes recurring patterns visible.

Without normalization, two lines that describe the same event may look different because they contain unstable values such as IP addresses, UUIDs, counters, durations, paths, or long request identifiers. That makes simple grouping and comparison much harder than it needs to be.

ClusterSage currently uses regex-based rules loaded from [configs/normalization.yaml](/Users/rohinghosh/Desktop/Projects/NVlog/clustersage/configs/normalization.yaml) to replace major token classes with readable placeholders such as:

- `<IP>`
- `<UUID>`
- `<HEX>`
- `<DURATION>`
- `<FLOAT>`
- `<INT>`
- `<PATH>`
- `<ID>`

The goal is not to erase detail. The goal is to preserve the original line in `raw_text` while producing a deterministic `normalized_text` that makes repeated event shapes easier to spot.

## Storage Model

Processed records are written into a local DuckDB database at the configured path, which defaults to `data/processed/clustersage.duckdb`.

The storage layer is intentionally minimal:

- one inspectable `log_records` table
- raw and normalized text stored together
- no heavy orchestration or service requirements

This keeps the current stage useful for local debugging and easy to evaluate in a research setting.

## Setup

From the repository root:

```bash
cd clustersage
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

The CLI and tests assume you run commands from the `clustersage/` project root so that local config and data paths resolve cleanly.

## Example Usage

ClusterSage ships with small synthetic logs under `data/raw/sample_run/`, so the ingest path can be exercised immediately.

```bash
cd clustersage
clustersage ingest ./data/raw/sample_run --job-id run_042
```

Expected behavior:

- discover supported log files recursively
- parse and normalize their contents
- write records to DuckDB
- print a concise summary including file count, line count, record count, and database path

## Repository Structure

The repository is divided by pipeline responsibility rather than by framework concern:

- `app/ingest/` handles file discovery, line loading, metadata inference, and timestamp parsing
- `app/normalize/` handles YAML-driven regex normalization
- `app/models/` defines record schemas and DuckDB persistence helpers
- `app/cli.py` exposes the batch workflow through Typer
- `configs/` stores readable defaults and normalization rules
- `data/` holds raw samples, processed outputs, and future reports
- `tests/` covers the current ingest and normalization behavior

This modularity is practical. Ingestion, normalization, storage, and later analysis stages will evolve at different speeds. Keeping those seams explicit makes the code easier to test, easier to extend, and easier for a collaborator to review quickly.

## Next Planned Stages

The current implementation stops after ingestion and normalization. The next planned stages are:

- **Template extraction**: group normalized lines into recurring event shapes
- **Scoring**: rank unusual templates or time windows using simple heuristic signals
- **Incidents**: cluster related suspicious windows into draft incidents
- **Reporting**: render concise evidence-backed summaries for human review

Those stages are already represented in the repository structure, but they are not the focus of the current implementation yet.

## Why This Structure Also Works As A Research Artifact

The current codebase is useful beyond the immediate engineering workflow because it creates clean interfaces between stages:

- raw input and structured records are separated
- normalization rules are explicit and inspectable
- persisted outputs are queryable in DuckDB
- later components can be evaluated against stable intermediate artifacts

That matters for research and collaboration. A professor or collaborator should be able to skim the repository and see a clear progression:

1. make logs usable
2. define stable intermediate representations
3. add stronger grouping and ranking methods later
4. evaluate improvements stage by stage instead of treating the system as a black box

This is the main reason ClusterSage stays modular. The engineering tool and the research artifact benefit from the same discipline: explicit data flow, readable heuristics, and inspectable outputs.
