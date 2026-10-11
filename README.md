# Multi-agent underwriting

An insurance application moves through four steps: intake, enrichment, risk scoring, and a final decision of approve, deny, or refer. Each step is a separate function. They pass a finished message through in-memory queues.

## How to run it

### Local (Python)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
OLLAMA_HOST=http://host.docker.internal:11434 .venv/bin/python scripts/run_three_cases.py
```

`OLLAMA_HOST` defaults to `http://localhost:11434`. Inside this container, Ollama is on the host, so use the `host.docker.internal` address above. The model is `gemma3:12b`.

The timeout demo does not call Ollama:

```bash
.venv/bin/python scripts/run_failure_case.py
```

There is no Docker image and no cloud deploy.

## How to test it

Same checks as GitHub Actions:

```bash
.venv/bin/python -m pytest tests/
.venv/bin/python -m flake8 src tests
.venv/bin/python -m mypy src
```

Unit tests use a fake model. They do not need Ollama.

## Configuration

| Name | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Where the live model runs |
| `APPROVE_AT` in `src/underwriting/config.py` | `0.7` | Score at or above this is approve, unless a prior claim or a hazardous occupation says refer, a recent lapse says deny, or a failed retry says refer |
| `TIMEOUT_APPLICANT_ID` | `APP-TIMEOUT` | This id makes risk scoring time out before any network call |

## Known limitations

- The queues live in memory and are empty when the run ends. They are not a broker.
- Enrichment reads only `data/applicant_records.json`. There is no database.
- Cost is `$0.00` per case because the model is local. A hosted model would bill differently.
- Three live cases show direction only. They are not a production accuracy rate.
- A person waiting on a screen needs an answer in 5 seconds. These cases took about 12 to 15 seconds, so the pipeline fits an overnight batch.
