# Data

Everything needed to rebuild the paper's tables and figure, without the survey responses
themselves. The collected answers are human-subject data from studies run under their own
consent terms (three of them by researchers outside the author team, two still unpublished), so
they are not redistributed. Each response is identified by a pseudonymous id instead.

| File | Rows | Contents |
|---|--:|---|
| `questions.json` | 24 | The open-ended survey questions of surveys #2 to #7 that signatures were generated for |
| `signatures/basic.jsonl` | 480 | Basic-prompt signatures: 4 models x 5 temperatures per question |
| `signatures/sentiment.jsonl` | 1,440 | Sentiment-based signatures: 3 sentiments x 4 models x 5 temperatures per question |
| `zero_shot_labels.csv` | 3,326 | LLM-based detection: each model's label per response, surveys #1 to #7 |
| `similarity_scores.csv` | 2,528 | Signature-based detection: best similarity per response, surveys #2 to #7 |

## Formats

**`questions.json`**: `survey` (1 to 7, as numbered in the paper), `question_id`, `question`.

**`signatures/*.jsonl`**: `survey`, `question_id`, `model`, `temperature`, `text`, plus
`sentiment` (`positive`, `neutral`, `negative`) in the sentiment file.

**`zero_shot_labels.csv`**: `id`, `survey`, `question_id`, and one column per model holding `1`
(labelled AI-generated), `0` (labelled human) or empty (the reply was not a bare 0 or 1).

**`similarity_scores.csv`**: `id`, `survey`, `question_id`, and three scores:

| Column | Meaning |
|---|---|
| `sim_basic` | Basic-prompt score as used for the paper's Table 3 and Figure 2 (see the note below) |
| `sim_basic_all20` | Basic-prompt score over all 20 signatures of the question |
| `sim_sentiment` | Sentiment-based score over all 60 signatures of the question |

**Ids.** `S<survey>-<question>-<nnnn>`, for example `S7-q1-0042`. Participant identifiers
(platform worker ids, response ids) were replaced during export, and the same response carries
the same id in both CSV files. Survey #1 has no per-question split, so its question field is
empty.

## Notes on the recorded data

- **`sim_basic` for surveys #2, #3, #4 and #7 covers 12 of the 20 signatures.** In the original
  analysis, the step that took the maximum over signatures matched temperature keys with the
  pattern `\d+\.\d+`, which skips temperatures `0` and `1`. For those four surveys the score is
  therefore the maximum over temperatures 0.25, 0.5 and 0.75 only; surveys #5 and #6 were scored
  over all 20. `sim_basic_all20` is the corrected score, and
  `python -m detect.evaluate --basic-column sim_basic_all20` rebuilds Table 3 from it.
- **The survey #7 questions carry leftover formatting codes** (for example `\'93\cf2`), copied
  from a rich-text file. The signatures for survey #7 were generated from these strings exactly
  as they appear in `questions.json`.
- **Response counts.** Survey #7 has 521 responses here and 520 in the paper's Table 1. Survey
  #5's zero-shot labels come from a run over all 1,166 responses.
