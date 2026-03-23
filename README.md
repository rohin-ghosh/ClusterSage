# ClusterSage

ClusterSage is a Python log-triage project for distributed compute environments, with an initial focus on GPU-cluster style systems. Its first job is straightforward: take messy, high-volume, multi-source logs and turn them into something legible and useful for human debugging. The system is meant to ingest raw logs, preserve source evidence, normalize unstable tokens, extract recurring event templates, identify suspicious windows, and prepare concise reports that help an engineer decide what to inspect next.

The first version is intentionally narrow. ClusterSage is not a root-cause engine, not an autonomous debugging system, and not a replacement for engineering judgment. It is a pipeline for turning unstable, repetitive, high-volume logs into structured evidence: normalized events, recurring templates, suspicious windows, and concise reports that stay tied to the source data.

This repository is meant to be useful in two settings:

- as a working engineering tool for local incident or run analysis
- as a clean starting point for later research in log parsing, anomaly detection, and incident triage

## Problem Statement

Logs from distributed systems are often hard to use in their raw form. The underlying issues are familiar:

- the same event appears with small textual variations
- identifiers such as UUIDs, hostnames, ports, paths, job IDs, and device IDs create token churn
- important signals are buried inside repeated boilerplate
- events may span multiple hosts, services, or devices
- timestamps and metadata can be incomplete, inconsistent, or only partially reliable

In GPU and interconnect-heavy environments, this gets worse. A single problem may leave traces in node-level logs, framework logs, scheduler output, transport messages, and device-related diagnostics. Even when the evidence is present, it is difficult to read as a coherent incident.

ClusterSage exists to improve that first step. Before detection becomes sophisticated, the data has to become usable.

## Primary Goal

The first goal of ClusterSage is simple and concrete:

1. ingest messy logs from a run or incident directory
2. preserve raw evidence
3. normalize unstable tokens and repeated textual noise
4. extract recurring event shapes
5. identify windows that look worth inspecting
6. present the result in a form a human can work with

The system is therefore optimized first for legibility, traceability, and practical debugging value.

## MVP Definition

The MVP is a batch-oriented log triage pipeline. It should help answer questions such as:

- What happened repeatedly during this run?
- Which messages are structurally the same but differ only in unstable fields?
- Which time windows look unusual or dense with suspicious activity?
- What evidence should a human inspect first?

The MVP does not need to solve diagnosis. It needs to reduce raw log volume into a smaller, more interpretable set of patterns and candidate incidents.

## MVP Pipeline

The intended `v0.1` pipeline is:

1. **Ingest**
  Load raw files from a run directory and preserve source provenance such as file path, line number, host, and component where available.
2. **Parse**
  Convert lines into a lightweight structured record when possible while keeping the original text intact.
3. **Normalize**
  Replace unstable fields such as UUIDs, addresses, counters, ports, durations, and file paths with canonical placeholders so similar events become comparable.
4. **Template Extraction**
  Group normalized records into recurring event templates. At this stage, the point is not theoretical novelty; it is to collapse repetitive log variation into readable event classes.
5. **Scoring**
  Apply simple heuristics such as rarity, burstiness, and novelty within the local run. These scores are not final diagnoses. They are ranking signals to focus attention.
6. **Windowing and Incident Grouping**
  Aggregate suspicious events into time windows, then cluster related windows into draft incidents.
7. **Reporting**
  Render an evidence-backed summary that shows what was observed, where it came from, and why it was surfaced.

The pipeline is deliberately conservative. It should prefer explicit evidence over aggressive interpretation.

## Design Principles

- Preserve raw evidence alongside transformed forms.
- Keep heuristics simple enough to inspect and revise.
- Favor deterministic processing where possible.
- Separate data preparation from interpretation.
- Make each stage useful on its own.
- Avoid hidden coupling between ingestion, normalization, scoring, and reporting.

These principles matter because this project is intended to support both day-to-day engineering use and later experimental work.

## Why The Architecture Is Modular

ClusterSage is organized into narrow modules because the problem naturally decomposes into stages with different responsibilities and different rates of change.

- `app/ingest/` handles file discovery, line loading, and run metadata.
- `app/normalize/` handles token replacement and canonicalization rules.
- `app/templates/` handles recurring event extraction and similarity logic.
- `app/scoring/` handles heuristic ranking of events and windows.
- `app/incidents/` handles grouping and summarization of suspicious regions.
- `app/report/` handles presentation, not analysis.
- `app/models/` defines stable record shapes and persistence boundaries.
- `app/core/` holds configuration, constants, and logging concerns.

This modularity is practical, not decorative.

