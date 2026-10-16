import json
from pathlib import Path
from time import perf_counter

from llama_cpp import Llama

from attraction_matcher import (
    load_overture_theaters,
    validate_attraction,
)

# ============================================================
# 1. MODEL CONFIGURATION
# ============================================================

MODEL_DIRECTORY = Path("models/qwen3-4b")

model_files = list(MODEL_DIRECTORY.rglob("*.gguf"))

if len(model_files) != 1:
    raise RuntimeError(
        f"Expected exactly one GGUF model in {MODEL_DIRECTORY}, "
        f"but found {len(model_files)}."
    )

model_path = model_files[0]

print(f"\nUsing model: {model_path}")
print("Loading Qwen model...")

start = perf_counter()

llm = Llama(
    model_path=str(model_path),
    n_ctx=4096,
    n_gpu_layers=-1,
    verbose=False,
)

load_time = perf_counter() - start

print(f"Model initialization: {load_time:.2f}s")


# ============================================================
# 2. STRUCTURED OUTPUT SCHEMA
# ============================================================

schema = {
    "type": "object",
    "properties": {
        "destination": {"type": "string"},
        "activity": {"type": "string"},
        "attractions": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "significance": {
                        "type": "string",
                        "enum": ["major_destination", "noteworthy", "local_interest"],
                    },
                    "reason": {"type": "string"},
                },
                "required": ["name", "aliases", "significance", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["destination", "activity", "attractions"],
    "additionalProperties": False,
}


# ============================================================
# 3. ATTRACTION DISCOVERY PROMPT
# ============================================================

prompt = """
Destination: Manhattan, New York City
Activity: Theater and Broadway

Identify 3 to 5 noteworthy physical theater buildings
or performance venues in Manhattan.

Do not include:
- Broadway shows or productions
- Theater companies without a specific venue
- Ticket vendors
- Fictional or invented venues

Use current venue names where known.
Include former names only as aliases.

Provide a brief reason for each venue's significance.

Do not provide addresses, coordinates, or opening dates.
"""


# ============================================================
# 4. RUN MODEL INFERENCE
# ============================================================

print("\nGenerating noteworthy attractions...")

start = perf_counter()

response = llm.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": (
                "You identify noteworthy travel attractions. "
                "Return only the requested structured data. "
                "Do not invent venues."
            ),
        },
        {"role": "user", "content": prompt},
    ],
    response_format={"type": "json_object", "schema": schema},
    temperature=0.1,
    max_tokens=700,
)

inference_time = perf_counter() - start

content = response["choices"][0]["message"]["content"]

if not content:
    raise RuntimeError("Model returned an empty response.")

try:
    result = json.loads(content)

    output_path = Path("data/generated")
    output_path.mkdir(parents=True, exist_ok=True)

    with open(
        output_path / "manhattan_theater_candidates.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(result, f, indent=2)
except json.JSONDecodeError as exc:
    raise RuntimeError(f"Model returned invalid JSON:\n{content}") from exc

if not isinstance(result, dict):
    raise RuntimeError("Model response must be a JSON object.")

attractions = result.get("attractions")

if not isinstance(attractions, list):
    raise RuntimeError("Model response does not contain an attractions list.")

print("\nMODEL-GENERATED ATTRACTIONS\n")
print(json.dumps(result, indent=2))

print(f"\nInference time: {inference_time:.2f}s")


# ============================================================
# 5. LOAD OVERTURE DATA
# ============================================================

print("\nLoading Overture theater data...")

start = perf_counter()

overture_df = load_overture_theaters()

overture_load_time = perf_counter() - start

print(f"Overture records loaded: {len(overture_df.pois)}")
print(f"Overture load time: {overture_load_time:.2f}s")


# ============================================================
# 6. VALIDATE MODEL ATTRACTIONS AGAINST OVERTURE
# ============================================================

print("\n" + "=" * 60)
print("ATTRACTION VALIDATION RESULTS")
print("=" * 60)

validation_results = []

for attraction in attractions:

    validation = validate_attraction(
        attraction,
        overture_df,
    )

    validation_results.append(validation)

    print(f"\nLLM attraction: {attraction['name']}")
    print(f"Status: {validation['status'].upper()}")
    print(f"Reason: {validation['reason']}")

    candidates = validation.get("candidates", [])

    if not candidates:
        print("  No matching Overture candidates found.")
        continue

    print("  Top Overture matches:")
    for candidate in candidates[:3]:
        print(
            f"    {candidate['overture_name']}"
            f" | Similarity: {candidate['similarity']:.1f}"
            f" | Category: {candidate['category']}"
            f" | Matched name: {candidate['matched_overture_name']}"
        )


# ============================================================
# 7. VALIDATION SUMMARY
# ============================================================

accepted = [item for item in validation_results if item["status"] == "accepted"]

review = [item for item in validation_results if item["status"] == "review"]

rejected = [item for item in validation_results if item["status"] == "rejected"]

print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

print(f"Total LLM attractions: {len(attractions)}")
print(f"Accepted: {len(accepted)}")
print(f"Needs review: {len(review)}")
print(f"Rejected: {len(rejected)}")

print("\nValidated attractions:")

if accepted:
    for item in accepted:
        match = item["best_match"]

        print(
            f"  {item['attraction']} "
            f"-> {match['overture_name']} "
            f"({match['similarity']:.1f})"
        )
else:
    print("  None")


# ============================================================
# 8. PERFORMANCE SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("PERFORMANCE SUMMARY")
print("=" * 60)

print(f"Model initialization: {load_time:.2f}s")
print(f"Model inference: {inference_time:.2f}s")
print(f"Overture loading: {overture_load_time:.2f}s")
