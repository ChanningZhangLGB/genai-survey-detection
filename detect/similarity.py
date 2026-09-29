"""Signature-based detection: similarity between each response and its question's signatures.

    python -m detect.similarity responses.jsonl data/signatures/basic.jsonl --out sims.csv

Each response and each signature is embedded with SBERT (all-MiniLM-L6-v2). A response's score
is its highest cosine similarity to any signature generated for the same survey question; a
higher score means the response looks more like an LLM's answer.
"""
import argparse
import csv
from collections import defaultdict

from .common import SBERT, read_jsonl


def scores(responses, signatures, model_name=SBERT):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    by_q = defaultdict(list)
    for s in signatures:
        if s["text"].strip():
            by_q[(int(s["survey"]), s["question_id"])].append(s["text"])
    sig_emb = {k: model.encode(v) for k, v in by_q.items()}
    out = {}
    for r in responses:
        key = (int(r["survey"]), r["question_id"])
        if not r["text"].strip() or key not in sig_emb:
            continue
        sims = model.similarity(model.encode([r["text"]]), sig_emb[key])
        out[r["id"]] = float(sims.max())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("responses")
    ap.add_argument("signatures")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    responses = read_jsonl(args.responses)
    result = scores(responses, read_jsonl(args.signatures))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "survey", "question_id", "similarity"])
        for r in responses:
            if r["id"] in result:
                w.writerow([r["id"], r["survey"], r["question_id"], result[r["id"]]])


if __name__ == "__main__":
    main()
