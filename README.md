# ClusterSage

## Status

Early prototype. Currently implements:  

- log discovery and ingestion  
- lightweight metadata extraction  
- timestamp/severity/component parsing  
- regex-based normalization  
- DuckDB persistence  
- Typer CLI  
- basic synthetic sample logs/tests

Next: template extraction, anomaly scoring, incident grouping, and agentic triage.

## Minimal Example

Raw log:

```text

2026-04-25 14:03:22 node03 [NCCL] WARN timeout connecting to 10.2.4.81:443 after 12000ms

Output:

{

  "timestamp": "2026-04-25T14:03:22",

  "host": "node03",

  "component": "NCCL",

  "severity": "WARN",

  "normalized_text": "<TIMESTAMP> node<INT> [NCCL] WARN timeout connecting to <IP>:<PORT> after <DURATION>"

}



ClusterSage is a small Python log-triage tool for distributed compute and GPU-cluster style environments. Its current job is focused and practical: ingest messy log files, normalize unstable tokens, store the resulting records in DuckDB, and run a lightweight benchmark harness so changes can be evaluated instead of guessed at.

It is not an autonomous debugging agent. It does not do incident diagnosis, anomaly detection, remediation, or LLM-assisted analysis. The project is intentionally kept narrow so one developer can understand the whole current system in one sitting.

## Current Scope

ClusterSage currently supports:

- recursive ingestion of `.log` and `.txt` files
- simple metadata inference from filenames such as `trainer_node03.log`
- timestamp, severity, and bracketed-component parsing when obvious
- regex-based normalization from `configs/normalization.yaml`
- DuckDB persistence for raw and normalized records
- lightweight evaluation of normalization and grouping baselines
- a Typer CLI for the two working commands: `ingest` and `benchmark`

Everything else is deliberately out of scope for now.

## Architecture

The active code is organized around the current working pipeline:

```text
app/
├── cli.py          # Typer commands for ingest and benchmark
├── config.py       # small settings/YAML helpers
├── schemas.py      # shared Pydantic records
├── storage.py      # DuckDB table creation and writes
├── ingest/         # file discovery, line parsing, metadata inference
├── normalize/      # YAML-driven regex normalization
└── eval/           # datasets, baselines, metrics, perturbation, reports
```

This is intentionally smaller than the original scaffold. Modules that only described future work, such as incidents, scoring, LLM integration, API routes, and report rendering, have been removed until there is real behavior to justify them.

## Ingestion

The ingest flow takes a directory or file path and:

1. finds `.log` and `.txt` files recursively
2. skips blank lines
3. infers `source` and `host` from simple filename patterns
4. parses common timestamp formats at the start of a line
5. infers `severity` and bracketed `component` labels when present
6. preserves the original line as `raw_text`
7. writes records to DuckDB after normalization

Example:

```bash
python -m app.cli ingest ./data/raw/sample_run --job-id run_042
```

Expected output includes:

- files processed
- log lines ingested
- normalized records written
- database path

## Canonical Record

Each ingested line is represented as a `LogRecord` with:

- `id`
- `timestamp`
- `source`
- `host`
- `job_id`
- `severity`
- `component`
- `line_number`
- `raw_text`
- `normalized_text`
- `file_path`

The schema is intentionally plain. It keeps the raw evidence and the normalized form together without pretending to solve higher-level debugging yet.

## Normalization

Normalization is the step that makes repeated event shapes easier to see. The current normalizer applies ordered regex rules from [configs/normalization.yaml](configs/normalization.yaml) and replaces unstable tokens with readable placeholders.

Examples of supported placeholders:

- `<IP>`
- `<UUID>`
- `<HEX>`
- `<DURATION>`
- `<FLOAT>`
- `<INT>`
- `<PATH>`
- `<ID>`

The goal is not to erase information. The raw line is always preserved, and `normalized_text` is used as a cleaner comparison surface for evaluation and later template work.

## Storage

Records are stored in DuckDB at:

```text
data/processed/clustersage.duckdb
```

The current database has one main table:

```text
log_records
```

This is enough for local inspection and avoids introducing service infrastructure before the tool needs it.

## Evaluation

The benchmark layer gives concrete feedback on preprocessing and grouping behavior. It exists because normalization quality can otherwise become too subjective.

Benchmark datasets can be either:

- local labeled datasets with `logs.txt` and `labels.json`
- synthetic sample-run logs with an optional `benchmark_manifest.json`

Seed dataset:

```text
data/benchmarks/sample_parser_eval/
├── logs.txt
└── labels.json
```

Run it with:

```bash
python -m app.cli benchmark ./data/benchmarks/sample_parser_eval
```

Run the synthetic sample logs with:

```bash
python -m app.cli benchmark ./data/raw/sample_run --mode synthetic
```

The benchmark currently reports:

- lines changed by normalization
- percent of lines changed
- replacement counts by normalization rule
- before/after examples
- exact template match rate when expected templates exist
- grouping pair accuracy when expected groups exist
- predicted vs expected template counts
- over-splitting and over-merging indicators
- concrete failure examples

Reports are written to:

```text
data/reports/benchmarks/
```

Each run writes a JSON report and a Markdown report.

## Setup

From the repository root:

```bash
cd clustersage
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Use `python -m ...` while developing so commands run inside the active virtual environment.

## Common Commands

Run ingestion:

```bash
python -m app.cli ingest ./data/raw/sample_run --job-id run_042
```

Run the benchmark:

```bash
python -m app.cli benchmark ./data/benchmarks/sample_parser_eval
```

Run tests:

```bash
python -m pytest
```

Inspect stored records:

```bash
python - <<'PY'
import duckdb

con = duckdb.connect("data/processed/clustersage.duckdb")
rows = con.execute("""
    select source, host, job_id, raw_text, normalized_text
    from log_records
    order by file_path, line_number
    limit 10
""").fetchall()

for row in rows:
    print(row)
PY
```

## What Comes Next

The next useful stage is not a bigger architecture. It is better behavior inside the small architecture:

- tune normalization so timestamps and useful structure are preserved
- improve simple grouping/template behavior
- add benchmark cases from real or public cluster logs
- compare changes through the existing benchmark reports

Incident clustering, scoring, richer reports, API work, and LLM support should wait until the preprocessing and evaluation layer is strong enough to justify them.