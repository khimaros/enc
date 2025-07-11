#!/usr/bin/env python
# NOTICE: this file was automatically generated by https://github.com/khimaros/enc using the following invocation:
# ./enc-release scripts/pricing.en -o scripts/pricing.py --context-files ./res/pricing.json:requirements.txt

import json
import json5
import pathlib
import urllib.request

# the source url is: https://raw.githubusercontent.com/Aider-AI/aider/refs/heads/main/aider/resources/model-metadata.json
SOURCE_URL = "https://raw.githubusercontent.com/Aider-AI/aider/refs/heads/main/aider/resources/model-metadata.json"

# the resulting data should be written to ./res/pricing.json
OUTPUT_PATH = pathlib.Path(__file__).parent.parent / "res/pricing.json"

# those objects have many keys, but will be filtered to have only the following ones:
ALLOWED_KEYS = {
    "max_tokens",
    "max_input_tokens",
    "input_cost_per_token",
    "input_cost_per_token_above_200k_tokens",
    "output_cost_per_token",
    "output_cost_per_token_above_200k_tokens",
    "source",
}

# the following data should also be added:
CUSTOM_DATA = {
    "anthropic/claude-sonnet-4-20250514": {
        "input_cost_per_token": 3e-06,
        "max_input_tokens": 200000,
        "max_tokens": 8192,
        "output_cost_per_token": 1.5e-05,
    },
}


def fetch_source_data(url):
    """fetches data from the given url."""
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def process_models(source_data):
    """parses and transforms the source model data."""
    # with python, json5 should be used to parse the source data.
    models = json5.loads(source_data)
    processed_data = {}

    # the base JSON is an object and the keys are of the form "<provider>/<model>"
    for key, data in models.items():
        # if there is an extra "openrouter/" prefix, it should be removed.
        key = key.removeprefix("openrouter/")

        # if no provider is specified, that entire object should be skipped.
        if "/" not in key:
            continue

        provider, model_name = key.split("/", 1)

        # where provider is "gemini", it will be replaced with "google"
        if provider == "gemini":
            provider = "google"

        new_key = f"{provider}/{model_name}"
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_KEYS}

        if filtered_data:
            processed_data[new_key] = filtered_data

    return processed_data


def write_pricing_data(path, data):
    """writes the final pricing data to a json file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)
        f.write("\n")
    print(f"pricing data successfully written to {path}")


def main():
    """main script execution."""
    print(f"downloading pricing data from {SOURCE_URL}...")
    source_text = fetch_source_data(SOURCE_URL)

    print("processing model data...")
    pricing_data = process_models(source_text)
    pricing_data.update(CUSTOM_DATA)

    write_pricing_data(OUTPUT_PATH, pricing_data)


if __name__ == "__main__":
    main()