from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_DIMENSIONS_PATH = Path(__file__).resolve().parent.parent / "resources" / "dimensions.json"


class DimensionScore(BaseModel):
    result: Literal["pass", "borderline", "fail"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class ScoreResults(BaseModel):
    utility: DimensionScore
    fairness: DimensionScore
    privacy: DimensionScore
    explainability: DimensionScore
    safety: DimensionScore


class ScoreSummary(BaseModel):
    passed: int
    borderline: int
    failed: int


class ScoreResponse(BaseModel):
    content: str
    model: str
    results: ScoreResults
    summary: ScoreSummary


def load_dimensions(dimensions_path: Path) -> dict:
    if not dimensions_path.exists():
        raise FileNotFoundError(f"dimensions.json not found at: {dimensions_path}")

    with dimensions_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required = {"utility", "fairness", "privacy", "explainability", "safety"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"dimensions.json missing required dimensions: {sorted(missing)}")

    return data


def build_messages(content: str, dimensions: dict) -> list[dict]:
    rubric_json = json.dumps(dimensions, indent=2)

    system_prompt = (
        "You are an expert evaluator for the Ethics Filter Framework (EFF). "
        "Assess the provided content against the supplied rubric. "
        "For each dimension, use the rubric and scoring_notes to assign one result: pass, borderline, or fail. "
        "Be conservative when information is missing or unclear. "
        "If justification for pass is not explicit, prefer borderline. "
        "Return only structured output as specified."
    )

    user_prompt = (
        "Evaluate the following content using the EFF rubric (JSON below).\n\n"
        "CONTENT:\n"
        f"{content}\n\n"
        "RUBRIC:\n"
        f"{rubric_json}\n\n"
        "Instructions:\n"
        "- For each dimension, use the rubric and scoring_notes to guide your judgment.\n"
        "- Do not invent details not present in the content.\n"
        "- Confidence must be a float between 0.0 and 1.0.\n"
        "- Reason must be brief, specific, and defensible.\n"
        "- Output must be valid JSON matching the expected schema."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    kwargs = {"api_key": api_key}
    if DEFAULT_BASE_URL:
        kwargs["base_url"] = DEFAULT_BASE_URL

    return OpenAI(**kwargs)


def call_model(content: str, dimensions: dict, model: str = DEFAULT_MODEL) -> ScoreResponse:
    client = build_client()
    messages = build_messages(content, dimensions)

    response = client.responses.parse(
        model=model,
        input=messages,
        text_format=ScoreResults,
    )

    parsed = response.output_parsed
    if parsed is None:
        raise ValueError("Model returned no parsed structured output.")

    summary = ScoreSummary(
        passed=sum(1 for x in parsed.model_dump().values() if x["result"] == "pass"),
        borderline=sum(1 for x in parsed.model_dump().values() if x["result"] == "borderline"),
        failed=sum(1 for x in parsed.model_dump().values() if x["result"] == "fail"),
    )

    return ScoreResponse(
        content=content,
        model=model,
        results=parsed,
        summary=summary,
    )


def score_story(
    content: str,
    dimensions_path: Path = DEFAULT_DIMENSIONS_PATH,
    model: str = DEFAULT_MODEL,
) -> dict:
    dimensions = load_dimensions(dimensions_path)
    result = call_model(content=content, dimensions=dimensions, model=model)
    return result.model_dump()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EFF scorer on a user story.")
    parser.add_argument(
        "content",
        nargs="?",
        default="As a user I want recommendations so I can find content.",
        help="The content or user story to score.",
    )
    parser.add_argument(
        "--dimensions",
        default=str(DEFAULT_DIMENSIONS_PATH),
        help="Path to dimensions.json",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name to use",
    )

    args = parser.parse_args()

    try:
        result = score_story(
            content=args.content,
            dimensions_path=Path(args.dimensions),
            model=args.model,
        )
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        json_output = json.dumps({"error": error}, indent=2)
        print(json_output)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
