"""
PawPal+ – backend logic layer.

Classes
-------
Owner      – the human caring for the pet(s)
Pet        – a single pet with its own task list
Task       – one care item (walk, feed, meds, …)
Scheduler  – builds and explains a daily plan for one Owner + Pet pair

UML (Mermaid):

classDiagram
    class Owner {
        +str name
        +int available_minutes
        +list preferences
        +add_pet(pet Pet) None
        +remove_pet(pet_name str) None
        +get_pets() list
        +get_all_tasks() list
        +to_dict() dict
        +save_to_json(filepath str) None
        +from_dict(data dict) Owner
        +load_from_json(filepath str) Owner
    }
    class Pet {
        +str name
        +str species
        +int age_years
        +str notes
        +list tasks
        +add_task(task Task) None
        +remove_task(title str) None
        +get_tasks() list
        +to_dict() dict
        +from_dict(data dict) Pet
    }
    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +bool completed
        +str frequency
        +mark_complete() None
        +reset() None
        +next_occurrence() Task
        +to_dict() dict
        +from_dict(data dict) Task
    }
    class Scheduler {
        +Owner owner
        +Pet pet
        +int time_budget_minutes
        +build_plan() list
        +build_weighted_plan() list
        +explain_plan(plan list) str
        +filter_tasks(completed bool, pet_name str) list
        +get_conflicts() list
    }

    Owner "1" --> "1..*" Pet : owns
    Pet  "1" --> "0..*" Task : has
    Scheduler --> Owner : references
    Scheduler --> Pet  : schedules for
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Weight tables for Challenge 1 – weighted prioritization
_PRIORITY_WEIGHT  = {"high": 10, "medium": 6, "low": 2}
_FREQUENCY_WEIGHT = {"daily": 3, "weekly": 2, "once": 1}
_CATEGORY_WEIGHT  = {
    "medication": 4,
    "feeding":    3,
    "hygiene":    3,
    "exercise":   2,
    "enrichment": 1,
    "grooming":   0,
    "general":    0,
}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care item (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str = "general"
    completed: bool = False
    frequency: str = "daily"   # "once" | "daily" | "weekly"

    # ── state ──────────────────────────────────────────────────────────────

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion status so the task is fresh for a new day."""
        self.completed = False

    def next_occurrence(self) -> "Task":
        """Return a fresh copy of this task for the next occurrence (completed=False)."""
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            completed=False,
            frequency=self.frequency,
        )

    # ── weighted score (Challenge 1) ────────────────────────────────────────

    def weight(self) -> int:
        """
        Compute a composite urgency score combining priority, frequency, and category.

        Higher score = should be scheduled sooner.
        Formula: priority_weight + frequency_weight + category_weight
        """
        return (
            _PRIORITY_WEIGHT.get(self.priority, 0)
            + _FREQUENCY_WEIGHT.get(self.frequency, 0)
            + _CATEGORY_WEIGHT.get(self.category, 0)
        )

    # ── serialisation (Challenge 2) ────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise this task to a plain dictionary."""
        return {
            "title":            self.title,
            "duration_minutes": self.duration_minutes,
            "priority":         self.priority,
            "category":         self.category,
            "completed":        self.completed,
            "frequency":        self.frequency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialise a Task from a dictionary."""
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data["priority"],
            category=data.get("category", "general"),
            completed=data.get("completed", False),
            frequency=data.get("frequency", "daily"),
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a single pet and owns its list of care tasks."""

    name: str
    species: str            # "dog" | "cat" | "other"
    age_years: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a new care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the first task whose title matches (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    # ── serialisation (Challenge 2) ────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise this pet to a plain dictionary."""
        return {
            "name":      self.name,
            "species":   self.species,
            "age_years": self.age_years,
            "notes":     self.notes,
            "tasks":     [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Deserialise a Pet (and its tasks) from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age_years=data.get("age_years", 0),
            notes=data.get("notes", ""),
        )
        for td in data.get("tasks", []):
            pet.add_task(Task.from_dict(td))
        return pet


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner and aggregates all their pets."""

    name: str
    available_minutes: int = 60     # total time budget for the day
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name (case-insensitive)."""
        self._pets = [p for p in self._pets if p.name.lower() != pet_name.lower()]

    def get_pets(self) -> list[Pet]:
        """Return a copy of the owner's pet list."""
        return list(self._pets)

    def get_all_tasks(self) -> list[Task]:
        """Collect and return every task across all pets."""
        all_tasks: list[Task] = []
        for pet in self._pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    # ── serialisation (Challenge 2) ────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise this owner (and all pets/tasks) to a plain dictionary."""
        return {
            "name":              self.name,
            "available_minutes": self.available_minutes,
            "preferences":       list(self.preferences),
            "pets":              [p.to_dict() for p in self._pets],
        }

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Persist the owner, pets, and tasks to a JSON file."""
        Path(filepath).write_text(
            json.dumps(self.to_dict(), indent=2), encoding="utf-8"
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Deserialise an Owner (and all pets/tasks) from a dictionary."""
        owner = cls(
            name=data["name"],
            available_minutes=data.get("available_minutes", 60),
            preferences=data.get("preferences", []),
        )
        for pd in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pd))
        return owner

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> "Owner | None":
        """
        Load an Owner from a JSON file.

        Returns None if the file does not exist (first run).
        """
        p = Path(filepath)
        if not p.exists():
            return None
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    """Builds a prioritised daily care plan for one Owner + Pet pair."""

    owner: Owner
    pet: Pet
    time_budget_minutes: int = 0    # 0 means use owner.available_minutes

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _effective_budget(self) -> int:
        """Return the active time budget (explicit override or owner's budget)."""
        return self.time_budget_minutes if self.time_budget_minutes > 0 else self.owner.available_minutes

    def _sorted_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted high → medium → low priority."""
        return sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: _PRIORITY_ORDER.get(t.priority, 99),
        )

    def _weighted_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted by composite weight score (descending)."""
        return sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: t.weight(),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_plan(self) -> list[Task]:
        """
        Greedily select tasks that fit within the time budget (priority order).

        Tasks are sorted high → medium → low. Each task is included if its
        duration fits in the remaining budget. Returns the ordered list.
        """
        budget = self._effective_budget()
        plan: list[Task] = []
        remaining = budget
        for task in self._sorted_tasks():
            if task.duration_minutes <= remaining:
                plan.append(task)
                remaining -= task.duration_minutes
        return plan

    def build_weighted_plan(self) -> list[Task]:
        """
        Challenge 1 – Weighted prioritization scheduler.

        Each task receives a composite urgency score:
            score = priority_weight + frequency_weight + category_weight

        Examples:
            daily medication (high)  → 10 + 3 + 4 = 17  (scheduled first)
            weekly grooming  (low)   →  2 + 2 + 0 =  4  (scheduled last)

        Tasks are greedy-selected in descending score order within the time
        budget, giving smarter ordering than a simple high/medium/low sort.
        """
        budget = self._effective_budget()
        plan: list[Task] = []
        remaining = budget
        for task in self._weighted_tasks():
            if task.duration_minutes <= remaining:
                plan.append(task)
                remaining -= task.duration_minutes
        return plan

    def filter_tasks(self, *, completed: bool | None = None, pet_name: str | None = None) -> list[Task]:
        """
        Return tasks filtered by completion status and/or pet name.

        Parameters
        ----------
        completed : bool | None
            True → completed only, False → incomplete only, None → all.
        pet_name : str | None
            Scope to a specific pet (case-insensitive). Defaults to this pet.
        """
        source_pet = self.pet
        if pet_name is not None and pet_name.lower() != self.pet.name.lower():
            match = next(
                (p for p in self.owner.get_pets() if p.name.lower() == pet_name.lower()), None
            )
            if match is None:
                return []
            source_pet = match

        tasks = source_pet.get_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def get_conflicts(self) -> list[tuple[Task, Task]]:
        """
        Return pairs of tasks that share the same title (case-insensitive).

        Duplicate titles cause the same activity to appear twice in the schedule.
        """
        tasks = self.pet.get_tasks()
        seen: dict[str, Task] = {}
        conflicts: list[tuple[Task, Task]] = []
        for task in tasks:
            key = task.title.lower()
            if key in seen:
                conflicts.append((seen[key], task))
            else:
                seen[key] = task
        return conflicts

    def explain_plan(self, plan: list[Task], weighted: bool = False) -> str:
        """
        Return a formatted, human-readable explanation of the daily plan.

        Shows each task with start/end times, duration, priority, and score
        (when weighted=True). Tasks are assumed to start back-to-back from 08:00.
        """
        if not plan:
            return "No tasks fit within today's time budget."

        budget = self._effective_budget()
        total_scheduled = sum(t.duration_minutes for t in plan)
        mode = "weighted score" if weighted else "priority"
        lines: list[str] = [
            f"Daily plan for {self.pet.name} ({self.owner.name})  [{mode} mode]",
            f"Time budget: {budget} min  |  Scheduled: {total_scheduled} min",
            "-" * 55,
        ]

        hour, minute = 8, 0
        for task in plan:
            start = f"{hour:02d}:{minute:02d}"
            end_m = minute + task.duration_minutes
            end_h = hour + end_m // 60
            end_m = end_m % 60
            end = f"{end_h:02d}:{end_m:02d}"
            detail = f"score={task.weight()}" if weighted else f"priority={task.priority}"
            lines.append(
                f"  {start}–{end}  [{task.category}]  {task.title}  "
                f"({task.duration_minutes} min, {detail})"
            )
            hour, minute = end_h, end_m

        lines.append("-" * 55)
        skipped = [t for t in self.pet.get_tasks() if t not in plan and not t.completed]
        if skipped:
            lines.append("Skipped (did not fit in budget):")
            for t in skipped:
                lines.append(f"  • {t.title} ({t.duration_minutes} min, priority={t.priority})")

        return "\n".join(lines)
