#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Tuple

# Load environment variables from .enc.env file
# You'll need to install this library: pip install python-dotenv
try:
    from dotenv import load_dotenv

    # Load global .enc.env file from user's home directory if it exists
    global_env_path = os.path.expanduser("~/.enc.env")
    if os.path.exists(global_env_path):
        load_dotenv(global_env_path)

    # Load local .enc.env file, overriding global settings if present
    load_dotenv(".enc.env", override=True)
except ImportError:
    print(
        "the 'python-dotenv' library is not installed. please run: pip install python-dotenv",
        file=sys.stderr,
    )
    # Continue without it, relying on system environment variables
    pass


# For interacting with LLMs
# You'll need to install these libraries:
# pip install openai google-generativeai
# OpenAI import is now conditional within get_llm_details

try:
    import google.generativeai as genai
except ImportError:
    print(
        "the 'google-generativeai' library is not installed. please install it by running: pip install google-generativeai",
        file=sys.stderr,
    )
    sys.exit(1)


# Language and extension mapping
LANGUAGE_TO_EXTENSION_MAP = {
    "python": "py",
    "c": "c",
    "c++": "cpp",
    "csharp": "cs",  # Added C# for completeness
    "java": "java",
    "javascript": "js",
    "typescript": "ts",
    "go": "go",
    "rust": "rs",
    "ruby": "rb",
    "php": "php",
    "swift": "swift",
    "kotlin": "kt",
    "html": "html",
    "css": "css",
    "bash": "sh",
    "shell": "sh",
    "sql": "sql",
    "perl": "pl",
    "scala": "scala",
}
EXTENSION_TO_LANGUAGE_MAP = {v: k for k, v in LANGUAGE_TO_EXTENSION_MAP.items()}
# Handle cases like .sh for both bash and shell, prioritizing one or making it specific.
# For now, the simple inversion is used. If multiple languages map to the same extension,
# the one that appears last in LANGUAGE_TO_EXTENSION_MAP will be chosen by this simple inversion.
# Or, more robustly:
EXTENSION_TO_LANGUAGE_MAP = {}
for lang, ext in LANGUAGE_TO_EXTENSION_MAP.items():
    if ext not in EXTENSION_TO_LANGUAGE_MAP:  # Prioritize first encountered
        EXTENSION_TO_LANGUAGE_MAP[ext] = lang


