# PawPal+ Project Reflection

## 1. System Design

**Core user actions (identified from the scenario):**

1. **Add a pet** – the owner enters a pet's name, species, and age so the system knows who it is scheduling for.
2. **Add / edit care tasks** – the owner defines tasks (walk, feeding, meds, grooming, enrichment) with a duration and priority so the scheduler has something to work with.
3. **Generate a daily plan** – the owner clicks "Generate schedule" and receives an ordered list of tasks that fit within their available time, with a plain-language explanation of the choices.

**a. Initial design**

The initial UML includes four classes:

| Class | Responsibility |
|---|---|
| `Task` | Holds a single care item: title, duration, priority, category, and completion status. It is a pure data object with no dependencies. |
| `Pet` | Owns a list of `Task` objects and provides methods to add/remove tasks. Carries identity info (name, species, age). |
| `Owner` | Aggregates one or more `Pet` objects and stores the owner's daily time budget and preferences. |
| `Scheduler` | References one `Owner` and one `Pet`; its `build_plan()` method selects tasks that fit the time budget ordered by priority, and `explain_plan()` narrates the result. |

Relationships:
- `Owner` has 1-to-many `Pet`
- `Pet` has 0-to-many `Task`
- `Scheduler` references both `Owner` (for the time budget) and `Pet` (for the task list)

Python dataclasses are used for `Task`, `Pet`, `Owner`, and `Scheduler` to keep the code concise and readable.

**b. Design changes**

Two additions were made during implementation that were not in the original UML:

1. **`Task.frequency` + `Task.next_occurrence()`** — the initial design had no concept of recurrence. Adding `frequency: str ("daily"/"weekly"/"once")` and a `next_occurrence()` factory method allowed the UI to automatically queue the next instance of a recurring task when the owner marks it complete. This was added to `Task` (not `Scheduler`) because recurrence is a property of the task itself, not of how it is scheduled.

2. **`Scheduler.get_conflicts()`** — conflict detection was not in the original design. It was added after recognising that duplicate task titles would silently appear twice in the schedule without warning. Placing it on `Scheduler` (rather than `Pet`) was a deliberate choice: `Pet` manages data, `Scheduler` manages scheduling concerns, and "is this a problem for the schedule?" is a scheduling concern.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints:

- **Time budget** — `Owner.available_minutes` (or an explicit `Scheduler.time_budget_minutes` override) caps the total duration of the plan. This was treated as the hardest constraint: it is non-negotiable because the owner cannot create more time in a day.
- **Priority** — tasks are sorted `high → medium → low` before greedy selection. Priority was chosen as the ordering signal because it directly encodes the owner's intent (medical tasks are high, enrichment is low).

Preferences (`Owner.preferences`) are stored but not yet factored into sorting. Time and priority were implemented first because they are the minimum viable constraints for a useful scheduler.

**b. Tradeoffs**

The scheduler uses a **greedy / first-fit algorithm**: it iterates through tasks in priority order and adds each one if it fits in the remaining time. The tradeoff is:

- **What it gives up:** optimality. A greedy pass can leave gaps. For example, if a 30-minute high task is followed by a 25-minute medium task, and the budget is 40 minutes, the 30-minute task takes the budget down to 10 — and a 15-minute low task that would have fit gets skipped. A knapsack solver would find the globally optimal combination.
- **Why it is reasonable:** PawPal+ is a daily care tool, not a logistics optimizer. Owners think in priority terms ("make sure the walk and feeding happen first"), and a greedy priority sort matches that mental model exactly. The simplicity also makes the "Why was this plan chosen?" explanation easy to generate and easy to trust.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools (VS Code Copilot and Claude Code) were used across every phase:

- **Phase 1 – Design:** Copilot Chat generated the initial Mermaid UML from a plain-English description of the four classes. The most useful prompt pattern was describing *responsibilities* rather than *implementation* — e.g., "the Scheduler should retrieve tasks from the Owner's pets" — which produced cleaner structural suggestions than asking "write a method that loops over pets."
- **Phase 2 – Implementation:** Agent Mode in Copilot fleshed out all four class bodies from the skeleton. Incremental prompts (one method at a time, reviewed before moving on) produced better results than asking for the whole file at once.
- **Phase 3 – Testing:** A fresh Copilot Chat session (separate from the implementation session) was opened specifically for testing. Asking "What are the most important edge cases for a pet scheduler with priority sorting and recurring tasks?" surfaced the full edge-case list (empty pet, budget too small, all tasks complete, duplicate conflicts) that grew the suite from 9 to 26 tests.
- **Phase 4 – UI polish:** Inline Chat on specific `st.button` blocks suggested `st.toast` for the recurrence feedback — a Streamlit component not used elsewhere — which was a genuinely useful discovery.

**Most effective Copilot features for the scheduler specifically:**
- *Agent Mode* — best for scaffolding and refactoring entire files (class skeletons → full implementations)
- *Inline Chat* — best for targeted edits (one method, one UI component) where full-file context would add noise
- *Separate chat sessions per phase* — keeping design, implementation, testing, and UI in separate sessions prevented context bleed. When the testing session opened with `#codebase`, Copilot focused on the existing signatures rather than re-proposing design changes that had already been decided.

The most consistently useful prompt pattern: **context + constraint + question** — e.g., "Given these four dataclasses, the Scheduler must not exceed the owner's time budget — how should `build_plan()` implement greedy selection?"

**b. Judgment and verification**

During Phase 2, AI initially suggested placing `get_all_tasks()` on the `Scheduler` class rather than on `Owner`. The reasoning given was that "the Scheduler is the one that needs all tasks." This was rejected because it would have violated the separation of concerns established in the UML: `Owner` is responsible for managing its pets and their data, while `Scheduler` is responsible for building plans. Putting `get_all_tasks()` on `Scheduler` would mean `Scheduler` reaches into `Owner`'s internal structure directly, making it harder to change either class independently.

