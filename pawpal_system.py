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
        +list~str~ preferences
        +add_pet(pet: Pet) None
        +remove_pet(pet_name: str) None
        +get_pets() list~Pet~
        +get_all_tasks() list~Task~
    }
    class Pet {
        +str name
        +str species
        +int age_years
        +str notes
        +list~Task~ tasks
        +add_task(task: Task) None
        +remove_task(title: str) None
        +get_tasks() list~Task~
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
    }
    class Scheduler {
        +Owner owner
        +Pet pet
        +int time_budget_minutes
        +build_plan() list~Task~
        +explain_plan(plan: list~Task~) str
        +filter_tasks(completed, pet_name) list~Task~
        +get_conflicts() list~tuple~
    }

    Owner "1" --> "1..*" Pet : owns
    Pet  "1" --> "0..*" Task : has
    Scheduler --> Owner : references
    Scheduler --> Pet  : schedules for
"""

from __future__ import annotations

from dataclasses import dataclass, field

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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
        """Return the pet's tasks sorted high → medium → low, skipping completed ones."""
        return sorted(
            [t for t in self.pet.get_tasks() if not t.completed],
            key=lambda t: _PRIORITY_ORDER.get(t.priority, 99),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_plan(self) -> list[Task]:
        """
        Greedily select tasks that fit within the time budget.

        Tasks are considered in priority order (high first). Each task is
        included if its duration fits in the remaining time.  Returns the
        ordered list of selected tasks.
        """
        budget = self._effective_budget()
        plan: list[Task] = []
        remaining = budget

        for task in self._sorted_tasks():
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
            If True, return only completed tasks.
            If False, return only incomplete tasks.
            If None (default), return all tasks regardless of status.
        pet_name : str | None
            If provided, only return tasks whose pet name matches (case-insensitive).
            If None, uses the Scheduler's own pet.
        """
        source_pet = self.pet
        if pet_name is not None and pet_name.lower() != self.pet.name.lower():
            # Caller asked for a different pet — look it up through the owner
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

        Duplicate titles indicate the same care activity was added twice,
        which would cause it to appear twice in the schedule.
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

    def explain_plan(self, plan: list[Task]) -> str:
        """
        Return a formatted, human-readable explanation of the daily plan.

        Shows each task with its start time, duration, priority, and a brief
        reason for its inclusion. Tasks are assumed to start back-to-back from
        08:00.
        """
        if not plan:
            return "No tasks fit within today's time budget."

        budget = self._effective_budget()
        total_scheduled = sum(t.duration_minutes for t in plan)
        lines: list[str] = [
            f"Daily plan for {self.pet.name} ({self.owner.name})",
            f"Time budget: {budget} min  |  Scheduled: {total_scheduled} min",
            "-" * 50,
        ]

        # Walk through tasks, tracking a running clock from 08:00
        hour, minute = 8, 0
        for task in plan:
            start = f"{hour:02d}:{minute:02d}"
            end_minute = minute + task.duration_minutes
            end_hour = hour + end_minute // 60
            end_minute = end_minute % 60
            end = f"{end_hour:02d}:{end_minute:02d}"

            reason = f"priority={task.priority}"
            lines.append(
                f"  {start}–{end}  [{task.category}]  {task.title}  "
                f"({task.duration_minutes} min, {reason})"
            )

            hour, minute = end_hour, end_minute

        lines.append("-" * 50)
        skipped = [t for t in self.pet.get_tasks() if t not in plan and not t.completed]
        if skipped:
            lines.append("Skipped (did not fit in budget):")
            for t in skipped:
                lines.append(f"  • {t.title} ({t.duration_minutes} min, priority={t.priority})")

        return "\n".join(lines)