def load_pricing_data(file_path: str) -> dict:
    """Loads pricing data from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"error: pricing file '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(
            f"error: could not decode JSON from pricing file '{file_path}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"error reading pricing file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)


def get_llm_details(cli_model_override: str | None) -> Tuple[Any, str, str]:
    """
    Initializes and returns an LLM client, provider name, and model name
    based on environment variables and CLI overrides.
    """
    provider = os.getenv("PROVIDER", "google").lower()
    client: Any = None
    model_name: str = ""

    # Determine the model name: CLI override > MODEL env var > provider-specific default
    default_model_for_provider = {
        "openai": "gpt-3.5-turbo",
        "google": "gemini-2.5-pro",
    }
    model_name_from_env = os.getenv("MODEL")

    if cli_model_override:
        model_name = cli_model_override
    elif model_name_from_env:
        model_name = model_name_from_env
    else:
        model_name = default_model_for_provider.get(
            provider, "gpt-3.5-turbo"
        )  # Fallback if provider unknown

    if provider == "openai":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print(
                "error: OPENAI_API_KEY is not set in environment or .enc.env for openai provider.",
                file=sys.stderr,
            )
            sys.exit(1)
        base_url = os.getenv("OPENAI_API_BASE")
        # model_name is already set above
        try:
            from openai import OpenAI  # Import moved here

            client = OpenAI(
                api_key=openai_api_key, base_url=base_url if base_url else None
            )
        except ImportError:
            print(
                "the 'openai' library is not installed. please install it by running: pip install openai",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            print(f"error initializing openai client: {e}", file=sys.stderr)
            sys.exit(1)
    elif provider == "google":
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print(
                "error: GEMINI_API_KEY is not set in environment or .enc.env for gemini provider.",
                file=sys.stderr,
            )
            sys.exit(1)
        # model_name is already set above
        try:
            genai.configure(api_key=gemini_api_key)
            client = genai.GenerativeModel(model_name)
        except Exception as e:
            print(f"error initializing gemini client: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            f"error: unsupported PROVIDER '{provider}'. choose 'openai' or 'gemini'.",
            file=sys.stderr,
        )
        sys.exit(1)

    return client, provider, model_name


def transpile_english_to_code(
    english_content: str,
    target_language: str,
    output_path: str,
    llm_client: Any,
    provider: str,
    model: str,
    hacking_conventions_content: str,
    prompt_template_file_path: str,
    generation_command_str: str,
    context_files_str: str,
    seed: int | None = None,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
    log_file_path: str | None = None,
) -> Tuple[str, int, int, int, str]:
    """
    Uses the specified LLM to transpile English content to the target programming language,
    adhering to the provided style guide and using the specified prompt template.
    Returns the generated code, input units, output units, and the unit type ('tokens' or 'characters').
    """
    try:
        with open(prompt_template_file_path, "r", encoding="utf-8") as f:
            code_generation_prompt_template = f.read()
    except FileNotFoundError:
        print(
            f"error: prompt template file '{prompt_template_file_path}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(
            f"error reading prompt template file '{prompt_template_file_path}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # this performs a single-pass replacement of template variables.
    # this is to prevent recursive expansion if a variable's content
    # contains another variable's name.
    replacements = {
        "target_language": target_language,
        "english_content": english_content,
        "hacking_conventions": hacking_conventions_content,
        "generation_command": generation_command_str,
        "context_files": context_files_str,
        "output_path": output_path,
    }

    def replacer(match):
        key = match.group(1).strip()
        return replacements.get(key, match.group(0))

    prompt_content = re.sub(
        r"\{\{(.*?)\}\}", replacer, code_generation_prompt_template
    )

    generated_code = ""
    input_units, output_units = 0, 0
    thinking_units = 0
    unit_name = "tokens"  # Default unit

    try:
        if provider == "openai":
            system_message_content = (
                f"You are an expert programmer specializing in {target_language}."
            )
            user_message_content = prompt_content
            messages = [
                {"role": "system", "content": system_message_content},
                {"role": "user", "content": user_message_content},
            ]
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,  # Lower temperature for more deterministic code generation
            }
            if seed is not None:
                request_params["seed"] = seed
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            # thinking_budget is not a direct OpenAI API parameter, log if provided
            # request_params["thinking_budget"] = thinking_budget # Example if it were supported

            if log_file_path:
                try:
                    request_data_to_log = {
                        "provider": "openai",
                        "model": model,
                        "request_params": request_params,
                        "thinking_budget_requested": thinking_budget,  # Logged here
                    }
                    with open(log_file_path, "a", encoding="utf-8") as lf:
                        lf.write(
                            f"--- OPENAI REQUEST ---\n{json.dumps(request_data_to_log, indent=2)}\n\n"
                        )
                except Exception as log_e:
                    # Still attempt to log the error to the log file if possible
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(
                                f"--- OPENAI REQUEST LOGGING ERROR ---\nError: {str(log_e)}\n\n"
                            )
                    except:
                        pass  # Suppress errors during error logging itself

            completion = llm_client.chat.completions.create(**request_params)
            generated_code = completion.choices[0].message.content.strip()

            if log_file_path:
                try:
                    # OpenAI V1.x.x completion object has model_dump()
                    response_data_to_log = completion.model_dump(exclude_none=True)
                    with open(log_file_path, "a", encoding="utf-8") as lf:
                        lf.write(
                            f"--- OPENAI RESPONSE ---\n{json.dumps(response_data_to_log, indent=2)}\n\n"
                        )
                except Exception as log_e:
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(
                                f"--- OPENAI RESPONSE LOGGING ERROR ---\nError: {str(log_e)}\nOriginal completion object (partial string representation):\n{str(completion)[:1000]}...\n\n"
                            )
                    except:
                        pass

            if completion.usage:
                input_units = completion.usage.prompt_tokens
                output_units = completion.usage.completion_tokens
                unit_name = "tokens"
                if (
                    input_units == 0 and output_units == 0
                ):  # Potentially no usage reported
                    print(
                        "warning: openai reported 0 tokens for both input and output. falling back to character counts for usage.",
                        file=sys.stderr,
                    )
                    input_units = len(system_message_content) + len(
                        user_message_content
                    )
                    output_units = len(generated_code)
                    unit_name = "characters"
            else:
                print(
                    "warning: token usage information not available from openai. falling back to character counts.",
                    file=sys.stderr,
                )
                input_units = len(system_message_content) + len(user_message_content)
                output_units = len(generated_code)
                unit_name = "characters"

        elif provider == "google":
            generation_config_params = {}  # Initialize
            if seed is not None:
                generation_config_params["temperature"] = 0.0
                # generation_config_params["top_k"] = 1
                # generation_config_params["top_p"] = 1.0
            else:
                generation_config_params["temperature"] = 0.2  # Default temperature

            if max_tokens is not None:
                generation_config_params["max_output_tokens"] = max_tokens
            # thinking_budget is not a direct Gemini API parameter, log if provided
            # generation_config_params["thinking_budget"] = thinking_budget # Example if it were supported

            if log_file_path:
                try:
                    request_data_to_log = {
                        "provider": "google",
                        "model": model,
                        "prompt": prompt_content,
                        "generation_config": generation_config_params,
                        "thinking_budget_requested": thinking_budget,  # Logged here
                    }
                    with open(log_file_path, "a", encoding="utf-8") as lf:
                        lf.write(
                            f"--- GEMINI REQUEST ---\n{json.dumps(request_data_to_log, indent=2)}\n\n"
                        )
                except Exception as log_e:
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(
                                f"--- GEMINI REQUEST LOGGING ERROR ---\nError: {str(log_e)}\n\n"
                            )
                    except:
                        pass

            response = llm_client.generate_content(
                prompt_content,
                generation_config=genai.types.GenerationConfig(
                    **generation_config_params
                ),
            )

            if log_file_path:
                try:
                    gemini_response_log_data = {}
                    if hasattr(response, "candidates") and response.candidates:
                        gemini_response_log_data["candidates"] = []
                        for cand in response.candidates:
                            candidate_info = {}
                            if hasattr(cand, "content") and hasattr(
                                cand.content, "parts"
                            ):
                                candidate_info["content_parts"] = [
                                    {"text": p.text}
                                    for p in cand.content.parts
                                    if hasattr(p, "text")
                                ]
                                if hasattr(cand.content, "role"):
                                    candidate_info["content_role"] = cand.content.role
                            if hasattr(cand, "finish_reason"):
                                candidate_info["finish_reason"] = str(
                                    cand.finish_reason
                                )
                            if hasattr(cand, "safety_ratings"):
                                candidate_info["safety_ratings"] = [
                                    {
                                        "category": str(sr.category),
                                        "probability": str(sr.probability),
                                    }
                                    for sr in cand.safety_ratings
                                ]
                            if hasattr(cand, "token_count"):
                                candidate_info["token_count"] = cand.token_count
                            gemini_response_log_data["candidates"].append(
                                candidate_info
                            )

                    if (
                        hasattr(response, "prompt_feedback")
                        and response.prompt_feedback
                    ):
                        gemini_response_log_data["prompt_feedback"] = {
                            "block_reason": (
                                str(response.prompt_feedback.block_reason)
                                if response.prompt_feedback.block_reason
                                else None
                            ),
                            "safety_ratings": (
                                [
                                    {
                                        "category": str(sr.category),
                                        "probability": str(sr.probability),
                                    }
                                    for sr in response.prompt_feedback.safety_ratings
                                ]
                                if hasattr(response.prompt_feedback, "safety_ratings")
                                else []
                            ),
                        }
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        gemini_response_log_data["usage_metadata"] = {
                            "prompt_token_count": (
                                response.usage_metadata.prompt_token_count
                                if hasattr(
                                    response.usage_metadata, "prompt_token_count"
                                )
                                else 0
                            ),
                            "candidates_token_count": (
                                response.usage_metadata.candidates_token_count
                                if hasattr(
                                    response.usage_metadata, "candidates_token_count"
                                )
                                else 0
                            ),
                            "total_token_count": (
                                response.usage_metadata.total_token_count
                                if hasattr(response.usage_metadata, "total_token_count")
                                else 0
                            ),
                        }
                    if hasattr(
                        response, "text"
                    ):  # Helper attribute for simple text responses
                        gemini_response_log_data["aggregated_text"] = response.text

                    with open(log_file_path, "a", encoding="utf-8") as lf:
                        lf.write(
                            f"--- GEMINI RESPONSE ---\n{json.dumps(gemini_response_log_data, indent=2, default=str)}\n\n"
                        )
                except Exception as log_e:
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(
                                f"--- GEMINI RESPONSE LOGGING ERROR ---\nError: {str(log_e)}\nOriginal response (partial string representation):\n{str(response)[:1000]}...\n\n"
                            )
                    except:
                        pass

            # Accessing text safely
            if response.parts:
                generated_code = "".join(part.text for part in response.parts).strip()
            elif response.candidates and response.candidates[0].content.parts:
                generated_code = "".join(
                    part.text for part in response.candidates[0].content.parts
                ).strip()
            else:
                print(
                    "warning: gemini response seems empty or was blocked.",
                    file=sys.stderr,
                )
                if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                    print(
                        f"prompt feedback: {response.prompt_feedback}", file=sys.stderr
                    )
                generated_code = f"// error: could not generate code. response from gemini was empty or blocked. target: {target_language}"

            # Token usage for Google Gemini
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(
                    response.usage_metadata, "prompt_token_count", 0
                )
                candidates_tokens = getattr(
                    response.usage_metadata, "candidates_token_count", 0
                )
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0)

                if (
                    total_tokens > 0 or prompt_tokens > 0 or candidates_tokens > 0
                ):  # Check if any token data is available
                    input_units = prompt_tokens
                    output_units = candidates_tokens
                    calculated_thinking_units = total_tokens - (
                        input_units + output_units
                    )
                    thinking_units = max(
                        0, calculated_thinking_units
                    )  # Ensure non-negative
                    unit_name = "tokens"
                else:  # No meaningful token data in metadata, fallback to characters
                    print(
                        "warning: token usage information from gemini metadata is zero or all zero. falling back to character counts.",
                        file=sys.stderr,
                    )
                    input_units = len(prompt_content)
                    output_units = len(generated_code)
                    thinking_units = 0  # No thinking units for character counts
                    unit_name = "characters"
            else:  # No usage_metadata attribute, fallback to characters
                print(
                    "warning: token usage information (usage_metadata) not available from gemini. falling back to character counts.",
                    file=sys.stderr,
                )
                input_units = len(prompt_content)
                output_units = len(generated_code)
                thinking_units = 0  # No thinking units for character counts
                unit_name = "characters"

        # Post-processing: remove markdown code fences if present.
        generated_code = strip_markdown_fences(generated_code)

        return generated_code, input_units, output_units, thinking_units, unit_name

    except Exception as e:
        if log_file_path:
            try:
                with open(log_file_path, "a", encoding="utf-8") as lf:
                    lf.write(f"--- LLM COMMUNICATION ERROR ---\n{str(e)}\n\n")
            except:
                pass  # Suppress errors during error logging
        print(f"error communicating with llm: {e}", file=sys.stderr)
        sys.exit(1)


def strip_markdown_fences(text: str) -> str:
    """
    Removes markdown code fences if they enclose the entire non-whitespace content.

    This function checks if the first and last non-whitespace lines of the text
    are markdown fence delimiters (e.g., "```"). If they are, it returns the
    text between these fences. Otherwise, it returns the original text unchanged.
    This is to avoid stripping fences from code that is part of a larger
    explanation, and only strip them when the response is purely a code block.
    """
    lines = text.split('\n')

    # Find the index of the first line with content
    first_content_index = -1
    for i, line in enumerate(lines):
        if line.strip():
            first_content_index = i
            break

    # If no content, return original text
    if first_content_index == -1:
        return text

    # Find the index of the last line with content
    last_content_index = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_content_index = i
            break
    
    # Check if the first and last content lines are fences
    first_line_is_fence = lines[first_content_index].strip().startswith("```")
    last_line_is_fence = lines[last_content_index].strip().startswith("```")

    # Only strip if both are fences and they are on different lines
    if first_line_is_fence and last_line_is_fence and first_content_index < last_content_index:
        # Return the content between the fences
        return '\n'.join(lines[first_content_index + 1:last_content_index])

    return text


def get_default_output_filename(input_filename: str, target_language: str) -> str:
    """
    Generates a default output filename based on the input filename and target language.
    Example: "hello.en" and "python" -> "hello.py"
    """
    base, _ = os.path.splitext(input_filename)
    ext = LANGUAGE_TO_EXTENSION_MAP.get(
        target_language.lower(), target_language.lower()
    )
    return f"{base}.{ext}"


def get_language_from_extension(filename: str) -> str | None:
    """
    Determines the programming language from a filename extension.
    Returns the language name (lowercase) or None if the extension is not recognized.
    """
    _, ext = os.path.splitext(filename)
    if ext.startswith("."):  # remove leading dot
        ext = ext[1:]
    return EXTENSION_TO_LANGUAGE_MAP.get(ext.lower())


def main():
    parser = argparse.ArgumentParser(
        description="transpile english language files to a target programming language using an LLM."
    )
    parser.add_argument(
        "input_file", help="path to the input english file (e.g., hello.en)"
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="optional path to the output code file. if not provided, it's derived from the input file name and target language.",
    )
    parser.add_argument(
        "-l",
        "--target_language",
        help="target programming language (e.g., python, c). optional if --output_file with a known extension is provided.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model to use. overrides model specified in .enc.env. ensure this model is available with your API key and selected provider.",
    )
    parser.add_argument(
        "--conventions",
        default="HACKING.md",
        help="path to a file containing coding conventions or a style guide for the LLM. defaults to HACKING.md.",
    )
    parser.add_argument(
        "--prompt-template-file",
        default=os.getenv("PROMPT_TEMPLATE_PATH", "res/prompt.tmpl"),
        help="path to the code generation prompt template file. "
        "can also be set with PROMPT_TEMPLATE_PATH env var. "
        "defaults to res/prompt.tmpl.",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="optional seed for the LLM to attempt deterministic output. not all models or providers may support this effectively. defaults to random.",
    )
    parser.add_argument(
        "-mt",
        "--max-tokens",
        type=int,
        default=None,  # Will be resolved dynamically after model selection
        help="optional maximum number of tokens for the LLM to generate. "
        "priority: cli argument > MAX_TOKENS env var > model-specific limit from pricing.json (max_output_tokens then max_tokens) > global fallback (1048576).",
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=os.getenv("THINKING_BUDGET", 2048),
        help="optional thinking budget for the LLM. "
        "set by THINKING_BUDGET env var if not provided. "
        "defaults to 2048. actual use depends on LLM provider/model.",
    )
    parser.add_argument(
        "--logs-path",
        default=os.getenv("LOGS_PATH", "./log/"),
        help="directory to store api call logs. "
        "can also be set with LOGS_PATH env var. "
        "defaults to ./log/.",
    )
    parser.add_argument(
        "--context-files",
        default=os.getenv("CONTEXT_FILES", ""),
        help="optional colon-separated list of paths to context files. can also be set with CONTEXT_FILES env var (colon-separated).",
    )
    parser.add_argument(
        "--grounded-mode",
        action=argparse.BooleanOptionalAction,
        default=os.getenv("GROUNDED_MODE", "false").lower() == 'true',
        help="if true, adds the existing code (if present) to context files. "
             "can be set with GROUNDED_MODE env var. defaults to false. "
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="print the fully constructed configuration (including environment variables, flags, etc.) and exit.",
    )
    parser.add_argument(
        "--pricing-file",
        default=os.getenv("PRICING_FILE_PATH", "res/pricing.json"),
        help="path to the pricing data JSON file. "
        "can also be set with PRICING_FILE_PATH env var. "
        "defaults to res/pricing.json.",
    )

    args = parser.parse_args()

    # Load pricing data and determine LLM details early for config resolution
    pricing_data = load_pricing_data(args.pricing_file)
    llm_client, provider_name, model_name = get_llm_details(args.model)

    DEFAULT_MAX_TOKENS_FALLBACK = 1048576

    # Determine effective max_tokens with priority: CLI > ENV > Pricing > Fallback
    # args.max_tokens is initially from CLI (or None if not provided)
    effective_max_tokens = args.max_tokens

    if effective_max_tokens is None:  # CLI --max-tokens not provided
        max_tokens_env = os.getenv("MAX_TOKENS")
        if max_tokens_env is not None:
            try:
                effective_max_tokens = int(max_tokens_env)
            except ValueError:
                print(
                    f"warning: MAX_TOKENS environment variable ('{max_tokens_env}') is not a valid integer. attempting model-specific default.",
                    file=sys.stderr,
                )
                # effective_max_tokens remains None, will fall through to pricing lookup

        if effective_max_tokens is None:  # Still None (no CLI, no valid ENV)
            model_key = f"{provider_name}/{model_name}"
            model_pricing_info = pricing_data.get(model_key)

            resolved_from_pricing = None
            if model_pricing_info:
                if "max_output_tokens" in model_pricing_info:
                    resolved_from_pricing = model_pricing_info["max_output_tokens"]
                elif "max_tokens" in model_pricing_info:  # Fallback to 'max_tokens'
                    resolved_from_pricing = model_pricing_info["max_tokens"]

                if resolved_from_pricing is not None:
                    effective_max_tokens = resolved_from_pricing
                else:
                    print(
                        f"warning: no 'max_output_tokens' or 'max_tokens' found for model '{model_key}' in pricing data. using global fallback {DEFAULT_MAX_TOKENS_FALLBACK}.",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"warning: no pricing data found for model '{model_key}'. using global fallback {DEFAULT_MAX_TOKENS_FALLBACK} for max_tokens.",
                    file=sys.stderr,
                )

            if (
                effective_max_tokens is None
            ):  # Fallback if model-specific lookup failed or no pricing info
                effective_max_tokens = DEFAULT_MAX_TOKENS_FALLBACK

    args.max_tokens = effective_max_tokens  # Update args with the final resolved value

    # Build the consolidated configuration dictionary
    config_dict = vars(args)
    # Add environment variables that influence config to the output for clarity
    config_dict["ENV_PROVIDER"] = os.getenv("PROVIDER")
    config_dict["ENV_MODEL"] = os.getenv("MODEL")
    config_dict["ENV_OPENAI_API_KEY_SET"] = bool(os.getenv("OPENAI_API_KEY"))
    config_dict["ENV_GEMINI_API_KEY_SET"] = bool(os.getenv("GEMINI_API_KEY"))
    config_dict["ENV_OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
    config_dict["ENV_PROMPT_TEMPLATE_PATH"] = os.getenv("PROMPT_TEMPLATE_PATH")
    config_dict["ENV_MAX_TOKENS"] = os.getenv("MAX_TOKENS")  # Show raw env value
    config_dict["ENV_THINKING_BUDGET"] = os.getenv("THINKING_BUDGET")
    config_dict["ENV_LOGS_PATH"] = os.getenv("LOGS_PATH")
    config_dict["ENV_CONTEXT_FILES"] = os.getenv("CONTEXT_FILES")
    config_dict["ENV_GROUNDED_MODE"] = os.getenv("GROUNDED_MODE")
    config_dict["ENV_PRICING_FILE_PATH"] = os.getenv("PRICING_FILE_PATH")
    # args.max_tokens in config_dict already reflects the resolved value

    if args.show_config:
        print(json.dumps(config_dict, indent=2, default=str))
        sys.exit(0)

    log_file_path = None
    # LOGS_PATH is now determined by argparse, with env var as fallback, then default
    if args.logs_path:
        os.makedirs(args.logs_path, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Sanitize provider_name and model_name for use in filename
        safe_provider_name = "".join(
            c if c.isalnum() or c in ["-", "."] else "_" for c in provider_name
        )
        safe_model_name = "".join(
            c if c.isalnum() or c in ["-", "."] else "_" for c in model_name
        )

        log_filename = (
            f"enc_api_log_{timestamp}_{safe_provider_name}_{safe_model_name}.log"
        )
        log_file_path = os.path.join(args.logs_path, log_filename)

        # Log the consolidated configuration
        try:
            with open(log_file_path, "a", encoding="utf-8") as lf:
                lf.write(
                    f"--- CONFIGURATION ---\n{json.dumps(config_dict, indent=2, default=str)}\n\n"
                )
        except Exception as e:
            print(
                f"warning: could not write config to log file '{log_file_path}': {e}",
                file=sys.stderr,
            )
    else:
        print(
            "info: api call logging is disabled as --logs-path is empty.",
            file=sys.stderr,
        )

    if not os.path.exists(args.input_file):
        print(f"error: input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            english_content = f.read()
    except Exception as e:
        print(f"error reading input file '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    if not english_content.strip():
        print(f"error: input file '{args.input_file}' is empty.", file=sys.stderr)
        sys.exit(1)

    # Determine target language and output file
    target_language = args.target_language.lower() if args.target_language else None
    output_file = args.output_file

    if output_file:
        derived_lang_from_output = get_language_from_extension(output_file)
        if derived_lang_from_output:
            if target_language and target_language != derived_lang_from_output:
                print(
                    f"error: specified target language '{target_language}' conflicts with language '{derived_lang_from_output}' inferred from output file extension '{os.path.splitext(output_file)[1]}'.",
                    file=sys.stderr,
                )
                sys.exit(1)
            target_language = derived_lang_from_output
        elif not target_language:
            print(
                f"error: cannot determine target language from output file '{output_file}' extension and --target_language not specified.",
                file=sys.stderr,
            )
            sys.exit(1)
    elif not target_language:
        print(
            "error: either --output_file (with a known extension) or --target_language must be specified.",
            file=sys.stderr,
        )
        sys.exit(1)

    if (
        not output_file
    ):  # If output_file was not specified, derive it now that we have target_language
        output_file = get_default_output_filename(args.input_file, target_language)

    generation_command_str = " ".join(sys.argv)

    # Process context_files argument, splitting by colon
    parsed_context_files = []
    if args.context_files:  # Check if the string is not empty
        parsed_context_files = [
            item.strip() for item in args.context_files.split(":") if item.strip()
        ]

    # GROUNDED_MODE logic: add output file to context if it exists
    if args.grounded_mode and output_file and os.path.isfile(output_file):
        print(f"info: grounded mode is on. adding existing '{output_file}' to context.", file=sys.stderr)
        # Prepend it to make it a primary context file.
        # Avoid adding it if it's already in the list from --context-files
        if output_file not in parsed_context_files:
            parsed_context_files.insert(0, output_file)

    context_files_list = []
    if parsed_context_files:
        for file_path in parsed_context_files:
            if not os.path.isfile(file_path):
                print(
                    f"warning: context file '{file_path}' not found or is not a file. skipping.",
                    file=sys.stderr,
                )
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f_context:
                    file_content = f_context.read()
                _, file_extension = os.path.splitext(file_path)
                language_tag = file_extension[1:] if file_extension else "text"
                context_files_list.append(
                    f"### {file_path}\n```{language_tag}\n{file_content}\n```"
                )
            except Exception as e:
                print(
                    f"warning: could not read context file '{file_path}': {e}. skipping.",
                    file=sys.stderr,
                )

    if context_files_list:
        context_files_str = "\n\n".join(context_files_list)
    else:
        context_files_str = "No context files were provided."

    # Read conventions file
    conventions_content = ""
    if args.conventions:
        if not os.path.exists(args.conventions):
            print(
                f"warning: conventions file '{args.conventions}' not found. proceeding without a style guide.",
                file=sys.stderr,
            )
        else:
            try:
                with open(args.conventions, "r", encoding="utf-8") as f:
                    conventions_content = f.read()
                if not conventions_content.strip():
                    print(
                        f"warning: conventions file '{args.conventions}' is empty. proceeding without a style guide.",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(
                    f"warning: error reading conventions file '{args.conventions}': {e}. proceeding without a style guide.",
                    file=sys.stderr,
                )

    print(f"transpiling '{args.input_file}' to {target_language} -> '{output_file}'...")

    # llm_client, provider_name, model_name were already obtained earlier
    # print(f"Using LLM provider: {provider_name}, Model: {model_name}, Max Tokens: {args.max_tokens}")

    generated_code, input_units, output_units, thinking_units, unit_name = (
        transpile_english_to_code(
            english_content,
            target_language,
            output_file,
            llm_client,
            provider_name,
            model_name,
            conventions_content,
            args.prompt_template_file,
            generation_command_str,
            context_files_str,
            args.seed,
            args.max_tokens,
            args.thinking_budget,
            log_file_path=log_file_path,
        )
    )

    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            # print(f"Created output directory: {output_dir}") # Removed this line

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"successfully transpiled to '{output_file}'")

        # Calculate and print pricing information
        print(f"llm provider: {provider_name}, model: {model_name}")
        usage_string = f"usage: input: {input_units} {unit_name}, output: {output_units} {unit_name}"
        if unit_name == "tokens":
            usage_string += f", thinking: {thinking_units} {unit_name}"
        else:
            usage_string += ", thinking: N/A"
        print(usage_string)

        model_key = f"{provider_name}/{model_name}"
        pricing_info = pricing_data.get(model_key)

        if pricing_info:
            if unit_name == "tokens":  # Ensure we are using tokens for calculation
                input_cost = 0
                output_cost = 0
                thinking_cost = 0

                if "input_cost_per_token" in pricing_info:
                    input_cost = input_units * pricing_info["input_cost_per_token"]
                else:
                    print(
                        f"warning: 'input_cost_per_token' missing for '{model_key}' in pricing data.",
                        file=sys.stderr,
                    )

                if "output_cost_per_token" in pricing_info:
                    output_cost = output_units * pricing_info["output_cost_per_token"]
                else:
                    print(
                        f"warning: 'output_cost_per_token' missing for '{model_key}' in pricing data.",
                        file=sys.stderr,
                    )

                # Calculate thinking cost
                if thinking_units > 0:
                    if "thinking_cost_per_token" in pricing_info:
                        thinking_cost = (
                            thinking_units * pricing_info["thinking_cost_per_token"]
                        )
                    elif (
                        "output_cost_per_token" in pricing_info
                    ):  # Fallback to output token cost
                        thinking_cost = (
                            thinking_units * pricing_info["output_cost_per_token"]
                        )
                        print(
                            f"warning: 'thinking_cost_per_token' missing for '{model_key}'. using 'output_cost_per_token' for {thinking_units} thinking units.",
                            file=sys.stderr,
                        )
                    else:  # No specific thinking cost and no fallback output cost
                        print(
                            f"warning: 'thinking_cost_per_token' missing and 'output_cost_per_token' (fallback) also missing for '{model_key}'. cost for {thinking_units} thinking units not calculated, remains $0.00.",
                            file=sys.stderr,
                        )
                # if thinking_units is 0, thinking_cost remains 0 as initialized

                total_cost = input_cost + output_cost + thinking_cost

                print(
                    f"estimated cost (input: {input_units} tk, output: {output_units} tk, thinking: {thinking_units} tk):"
                )
                print(f"  input cost:    ${input_cost:.6f}")
                print(f"  output cost:   ${output_cost:.6f}")
                # Print thinking cost if it was calculated (is > 0) or if a price for it (specific or fallback) exists (to show $0.00 if units are 0 or price is 0)
                if (
                    thinking_cost > 0
                    or ("thinking_cost_per_token" in pricing_info)
                    or (
                        "output_cost_per_token" in pricing_info
                        and "thinking_cost_per_token" not in pricing_info
                    )
                ):
                    print(f"  thinking cost: ${thinking_cost:.6f}")
                print(f"  total cost:    ${total_cost:.6f}")
            else:
                print(
                    f"cost calculation skipped: pricing data is per token, but usage is reported in '{unit_name}'."
                )
        else:
            print(
                f"cost calculation skipped: no pricing data available for model '{model_key}' in '{args.pricing_file}'."
            )

    except Exception as e:
        print(f"error writing output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
