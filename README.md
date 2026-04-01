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
