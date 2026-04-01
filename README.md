# do_what_i_want()

WARNING! First 'works for me' version!

> A Python function that accepts a plain-English task description and produces a result. No schema definitions. No method chaining. No configuration per call. You tell it what you want; it attempts to deliver.

```python
from dwiw import do_what_i_want

result = do_what_i_want("Find the three highest-paid employees", data)
```

---

## Motivation

Every data processing pipeline eventually reaches a point where the developer knows exactly what the output should look like but finds the transformation tedious to express in code. `do_what_i_want()` is an experiment in delegating that last mile to a language model — at the cost of determinism, speed, and arguably good engineering judgment.

This library does not pretend to be production software. It is, however, genuinely useful for prototyping, one-off data tasks, and situations where the alternative is writing thirty lines of boilerplate you will never look at again.

---

## Installation

```bash
pip install anthropic requests
```

Clone the repository and place `dwiw.py`, `dwiw_config_loader.py`, and `dwiw_config.json` in your project directory. There is no PyPI package. This is intentional.

---

## Configuration

Copy `dwiw_config.json` and fill in your credentials:

```json
{
  "default_backend": "claude",

  "claude": {
    "api_key": "sk-ant-...",
    "model": "claude-haiku-4-5",
    "max_tokens": 4096,
    "base_url": "https://api.anthropic.com/v1"
  },

  "local": {
    "api_key": "lm-studio",
    "model": "lmstudio-community/gemma-3-4b",
    "max_tokens": 4096,
    "base_url": "http://localhost:1234/v1"
  },

  "openai": {
    "api_key": "sk-...",
    "model": "gpt-4o-mini",
    "max_tokens": 4096,
    "base_url": "https://api.openai.com/v1"
  },

  "execute_timeout": 10,
  "verbose": false
}
```

The `default_backend` field determines which AI provider is used unless overridden at call time. Any backend following the OpenAI chat completions API format — including Ollama and LM Studio — works out of the box under the `local` key or any custom key you define.

API keys can also be provided via environment variables as a fallback:

| Backend | Environment variable  |
|---------|-----------------------|
| claude  | `ANTHROPIC_API_KEY`   |
| openai  | `OPENAI_API_KEY`      |
| local   | `LM_STUDIO_API_KEY`   |

---

## Usage

### Signature

```python
def do_what_i_want(
    task: str,
    data: Any = None,
    execute: bool = False,
    backend: str | None = None,
) -> dict:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | `str` | A plain-English description of what should be done. |
| `data` | `Any` | The data to operate on. Accepts dicts, lists, strings, numbers, or any JSON-serializable object. Defaults to `None`. |
| `execute` | `bool` | If `False` (default), the AI solves the task directly and returns a result. If `True`, the AI generates Python code which is then executed locally. |
| `backend` | `str \| None` | Overrides `default_backend` for this call. Must match a key defined in `dwiw_config.json`. |

### Return value

Always returns a `dict`:

```python
{
    "result": ...,        # The answer. Type depends on the task.
    "explanation": "...", # A brief description of what was done.
    "code": "...",        # Only present when execute=True.
}
```

On failure:

```python
{
    "result": None,
    "explanation": "Something went wrong.",
    "error": "ExceptionType",
    "details": "..."
}
```

---

## Modes

### Solve mode (`execute=False`)

The AI receives the task and data, reasons about the problem, and returns a structured JSON answer directly. No code is generated or executed locally. This is the default.

```python
people = [
    {"name": "Alice", "age": 30, "salary": 55000},
    {"name": "Bob",   "age": 25, "salary": 42000},
    {"name": "Carol", "age": 35, "salary": 67000},
]

result = do_what_i_want(
    "Sort by salary descending and return only name and salary",
    people
)
# → {"result": [{"name": "Carol", ...}, ...], "explanation": "Sorted the list..."}
```

Suitable for: data transformation, summarization, classification, extraction, and any task where the AI's reasoning alone is sufficient.

### Execute mode (`execute=True`)

The AI generates a Python script that solves the task. The script is executed locally via `exec()`. The generated code receives the `data` variable in its local scope and is expected to assign its output to a variable named `result`.

```python
result = do_what_i_want(
    "Calculate average salary and identify the oldest person",
    people,
    execute=True
)
# → {"result": {"average_salary": 54000.0, "oldest": "Carol"}, "code": "...", ...}
```

Suitable for: numeric computation, data reshaping, and tasks that benefit from deterministic code rather than model inference.

**Security note:** `execute=True` runs AI-generated code on your machine without sandboxing. Do not use this mode with untrusted input data or in any environment where arbitrary code execution is a concern.

### Selecting a backend per call

```python
# Use the local LM Studio instance for this call only
result = do_what_i_want(
    "How many records have a status of 'active'?",
    records,
    backend="local"
)
```

---

## Verbose mode

Set `"verbose": true` in `dwiw_config.json` to print the selected backend, mode, and — in execute mode — the full generated code to stdout. Useful for debugging unexpected results.

---

## Limitations

- **Non-deterministic.** The same call may return different results on different runs.
- **Slow.** Each call is a full API round-trip. This is not a replacement for a `sorted()` call.
- **No streaming.** Results are returned only after the model finishes.
- **Standard library only in execute mode.** Generated code cannot import third-party packages.
- **JSON-serializable data only.** Objects that cannot be serialized fall back to `repr()`, which may reduce model accuracy.

---

## Project structure

```
dwiw/
├── dwiw.py                  # Core function
├── dwiw_config_loader.py    # Config loading and backend resolution
├── dwiw_config.json         # Your credentials and backend definitions
└── examples.py              # Runnable usage examples
```

---

## License

MIT. Use it however you like. Attribution is appreciated but not required.

---

## Origin

The name and concept are inspired by a webcomic in which a programmer, frustrated with the specificity demanded by conventional APIs, sets out to build a function that simply does what he wants. At the time, this was a joke. It remains, at least partially, a joke. Also, yes, this is low efford and done by Claude.
