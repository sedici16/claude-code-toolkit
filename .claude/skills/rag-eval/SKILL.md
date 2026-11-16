---
name: rag-eval
description: Measure and improve a retrieval-augmented generation (RAG) or search system with a fixed test set and before/after numbers. Use when the user asks whether retrieval, ranking, a prompt or a chunking change made answers better or worse.
---

# Evaluate a RAG / search change

The rule: **no change is "better" without numbers on the same test set.**

## 1. Test set (create once, then freeze)
- 20–50 real questions in `eval/eval_set.json`, each with: `question`, the expected
  source (`doc` + `section`/`clause`/`page`), and one `must_contain` fact for the answer.
- Include 2–3 questions the corpus cannot answer: the correct behaviour is a refusal.
- Never edit the set to make a run look better. Add new cases in a new version.

## 2. Metrics to report every run
| Metric | Meaning |
|---|---|
| hit@1 / hit@5 | expected source is the top result / in the top 5 |
| answer correct | `must_contain` fact present (spot-check by hand) |
| refusals | unanswerable questions correctly refused |
| cost / latency | input + output tokens per question, seconds per question |

## 3. Procedure
1. Run the current system: this is the **baseline**. Save it to `eval/results/<date>-baseline.json`.
2. Change **one thing** (chunk size, hybrid weighting, re-ranker, prompt…).
3. Re-run on the same set and save it next to the baseline.
4. Report a before/after table and list the questions that changed (fixed and broken).
5. Keep the change only if it improves the target metric without breaking other cases.

## 4. Diagnosing a wrong answer
Check in this order and say which one failed:
1. **Retrieval**: was the right chunk in the top k at all?
2. **Ranking**: was it retrieved but ranked too low to be used?
3. **Generation**: was it in the context, but the answer ignored or misread it?
4. **Content**: is the information missing from the corpus?
