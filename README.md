# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

| Feature | Description |
|---|---|
| **Priority-sorted scheduling** | Tasks are ordered high → medium → low before selection. High-priority care (medication, feeding) is always scheduled before enrichment or grooming. |
| **Weighted prioritization** ⭐ | `build_weighted_plan()` scores each task by priority + frequency + category urgency. A daily medication outranks a weekly grooming session even if both are "high". |
| **Greedy time-budget enforcement** | The scheduler fills the owner's daily time budget greedily, skipping tasks that don't fit rather than overcommitting. The budget is hard — the plan never exceeds it. |
| **Conflict detection** | `Scheduler.get_conflicts()` flags duplicate task titles on the same pet, surfacing a warning in the UI before the schedule is generated. |
| **Daily recurrence** | Tasks carry a `frequency` field (`daily`, `weekly`, `once`). When a recurring task is marked complete, `next_occurrence()` automatically queues a fresh copy for the next cycle. |
| **Data persistence** ⭐ | `Owner.save_to_json()` / `load_from_json()` serialise the entire object graph to `data.json`. The Streamlit app loads it on startup so pets and tasks survive restarts. |
| **Plain-language explanation** | `explain_plan()` produces a timed, annotated narrative of every scheduled task — including start/end times, category, and priority — so owners understand *why* the plan looks the way it does. |
| **Multi-pet support** | An owner can register multiple pets. Each pet maintains its own task list; schedules are generated per pet. |
| **Professional CLI output** ⭐ | `main.py` uses `tabulate` to render all terminal output as formatted tables with borders. |

## Optional Extensions Implemented

### Challenge 1 — Weighted Prioritization (Agent Mode)

`Scheduler.build_weighted_plan()` was designed using Agent Mode with the prompt:

> "In `#file:pawpal_system.py`, add a `build_weighted_plan()` method to `Scheduler` that scores each task using a composite weight combining priority level, task frequency, and care category urgency. Daily medication should always outrank weekly grooming even if both are marked high priority."

Agent Mode generated the `_PRIORITY_WEIGHT`, `_FREQUENCY_WEIGHT`, and `_CATEGORY_WEIGHT` lookup tables and the `Task.weight()` helper, then wired them into the greedy selection loop. The scoring was reviewed and the category weights were manually adjusted (medication=4, feeding=3 were bumped up after testing) before accepting the output.

Score formula: `priority_weight + frequency_weight + category_weight`

| Example task | Priority | Frequency | Category | **Score** |
|---|---|---|---|---|
| Daily medication | high | daily | medication | 10+3+4 = **17** |
| Daily walk | high | daily | exercise | 10+3+2 = **15** |
| Weekly grooming | low | weekly | grooming | 2+2+0 = **4** |

### Challenge 2 — Data Persistence (Agent Mode)

Agent Mode was used with the prompt:

> "Add `to_dict()`, `from_dict()`, `save_to_json()`, and `load_from_json()` methods to the `Owner`, `Pet`, and `Task` classes in `#file:pawpal_system.py`. Then update `#file:app.py` to call `Owner.load_from_json('data.json')` on startup and `owner.save_to_json()` after every mutation."

No external library (`marshmallow`, etc.) was needed — a custom recursive `to_dict()` / `from_dict()` pattern keeps the serialisation self-contained and dependency-free.

### Challenge 3 — Advanced Priority UI

🔴 High / 🟡 Medium / 🟢 Low colour-coded icons appear in the task table and schedule table. The weighted score column is shown alongside priority when weighted mode is selected.

### Challenge 4 — Professional CLI Output

`main.py` uses `tabulate` (`rounded_outline` style) to render all terminal output as formatted tables. Install with `pip install tabulate` (included in `requirements.txt`).

### Challenge 5 — Multi-Model Prompt Comparison

See the **Prompt Comparison** section in `reflection.md`.

## 📸 Demo

*Add a screenshot of your running app here using the embed below:*

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

PawPal+'s scheduling goes beyond a simple to-do list:

- **Priority sorting** — tasks are always evaluated high → medium → low. A medication task will never be bumped by a grooming session.
- **Greedy budget enforcement** — the scheduler fills available time without ever overcommitting. If a 30-minute walk and a 20-minute play session both fit but you only have 40 minutes, the walk wins (higher priority) and the remaining 10 minutes stay free.
- **Filtering** — `Scheduler.filter_tasks(completed=False)` returns only pending tasks; `filter_tasks(pet_name="Luna")` scopes to a specific pet. Both filters can be combined.
- **Conflict detection** — `Scheduler.get_conflicts()` finds duplicate task titles before the plan is built, preventing silent double-scheduling.
- **Daily recurrence** — marking a `daily` or `weekly` task complete triggers `next_occurrence()`, which instantly queues a fresh copy so the pet's routine is never broken.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

### What the tests cover

| Area | Tests |
|---|---|
| **Task state** | `mark_complete()`, `reset()`, default `completed=False` |
| **Recurrence** | `next_occurrence()` returns a fresh copy; original and copy are independent |
| **Pet CRUD** | add/remove tasks, empty-pet edge case, removing a non-existent task |
| **Owner aggregation** | add/remove pets, `get_all_tasks()` across multiple pets |
| **Scheduler – sorting** | high → medium → low priority order; ties handled |
| **Scheduler – budget** | total duration ≤ budget; budget smaller than all tasks → empty plan |
| **Scheduler – exclusion** | completed tasks never appear in plan; all-done → empty plan |
| **Scheduler – conflicts** | duplicate titles detected case-insensitively; no false positives |

### Confidence level

⭐⭐⭐⭐ (4/5) — Core scheduling logic, priority sorting, recurrence, and conflict detection are fully tested. Edge cases for empty pets/owners and budget overflows are covered. A 5th star would require integration tests against the Streamlit UI and testing weekly recurrence scheduling across multiple days.
