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
        +mark_complete() None
        +reset() None
    }
    class Scheduler {
        +Owner owner
        +Pet pet
        +int time_budget_minutes
        +build_plan() list~Task~
        +explain_plan(plan: list~Task~) str
    }

    Owner "1" --> "1..*" Pet : owns
    Pet  "1" --> "0..*" Task : has
    Scheduler --> Owner : references
    Scheduler --> Pet  : schedules for
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care item."""

    title: str
    duration_minutes: int
    priority: str          # "low" | "medium" | "high"
    category: str = "general"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass  # TODO: implement

    def reset(self) -> None:
        """Reset completed status (e.g. for a new day)."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a single pet."""

    name: str
    species: str           # "dog" | "cat" | "other"
    age_years: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        pass  # TODO: implement

    def remove_task(self, title: str) -> None:
        """Remove a task by title (case-insensitive)."""
        pass  # TODO: implement

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner."""

    name: str
    available_minutes: int = 60    # time budget for the day
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        pass  # TODO: implement

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name (case-insensitive)."""
        pass  # TODO: implement

    def get_pets(self) -> list[Pet]:
        """Return all pets owned."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    """Builds a daily care plan for one Owner + Pet pair."""

    owner: Owner
    pet: Pet
    time_budget_minutes: int = 0   # defaults to owner.available_minutes if 0

    def build_plan(self) -> list[Task]:
        """
        Select and order tasks that fit within the time budget.

        Strategy (to implement):
          1. Filter tasks by priority (high → medium → low).
          2. Greedily add tasks until time_budget is exhausted.
          3. Return the ordered list.
        """
        pass  # TODO: implement

    def explain_plan(self, plan: list[Task]) -> str:
        """
        Return a human-readable explanation of why each task was chosen
        and when it is scheduled.
        """
        pass  # TODO: implement
