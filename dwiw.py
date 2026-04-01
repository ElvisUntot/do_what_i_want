"""
do_what_i_want() — because precision is overrated.

Usage:
    from dwiw import do_what_i_want

    result = do_what_i_want("Sort by age", {"people": [...]})
    result = do_what_i_want("Calculate the average", [1, 2, 3], execute=True)
    result = do_what_i_want("Do something useful", data, backend="local")
"""

import json
import traceback
import textwrap
from typing import Any

import requests

from dwiw_config_loader import load_config, get_backend


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialize_data(data: Any) -> str:
    """Convert data into a string the AI can understand."""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return repr(data)


def _build_solve_prompt(task: str, data_str: str) -> str:
    return textwrap.dedent(f"""
        You are a universal problem solver. You receive a task and some data.
        Solve the task directly and respond ONLY with a JSON object.
        No explanatory text outside the JSON. No Markdown code blocks.

        JSON format:
        {{
            "result": <the result of the task, any type>,
            "explanation": "<brief English explanation of what you did>"
        }}

        Task: {task}

        Data:
        {data_str}
    """).strip()


def _build_execute_prompt(task: str, data_str: str) -> str:
    return textwrap.dedent(f"""
        You are a Python developer. You receive a task and some data.
        Write Python code that solves the task and respond ONLY with a JSON object.
        No explanatory text outside the JSON. No Markdown code blocks.

        JSON format:
        {{
            "code": "<complete Python code as a string>",
            "explanation": "<brief English explanation of what the code does>"
        }}

        Requirements for the code:
        - The variable `data` already contains the input data (as a Python object).
        - The result must be stored in a variable named `result` at the end.
        - No imports outside the Python standard library.
        - No input(), no print() for result output.

        Task: {task}

        Data (for reference, available in code as `data`):
        {data_str}
    """).strip()


def _call_claude_api(prompt: str, backend_cfg: dict, verbose: bool) -> str:
    """Call the Anthropic Claude API directly."""
    import anthropic  # lazy import — only when Claude is actually used

    client = anthropic.Anthropic(api_key=backend_cfg["api_key"])
    if verbose:
        print(f"[dwiw] → Claude API ({backend_cfg['model']})")

    message = client.messages.create(
        model=backend_cfg["model"],
        max_tokens=backend_cfg.get("max_tokens", 4096),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai_compat_api(prompt: str, backend_cfg: dict, verbose: bool) -> str:
    """Call any OpenAI-compatible API (OpenAI, LM Studio, Ollama, ...)."""
    url = backend_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {backend_cfg['api_key']}",
    }
    payload = {
        "model": backend_cfg["model"],
        "max_tokens": backend_cfg.get("max_tokens", 4096),
        "messages": [{"role": "user", "content": prompt}],
    }
    if verbose:
        print(f"[dwiw] → OpenAI-compat API: {url} ({backend_cfg['model']})")

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _call_ai(prompt: str, backend_name: str, backend_cfg: dict, verbose: bool) -> str:
    """Route the API call to the appropriate backend."""
    if backend_name == "claude":
        return _call_claude_api(prompt, backend_cfg, verbose)
    else:
        return _call_openai_compat_api(prompt, backend_cfg, verbose)


def _parse_json_response(raw: str) -> dict:
    """Extract JSON from the AI response, even if Markdown fences are present."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(cleaned)


def _execute_code(code: str, data: Any, timeout: int, verbose: bool) -> Any:
    """Execute AI-generated code and return the value of `result`."""
    if verbose:
        print(f"[dwiw] Executing code:\n{'-'*40}\n{code}\n{'-'*40}")

    local_vars = {"data": data}
    try:
        exec(compile(code, "<dwiw_generated>", "exec"), {}, local_vars)  # noqa: S102
    except Exception as e:
        raise RuntimeError(
            f"Error while executing generated code:\n{traceback.format_exc()}"
        ) from e

    if "result" not in local_vars:
        raise RuntimeError(
            "The generated code did not set a variable named 'result'."
        )
    return local_vars["result"]


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def do_what_i_want(
    task: str,
    data: Any = None,
    execute: bool = False,
    backend: str | None = None,
) -> dict:
    """
    Does what you want. Somehow. Usually.

    Parameters:
        task     – What should be done? (free text)
        data     – The data to work with (any Python object)
        execute  – False: AI solves directly → JSON result
                   True:  AI writes code → executed locally
        backend  – Overrides the default_backend from config
                   ("claude", "local", "openai", ...)

    Returns:
        dict with at least "result" and "explanation".
        With execute=True additionally includes "code".
        On error: "error" and "details".
    """
    config = load_config()
    verbose: bool = config.get("verbose", False)
    timeout: int = config.get("execute_timeout", 10)

    backend_name, backend_cfg = get_backend(config, override=backend)
    data_str = _serialize_data(data)

    if verbose:
        print(f"[dwiw] Task    : {task}")
        print(f"[dwiw] Mode    : {'execute' if execute else 'solve'}")
        print(f"[dwiw] Backend : {backend_name}")

    try:
        if execute:
            prompt = _build_execute_prompt(task, data_str)
            raw = _call_ai(prompt, backend_name, backend_cfg, verbose)
            parsed = _parse_json_response(raw)

            code = parsed.get("code", "")
            result_value = _execute_code(code, data, timeout, verbose)

            return {
                "result": result_value,
                "explanation": parsed.get("explanation", ""),
                "code": code,
            }
        else:
            prompt = _build_solve_prompt(task, data_str)
            raw = _call_ai(prompt, backend_name, backend_cfg, verbose)
            parsed = _parse_json_response(raw)

            return {
                "result": parsed.get("result"),
                "explanation": parsed.get("explanation", ""),
            }

    except Exception as e:
        return {
            "result": None,
            "explanation": "Something went wrong.",
            "error": type(e).__name__,
            "details": str(e),
        }
