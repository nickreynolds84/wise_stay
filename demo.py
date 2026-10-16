import argparse
import json
from travel_ai.local import LocalAI, compatibility, install_model, load_catalog, system_info

parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["system", "check", "install", "infer"])
parser.add_argument("--model", default="candidate-model")
parser.add_argument("--catalog", default="catalog.json")
parser.add_argument("--model-path")
args = parser.parse_args()

if args.action == "system":
    print(json.dumps(system_info(), indent=2))
elif args.action == "check":
    model = load_catalog(args.catalog)[args.model]
    print(json.dumps(compatibility(model), indent=2))
elif args.action == "install":
    print(install_model(args.model, args.catalog))
elif args.action == "infer":
    if not args.model_path:
        parser.error("--model-path is required for inference")
    ai = LocalAI(args.model_path)
    result = ai.generate_json(
        "Return a JSON object with key 'attractions' containing an array of attraction names. "
        "Treat suggestions as unverified candidates; do not fabricate coordinates.",
        "Suggest up to 5 noteworthy physical theater attractions in Manhattan, New York City.")
    print(json.dumps(result, indent=2))
