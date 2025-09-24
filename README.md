# Todoist Section Assigner (AI‑powered)

Assign unsectioned Todoist tasks to the most fitting sections using an LLM. The script fetches tasks and sections from a given Todoist project, asks an AI agent to propose a mapping, and then applies the moves via the official Todoist API (async).

> **Note**
> This tool **only** touches tasks **without** a section. Tasks that already have a section are left as‑is.

---

## Features

* 🔍 Detects tasks in a project that have **no section** yet
* 🧠 Uses an LLM to match tasks → sections based on their names
* ⚡ Applies moves concurrently via `asyncio.gather` for speed
* 📝 Human‑readable logging (prints task/section **names**, not only IDs)

---

## Requirements

* **Python**: 3.10+
* **APIs & Keys**:

  * **Todoist API token** (passed via `--api-key` or env `TODOIST_API_TOKEN`)
  * **OpenAI API key** (env `OPENAI_API_KEY`) for the LLM used by `pydantic_ai`
* **Libraries**:

  * `todoist-api-python`
  * `pydantic`
  * `pydantic_ai`
  * `python-dotenv`

You can install dependencies with:

```bash
pip install -U todoist-api-python pydantic pydantic_ai python-dotenv
```

> If you prefer, create a virtual env first: `python -m venv .venv && source .venv/bin/activate`

---

## Configuration

### Environment variables

* `OPENAI_API_KEY` – required for the AI agent backend (OpenAI).
* `TODOIST_API_TOKEN` – optional; used **only if** you don’t pass `--api-key` on the CLI.

You can keep them in a `.env` file for local development (auto‑loaded via `python-dotenv`):

```env
OPENAI_API_KEY=sk-...
# Optional fallback if you don’t pass --api-key
TODOIST_API_TOKEN=todoist_...
```

> `.env` is **not** required; it just makes local dev convenient.

---

## Usage

The script exposes two inputs:

* **Project ID**: **must** be provided **via CLI** (`--project-id`).
* **API key**: provided via CLI (`--api-key`) or taken from env `TODOIST_API_TOKEN` if `--api-key` is omitted.

### Examples

**With API key in env:**

```bash
export OPENAI_API_KEY=sk-...
export TODOIST_API_TOKEN=todoist_...
python todoist_assign_sections_cli.py --project-id {project_id}
```

**With API key via CLI:**

```bash
export OPENAI_API_KEY=sk-...
python todoist_assign_sections_cli.py \
  --project-id {project_id} \
  --api-key todoist_...
```

**Show help:**

```bash
python main.py -h
```

---

## What it actually does (flow)

1. Loads environment (via `python-dotenv` if present).
2. Parses CLI:

   * `--project-id` (required)
   * `--api-key` (optional; falls back to `TODOIST_API_TOKEN`)
3. Instantiates `TodoistAPIAsync` with the resolved API token.
4. Fetches all **tasks** and **sections** for the project.
5. Filters to tasks **without** a section.
6. Prepares a compact list of task/section candidates and asks the AI agent (`pydantic_ai` with `openai:gpt-4o`) for mappings.
7. Moves tasks to their suggested sections **concurrently** (via `asyncio.gather`).
8. Logs results using task/section **names**.

---

## Logging

Logs are in the format: `YYYY-MM-DD HH:MM:SS [LEVEL] message`.

Sample output:

```
2025-09-24 12:00:00 [INFO] Starting task-section assignment process
2025-09-24 12:00:00 [INFO] Found 3 tasks without section
2025-09-24 12:00:02 [INFO] Requesting AI agent to map tasks to sections
2025-09-24 12:00:03 [INFO] Received mapping from AI agent, moving tasks to sections
2025-09-24 12:00:03 [INFO] Successfully moved task 'Pay electricity bill' to section 'Bills'
2025-09-24 12:00:03 [INFO] Successfully moved task 'Draft release notes' to section 'Release'
2025-09-24 12:00:03 [ERROR] Failed to move task 'Buy cat food' to section 'Groceries': 403 Forbidden
2025-09-24 12:00:03 [INFO] Task-section assignment process completed
```

> Set `PYTHONWARNINGS=default` or run with `-X dev` for more verbosity during debugging.

---

## Troubleshooting

* **`API key is required` error** – Pass `--api-key` or set `TODOIST_API_TOKEN`.
* **`OPENAI_API_KEY` not set** – The AI agent won’t run; set the env var.
* **`403/401` from Todoist** – Check token validity and project access; verify the project ID.
* **No sections returned** – Ensure the project actually has sections created.
* **Agent returns odd mappings** – Rename ambiguous tasks/sections for clearer context; you can also rerun.
* **Rate limits** – Both OpenAI and Todoist can rate‑limit. The script batches moves concurrently; if you hit limits, rerun or reduce parallelism (implementing a limiter is on the roadmap).

---

## Development

* Keep Python ≥3.10.
* Type‑checked with `pydantic` models.
* Async boundary at the top‑level `asyncio.run(run(...))`.
* The AI prompt is intentionally short; feel free to refine instructions for your taxonomy.

### Code structure (high level)

```
.
├── todoist_assign_sections_cli.py
└── README.md (this file)
```

---

## Security & Privacy

* Your Todoist and OpenAI API keys remain local environment/CLI inputs.
* Task/section names are sent to the LLM provider to compute mappings. Avoid including sensitive data in task titles if this is a concern.

---

## FAQ

**Q: Will it change tasks that already have a section?**
A: No. Only tasks with an empty `section_id` are processed.

**Q: Can I run it on multiple projects at once?**
A: Not in one invocation. Run it separately per project ID.

---

## Acknowledgements

* [Todoist API Python (async)](https://github.com/Doist/todoist-api-python)
* [pydantic](https://docs.pydantic.dev/)
* [pydantic‑ai](https://github.com/pydantic/pydantic-ai)
* OpenAI `gpt-4o` model for the suggestion engine
