"""
PawPal+ – backend logic layer.

Classes: Owner, Pet, Task, Scheduler

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

# Weights used by build_weighted_plan()
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
    """A single care item (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str        # "high" | "medium" | "low"
    category: str = "general"
    completed: bool = False
    frequency: str = "daily"  # "daily" | "weekly" | "once"

    def mark_complete(self) -> None:
        """Mark as done."""
        self.completed = True

    def reset(self) -> None:
        """Clear completed status."""
        self.completed = False

    def next_occurrence(self) -> "Task":
        """Return a copy of this task with completed=False."""
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            completed=False,
            frequency=self.frequency,
        )

    def weight(self) -> int:
        """Return a score based on priority + frequency + category."""
        return (
            _PRIORITY_WEIGHT.get(self.priority, 0)
            + _FREQUENCY_WEIGHT.get(self.frequency, 0)
            + _CATEGORY_WEIGHT.get(self.category, 0)
        )

    def to_dict(self) -> dict:
        """Convert to a plain dictionary."""
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
        """Create a Task from a dictionary."""
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
    """A pet with a list of care tasks."""

    name: str
    species: str  # "dog" | "cat" | "other"
    age_years: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    def get_tasks(self) -> list[Task]:
        """Return a copy of the task list."""
        return list(self.tasks)

    def to_dict(self) -> dict:
        """Convert to a plain dictionary."""
        return {
            "name":      self.name,
            "species":   self.species,
            "age_years": self.age_years,
            "notes":     self.notes,
            "tasks":     [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Create a Pet (and its tasks) from a dictionary."""
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
    """The pet owner — holds pets and a daily time budget."""

    name: str
    available_minutes: int = 60
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet."""
        self._pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name (case-insensitive)."""
        self._pets = [p for p in self._pets if p.name.lower() != pet_name.lower()]

    def get_pets(self) -> list[Pet]:
        """Return a copy of the pet list."""
        return list(self._pets)

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks across all pets."""
        all_tasks: list[Task] = []
        for pet in self._pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def to_dict(self) -> dict:
        """Convert to a plain dictionary."""
        return {
            "name":              self.name,
            "available_minutes": self.available_minutes,
            "preferences":       list(self.preferences),
            "pets":              [p.to_dict() for p in self._pets],
        }

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Save to a JSON file."""
        Path(filepath).write_text(
            json.dumps(self.to_dict(), indent=2), encoding="utf-8"
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Create an Owner (and all pets/tasks) from a dictionary."""
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
        """Load from a JSON file. Returns None if the file doesn't exist."""
        p = Path(filepath)
        if not p.exists():
            return None
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    """Builds a daily care plan for one Owner + Pet pair."""

    owner: Owner
    pet: Pet
    time_budget_minutes: int = 0  # 0 = use owner.available_minutes

    def _effective_budget(self) -> int:
        """Return the time budget to use."""
        return self.time_budget_minutes if self.time_budget_minutes > 0 else self.owner.available_minutes

    def _sorted_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted high → medium → low."""
        return sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: _PRIORITY_ORDER.get(t.priority, 99),
        )

    def _weighted_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted by weight score, highest first."""
        return sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: t.weight(),
            reverse=True,
        )

    def build_plan(self) -> list[Task]:
        """Select tasks by priority order until the time budget is used up."""
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
        Select tasks by weight score until the time budget is used up.

        Score = priority_weight + frequency_weight + category_weight.
        Higher score means the task is scheduled first.
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

        completed: True = done only, False = pending only, None = all.
        pet_name: filter to a specific pet (defaults to the scheduler's pet).
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
        """Return pairs of tasks with the same title (case-insensitive)."""
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
        """Print a timed summary of the plan. Tasks start back-to-back from 08:00."""
        if not plan:
            return "No tasks fit within today's time budget."

        budget = self._effective_budget()
        total = sum(t.duration_minutes for t in plan)
        mode = "weighted score" if weighted else "priority"
        lines: list[str] = [
            f"Daily plan for {self.pet.name} ({self.owner.name})  [{mode} mode]",
            f"Budget: {budget} min  |  Scheduled: {total} min",
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
            lines.append("Skipped (did not fit):")
            for t in skipped:
                lines.append(f"  • {t.title} ({t.duration_minutes} min, {t.priority})")

        return "\n".join(lines)
