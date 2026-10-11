# Cost and latency

Numbers below are from the three live traces run on 2026-10-11 at about 15:16 UTC. The script called local Ollama `gemma3:12b` at `host.docker.internal:11434`. N = 3. No step was retried, so each total is the first attempt through the final result.

The ceilings were written before the code: 5 seconds for a person watching a screen, 10 minutes for an overnight batch, and `$0.00` per case because this model is local.

## Per case

| Case | Intake ms | Enrichment ms | Risk ms | Recommendation ms | Total ms | Tokens | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| APP-1001 | 5742 | 3483 | 2396 | 2819 | 14440 | 1472 | $0.00 |
| APP-1002 | 4190 | 3409 | 2310 | 2706 | 12615 | 1473 | $0.00 |
| APP-1003 | 4082 | 3366 | 2289 | 2674 | 12411 | 1471 | $0.00 |

Token totals are input plus output for all four agents. Cost is those tokens times the pinned local rate of `$0` per million. This is the actual API bill. A hosted model would use a different rate.

## What the wait shows

Sorted case times are 12411 ms, 12615 ms, and 14440 ms. The middle value is 12615 ms. The longest case is 14440 ms.

Intake is the slowest agent in every case. Its longest visit is 5742 ms, on APP-1001.

Every case is longer than the 5-second real-time ceiling. Every case is far under the 10-minute batch ceiling. This pipeline fits an overnight batch. It does not fit a person waiting on a screen.

## What three cases do not show

Three cases show direction only. They do not support a production percentage. They also contain no retries, so they do not show what a timeout would add to the bill or the wait.
