# State and memory design

## Choice

This pipeline uses message passing. One in-memory queue sits between each step:

1. Intake finishes and puts a message on `application_received`.
2. Enrichment pulls that message, then puts a message on `enrichment_complete`.
3. Risk scoring pulls that message, then puts a message on `risk_assessed`.
4. Recommendation pulls that message and sets the final word.

No agent calls the next one directly. No agent opens a shared case file. Memory is this application only. When the run ends, every queue is empty. The next applicant starts with a new message.

## Why

Shared state is often simpler to set up initially but riskier, since any agent can accidentally read or write something it shouldn't. Message passing enforces cleaner boundaries between agents' responsibilities, at the cost of more explicit plumbing between each handoff.

The queues are that plumbing. A later step cannot start until the previous step has placed a finished message.

## What this avoids

**Stale data.** A step starts only after it pulls a finished message. Risk scoring cannot run while enrichment is still empty, because that message has not been queued yet.

**Context bleed.** Each run builds its own messages. One applicant's name, age, amount, and score stay on that applicant's messages. Nothing is kept in a global list.

**Unbounded growth.** One message carries one case, then the queues are emptied. Past applications are not appended into the next prompt.

## What each agent reads and writes

| Agent | Reads | Writes | Does not see |
|---|---|---|---|
| Intake | The raw form only: `applicant_id`, `full_name`, `age`, `coverage_amount` | A clean application, plus any missing fields | Enrichment, the score, the decision |
| Enrichment | The intake message, plus matching rows in `data/applicant_records.json` | That application plus extra facts copied from the file | A shared case file, the score, the decision |
| Risk scoring | The enrichment message only | A score from 0 to 1, reasons, and the extra facts copied forward | The records file, the decision |
| Recommendation | The risk message only | `approve`, `deny`, or `refer`, plus a reason written by the model | Any field that was not on the risk message |

A fact that is not in the records file is not added. An unknown applicant id produces an empty fact list.

## Decision rule

Code sets the final word. The model writes the reason.

1. A `prior_claim` on the risk message means `refer`. A prior claim means this person has filed an insurance claim before.
2. A `hazardous_occupation` on the risk message means `refer`. That is a job with a higher chance of a claim, so a person reviews it.
3. A `recent_lapse` on the risk message means `deny`, including when the score is `0.7` or higher. A lapsed policy is not approved.
4. A timeout or a failed check after one retry means `refer`. No score is invented.
5. Otherwise a score of `0.7` or higher means `approve`, and a score below `0.7` means `deny`.

`0.7` is `APPROVE_AT` in config. It can be changed there.

## Budgets, written before code

| Budget | Ceiling |
|---|---|
| Real-time, a person watching a screen | 5 seconds per case |
| Overnight batch | 10 minutes per case |
| Cost | `$0.00` per case, because the model is local |

Three traces later will be compared with these ceilings. Three cases show direction only. They do not prove a production rate.