It keeps the early implementation readable. It allows normalization rules to change without rewriting scoring. It allows different template extraction approaches to be compared without disturbing ingestion. It allows reports to evolve independently from the logic that produces evidence. Most importantly, it makes the project easier for another engineer, collaborator, or reviewer to inspect without reconstructing the entire system from one large pipeline script.

## High-Level System View

```text
raw logs
  -> ingest
  -> parse into records
  -> normalize unstable tokens
  -> extract recurring templates
  -> score suspicious events and windows
  -> group candidate incidents
  -> render evidence-backed reports
```

DuckDB is included as the local analytical store so intermediate artifacts can be queried without introducing unnecessary infrastructure. Typer provides a simple CLI for local workflows. FastAPI provides a minimal service surface for status endpoints and future orchestration. Jinja2 supports report rendering without coupling output generation to analysis logic.

## Scope For v0.1

In scope:

- repository scaffold and module boundaries
- basic CLI and API entrypoints
- Pydantic models and configuration loading
- DuckDB connection layer
- YAML-driven placeholders for normalization and scoring configuration
- report templates
- test scaffolding for the core stages
- notebook space for controlled exploratory work

Out of scope:

- autonomous debugging or remediation
- production streaming ingestion
- learned anomaly models
- full causal diagnosis
- deep GPU-specific interpretation logic
- complex orchestration and deployment concerns
- broad platform or multi-tenant service design

The first version should be judged by whether it makes logs easier to use, not by whether it claims to solve debugging end-to-end.

## Research Value And Future Evolution

Although the MVP is an engineering tool first, the structure is meant to support research-grade iteration later.

Possible research directions include:

- evaluation of different template extraction strategies
- comparison of normalization schemes across noisy infrastructure logs
- weakly supervised or semi-supervised scoring methods
- incident clustering methods for multi-host or multi-device traces
- domain-specific analysis for GPU fabric, transport, or distributed training failures

This is why the project keeps explicit seams between stages. A stronger parser, a different template miner, a learned ranking layer, or a domain-specific GPU analysis component should be addable without redesigning the entire repository.

For a collaborator or professor skimming the codebase, the intended progression is straightforward:

1. establish a reliable baseline pipeline for making logs legible
2. instrument and evaluate each stage independently
3. swap heuristic components with stronger experimental methods where justified
4. preserve a usable engineering tool even as the research layer becomes more ambitious

That dual-use design is intentional. The repository should remain useful even if the research direction changes.

## Repository Layout

```text
clustersage/
├── README.md
├── pyproject.toml
├── .env.example
├── data/
│   ├── raw/
│   │   └── sample_run/
│   ├── processed/
│   └── reports/
├── configs/
│   ├── default.yaml
│   ├── normalization.yaml
│   └── scoring.yaml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── cli.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── constants.py
│   ├── models/
│   │   ├── schemas.py
│   │   ├── db.py
│   │   └── entities.py
│   ├── ingest/
│   │   ├── loader.py
│   │   ├── parsers.py
│   │   └── metadata.py
│   ├── normalize/
│   │   ├── rules.py
│   │   ├── tokenizer.py
│   │   └── canonicalize.py
│   ├── templates/
│   │   ├── extractor.py
│   │   ├── drain_like.py
│   │   └── similarity.py
│   ├── scoring/
│   │   ├── rarity.py
│   │   ├── burst.py
│   │   ├── novelty.py
│   │   ├── windows.py
│   │   └── ranker.py
│   ├── incidents/
│   │   ├── cluster.py
│   │   ├── summarize.py
│   │   └── evidence.py
│   ├── report/
│   │   ├── render_html.py
│   │   ├── render_markdown.py
│   │   └── templates/
│   │       └── report.html.j2
│   ├── llm/
│   │   ├── client.py
│   │   ├── prompts.py
│   │   └── guardrails.py
│   └── utils/
│       ├── time.py
│       ├── files.py
│       └── text.py
├── tests/
│   ├── test_ingest.py
│   ├── test_normalize.py
│   ├── test_templates.py
│   ├── test_scoring.py
│   └── test_incidents.py
└── notebooks/
    └── exploratory.ipynb
```

## Getting Started

The repository currently contains the project scaffold and placeholder modules.

```bash
cd clustersage
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
clustersage --help
uvicorn app.main:app --reload
```

## Current Status

ClusterSage is at the scaffold stage. The codebase currently defines repository structure, module boundaries, configuration stubs, and placeholder interfaces. The next implementation work is to make the ingestion, normalization, and template stages functional while keeping the outputs inspectable and evidence-preserving.