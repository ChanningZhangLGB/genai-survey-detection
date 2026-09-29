"""Signature generation: ask LLMs to answer the survey questions themselves.

    python -m detect.signatures data/questions.json --strategy basic --out sigs.jsonl
    python -m detect.signatures data/questions.json --strategy sentiment --out sigs.jsonl

basic      the question alone is the prompt: 4 models x 5 temperatures = 20 signatures.
sentiment  the question is asked to be answered positively, neutrally and negatively:
           3 x 4 x 5 = 60 signatures.

Input: a JSON list of {"survey", "question_id", "question"}. Output: JSONL with one signature
per line, in the same format as data/signatures/*.jsonl.
"""
import argparse
import json

from .common import MODELS, SENTIMENTS, TEMPERATURES, chat, client, prompt, write_jsonl


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("questions")
    ap.add_argument("--strategy", choices=["basic", "sentiment"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="+", default=MODELS)
    args = ap.parse_args()

    questions = json.load(open(args.questions, encoding="utf-8"))
    cli = client()
    out = []
    for q in questions:
        variants = ({None: prompt("signature_basic").format(question=q["question"])}
                    if args.strategy == "basic" else
                    {s: prompt(f"signature_sentiment_{s}").format(question=q["question"])
                     for s in SENTIMENTS})
        for sentiment, text in variants.items():
            for m in args.models:
                for t in TEMPERATURES:
                    row = {"survey": q["survey"], "question_id": q["question_id"]}
                    if sentiment:
                        row["sentiment"] = sentiment
                    row.update(model=m, temperature=str(t), text=chat(cli, m, text, t))
                    out.append(row)
    write_jsonl(out, args.out)


if __name__ == "__main__":
    main()