The fix was verified by checking: "if I swap out `Owner` for a different data source, does `Scheduler` need to change?" With `get_all_tasks()` on `Owner`, the answer is no — `Scheduler` just calls `owner.get_all_tasks()` and doesn't care how the owner stores its pets.

---

## 4. Testing and Verification

**a. What you tested**

The 26-test suite covers:

- **Task state:** `mark_complete()`, `reset()`, default `completed=False`
- **Recurrence:** `next_occurrence()` returns a fresh independent copy; original mutation does not affect the copy; works for all frequency values
- **Pet CRUD:** add task, remove task, empty pet returns `[]`, removing a non-existent title is safe
- **Owner aggregation:** add/remove pets, `get_all_tasks()` across multiple pets, owner with no pets
- **Scheduler – sorting:** high before medium before low; ties handled (all same priority)
- **Scheduler – budget:** total ≤ budget; budget smaller than all tasks → empty plan; explicit override
- **Scheduler – exclusion:** completed tasks absent from plan; all-done → empty plan
- **Scheduler – conflicts:** duplicate titles detected; case-insensitive; no false positives

These tests were important because the scheduler's value to the user depends entirely on its correctness: a plan that exceeds the time budget, includes completed tasks, or silently duplicates entries would erode trust immediately.

**b. Confidence**

Confidence: **4/5**.

The core scheduling behaviors are well-covered. The remaining 1 star reflects:
- No integration tests against the Streamlit UI (button clicks, session-state persistence)
- No tests for weekly recurrence across a multi-day simulation
- No tests for the `Owner.preferences` field, which is stored but not yet used in scheduling

---

## 5. Reflection

**a. What went well**

The layered architecture (Task → Pet → Owner → Scheduler) made each phase feel manageable. Because `Scheduler` talks to `Owner` and `Pet` through clean method calls rather than accessing internal fields directly, adding `get_conflicts()` and `next_occurrence()` in Phase 3 required no changes to the existing methods — they just slotted in alongside them. This separation-of-concerns payoff was the most satisfying part of the build.

**b. What you would improve**

The current scheduler makes one pass and stops. A second pass (trying to fill remaining budget gaps with lower-priority tasks that fit) would improve utilisation without breaking the priority ordering guarantee. I would also move the time-slot calculation logic (the `08:00` running clock) out of `explain_plan()` and `app.py` into a dedicated `Scheduler._assign_times()` method so it is testable and reusable.

---

## 6. Prompt Comparison (Challenge 5)

**Task chosen:** Implement the logic for rescheduling weekly tasks — specifically, when a `weekly` task is marked complete, how should the system calculate and schedule the next occurrence?

**Prompt used (identical for both models):**
> "Given a `Task` dataclass with fields `title`, `duration_minutes`, `priority`, `category`, `completed`, and `frequency` ('once'/'daily'/'weekly'), write a method `next_occurrence()` that returns a new Task instance representing the next scheduled occurrence. For weekly tasks, the new task should not be completed and should preserve all other fields. How should the method handle the 'once' frequency?"

---

**Claude (claude-sonnet-4-6) response:**

```python
def next_occurrence(self) -> "Task":
    return Task(
        title=self.title,
        duration_minutes=self.duration_minutes,
        priority=self.priority,
        category=self.category,
        completed=False,
        frequency=self.frequency,
    )
```

Claude's approach: a simple factory method that returns a fresh copy with `completed=False`. It left the `once` frequency decision to the caller — the method always produces a copy regardless of frequency, and the calling code (UI or `main.py`) decides whether to actually add it.

---

**GPT-4o response:**

```python
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Task:
    ...
    due_date: Optional[date] = None

    def next_occurrence(self) -> Optional["Task"]:
        if self.frequency == "once":
            return None  # no recurrence
        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        next_due = (self.due_date or date.today()) + delta
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            completed=False,
            frequency=self.frequency,
            due_date=next_due,
        )
```

GPT-4o's approach: adds a `due_date` field to `Task` and computes `today + 7 days` for weekly tasks. Returns `None` for `once` tasks. More date-aware but requires a schema change.

---

**Comparison and decision:**

| Dimension | Claude | GPT-4o |
|---|---|---|
| Schema change required | None | Adds `due_date` to `Task` |
| Handles `once` frequency | Caller decides | Returns `None` |
| Date arithmetic | Not included | `timedelta` built in |
| Simplicity | High | Moderate |
| Future-proofness | Low (no dates) | High (due dates enable sorting) |

**Which was kept and why:** Claude's version was used in the final implementation. At the time of the decision, PawPal+ had no date-based sorting and the UI doesn't display due dates — adding `due_date` to `Task` would have required updating `to_dict()`, `from_dict()`, the Streamlit form, the test fixtures, and the `main.py` demo. The added complexity wasn't justified by a feature the app doesn't yet use.

GPT-4o's version is the better long-term design if PawPal+ ever adds a calendar view or multi-day planning. The `due_date` field and `None`-on-once behaviour are both strictly more correct. The decision to defer it was about scope, not quality.

**Key insight:** Both models produced working code. The architectural question — does `Task` own its schedule date? — is a design decision that neither model can make. That required human judgment about the current scope of the project.

---

**c. Key takeaway**

The most important insight from this project: **AI is a fast first-drafter, but the architect role belongs to the developer.** AI could generate a working scheduler in minutes, but it could not decide *where* `get_all_tasks()` should live, *why* greedy-over-knapsack is the right tradeoff for this use case, or *what* edge cases actually matter for a pet owner's daily routine. Every meaningful design decision required human judgment — the AI just removed the friction of translating those decisions into code.
