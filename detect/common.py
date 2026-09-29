"""Shared constants, file helpers and the OpenAI client."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
DATA = ROOT / "data"
RESULTS = ROOT / "results"

# The four dated snapshots used in the paper.
MODELS = ["gpt-3.5-turbo-0125", "gpt-4-0613", "gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18"]
MODEL_NAMES = {"gpt-3.5-turbo-0125": "GPT-3.5-Turbo", "gpt-4-0613": "GPT-4",
               "gpt-4o-2024-08-06": "GPT-4o", "gpt-4o-mini-2024-07-18": "GPT-4o-Mini"}

# Five temperatures x four models = 20 signatures per question (basic prompt).
TEMPERATURES = [0, 0.25, 0.5, 0.75, 1]
# The sentiment-based prompt repeats that grid once per sentiment: 60 signatures per question.
SENTIMENTS = ["positive", "neutral", "negative"]

SBERT = "all-MiniLM-L6-v2"

# Surveys run before ChatGPT's release (Nov 2022) are treated as free of AI-generated text.
PRE_2022 = [1, 2, 3, 4]
POST_2022 = [5, 6, 7]


def prompt(name):
    return (PROMPTS / f"{name}.txt").read_text(encoding="utf-8")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def client():
    """OpenAI client; the key comes from the OPENAI_API_KEY environment variable."""
    from openai import OpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment first.")
    return OpenAI()


def chat(cli, model, text, temperature):
    completion = cli.chat.completions.create(
        model=model, temperature=temperature, messages=[{"role": "user", "content": text}])
    return completion.choices[0].message.content.strip()
