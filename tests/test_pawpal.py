"""
tests/test_pawpal.py – automated test suite for PawPal+ core logic.

Coverage
--------
Task        – completion, reset, recurrence (next_occurrence)
Pet         – add/remove tasks, edge case: no tasks
Owner       – add/remove pets, aggregate tasks across pets
Scheduler   – priority sorting, time budget, completed-task exclusion,
              empty-pet edge case, budget-too-small edge case,
              conflict detection
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ============================================================
# Helpers
# ============================================================

def make_owner(minutes: int = 90) -> Owner:
    owner = Owner(name="Jordan", available_minutes=minutes)
    return owner


def make_pet(name: str = "Mochi", species: str = "dog") -> Pet:
    return Pet(name=name, species=species)


# ============================================================
# Task – basic state
# ============================================================

def test_mark_complete_changes_status():
    """mark_complete() flips completed False → True."""
    task = Task("Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_reset_clears_completed_status():
    """reset() flips completed back to False."""
    task = Task("Breakfast", duration_minutes=10, priority="high")
    task.mark_complete()
    task.reset()
    assert task.completed is False


def test_task_default_not_completed():
    """A newly created task should not be completed by default."""
    task = Task("Walk", duration_minutes=20, priority="medium")
    assert task.completed is False


# ============================================================
# Task – recurrence
# ============================================================

def test_next_occurrence_returns_fresh_task():
    """next_occurrence() on a completed daily task returns a new incomplete task."""
    task = Task("Morning walk", duration_minutes=30, priority="high", frequency="daily")
    task.mark_complete()
    assert task.completed is True

    next_task = task.next_occurrence()

    assert next_task.completed is False
    assert next_task.title == task.title
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.priority == task.priority
    assert next_task.frequency == task.frequency


def test_next_occurrence_is_independent_copy():
    """Modifying the original task after calling next_occurrence() does not affect the copy."""
    task = Task("Play", duration_minutes=15, priority="medium", frequency="daily")
    copy = task.next_occurrence()
    task.mark_complete()   # mutate original
    assert copy.completed is False


def test_once_frequency_next_occurrence():
    """next_occurrence() still produces a fresh task even for 'once' tasks (caller decides logic)."""
    task = Task("Vet visit", duration_minutes=60, priority="high", frequency="once")
    task.mark_complete()
    next_task = task.next_occurrence()
    assert next_task.completed is False
    assert next_task.frequency == "once"


# ============================================================
# Pet – task management
# ============================================================

def test_add_task_increases_count():
    """add_task() should increase pet task count by 1."""
    pet = make_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    assert len(pet.get_tasks()) == 1


def test_remove_task_decreases_count():
    """remove_task() removes the matching task by title (case-insensitive)."""
    pet = make_pet()
    pet.add_task(Task("Breakfast", duration_minutes=5, priority="high"))
    pet.add_task(Task("Play",      duration_minutes=15, priority="medium"))
    pet.remove_task("Breakfast")
    titles = [t.title for t in pet.get_tasks()]
    assert "Breakfast" not in titles
    assert len(titles) == 1


def test_pet_with_no_tasks_returns_empty_list():
    """A pet with no tasks should return an empty list, not raise an error."""
    pet = make_pet()
    assert pet.get_tasks() == []


def test_remove_nonexistent_task_is_safe():
    """remove_task() on a title that doesn't exist should not raise and leave list unchanged."""
    pet = make_pet()
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    pet.remove_task("Nonexistent task")
    assert len(pet.get_tasks()) == 1


# ============================================================
# Owner – pet + task aggregation
# ============================================================

def test_owner_add_pet_increases_count():
    """add_pet() registers the pet under the owner."""
    owner = make_owner()
    assert len(owner.get_pets()) == 0
    owner.add_pet(make_pet())
    assert len(owner.get_pets()) == 1


def test_owner_remove_pet():
    """remove_pet() should remove the named pet."""
    owner = make_owner()
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    owner.remove_pet("Mochi")
    names = [p.name for p in owner.get_pets()]
    assert "Mochi" not in names
    assert "Luna" in names


def test_owner_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() returns every task from all pets combined."""
    owner = make_owner()
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    dog.add_task(Task("Walk",       duration_minutes=30, priority="high"))
    cat.add_task(Task("Litter box", duration_minutes=5,  priority="high"))
    cat.add_task(Task("Play",       duration_minutes=15, priority="medium"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 3


def test_owner_with_no_pets_returns_empty_task_list():
    """An owner with no pets should return an empty task list."""
    owner = make_owner()
    assert owner.get_all_tasks() == []


# ============================================================
# Scheduler – sorting correctness
# ============================================================

def test_scheduler_sorts_high_before_medium_before_low():
    """build_plan() returns tasks ordered high → medium → low priority."""
    owner = make_owner(60)
    pet   = make_pet()
    pet.add_task(Task("Play",    duration_minutes=10, priority="low"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    pet.add_task(Task("Brush",   duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    priorities = [t.priority for t in plan]
    assert priorities.index("high") < priorities.index("medium")
    assert priorities.index("medium") < priorities.index("low")


def test_scheduler_all_same_priority_includes_all_that_fit():
    """When all tasks share the same priority, all that fit in budget are included."""
    owner = make_owner(60)
    pet   = make_pet()
    for i in range(4):
        pet.add_task(Task(f"Task {i}", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert len(plan) == 4   # 4 × 10 min = 40 min, fits in 60


# ============================================================
# Scheduler – time budget
# ============================================================

def test_scheduler_respects_time_budget():
    """Total scheduled duration must not exceed the owner's time budget."""
    owner = make_owner(40)
    pet   = make_pet()
    pet.add_task(Task("Walk",    duration_minutes=30, priority="high"))
    pet.add_task(Task("Play",    duration_minutes=20, priority="medium"))  # won't fit
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert sum(t.duration_minutes for t in plan) <= 40


def test_scheduler_budget_smaller_than_all_tasks_returns_empty():
    """If every task exceeds the budget, the plan should be empty (not an error)."""
    owner = make_owner(5)
    pet   = make_pet()
    pet.add_task(Task("Walk", duration_minutes=30, priority="high"))
    pet.add_task(Task("Play", duration_minutes=20, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert plan == []


def test_scheduler_explicit_budget_overrides_owner_budget():
    """An explicit time_budget_minutes on the Scheduler takes precedence over owner budget."""
    owner = make_owner(90)
    pet   = make_pet()
    pet.add_task(Task("Walk",    duration_minutes=30, priority="high"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    # Restrict to 15 min — only Feeding should fit
    plan = Scheduler(owner=owner, pet=pet, time_budget_minutes=15).build_plan()
    assert sum(t.duration_minutes for t in plan) <= 15


# ============================================================
# Scheduler – completed task exclusion
# ============================================================

def test_completed_tasks_excluded_from_plan():
    """Tasks already marked complete must not appear in the plan."""
    owner = make_owner(60)
    pet   = make_pet()
    done  = Task("Walk", duration_minutes=30, priority="high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert all(not t.completed for t in plan)
    assert "Walk" not in [t.title for t in plan]


def test_all_tasks_completed_returns_empty_plan():
    """If every task is already done, the plan should be empty."""
    owner = make_owner(60)
    pet   = make_pet()
    for title in ("Walk", "Feeding", "Play"):
        t = Task(title, duration_minutes=10, priority="high")
        t.mark_complete()
        pet.add_task(t)
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert plan == []


# ============================================================
# Scheduler – edge cases
# ============================================================

def test_scheduler_pet_with_no_tasks_returns_empty_plan():
    """A pet with no tasks should produce an empty plan without errors."""
    owner = make_owner(60)
    pet   = make_pet()
    owner.add_pet(pet)

    plan = Scheduler(owner=owner, pet=pet).build_plan()
    assert plan == []


def test_explain_plan_empty_plan_message():
    """explain_plan() on an empty plan should return a descriptive message."""
    owner = make_owner(60)
    pet   = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, pet=pet)
    msg = scheduler.explain_plan([])
    assert "No tasks" in msg


# ============================================================
# Scheduler – conflict detection
# ============================================================

def test_get_conflicts_detects_duplicate_titles():
    """get_conflicts() should flag two tasks with the same title on the same pet."""
    owner = make_owner(60)
    pet   = make_pet()
    pet.add_task(Task("Morning walk", duration_minutes=30, priority="high"))
    pet.add_task(Task("Morning walk", duration_minutes=30, priority="high"))  # duplicate
    owner.add_pet(pet)

    conflicts = Scheduler(owner=owner, pet=pet).get_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0][0].title == conflicts[0][1].title


def test_get_conflicts_case_insensitive():
    """Conflict detection should be case-insensitive for title comparison."""
    owner = make_owner(60)
    pet   = make_pet()
    pet.add_task(Task("morning walk", duration_minutes=30, priority="high"))
    pet.add_task(Task("Morning Walk", duration_minutes=30, priority="medium"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner=owner, pet=pet).get_conflicts()
    assert len(conflicts) == 1


def test_get_conflicts_no_duplicates_returns_empty():
    """get_conflicts() should return an empty list when all titles are unique."""
    owner = make_owner(60)
    pet   = make_pet()
    pet.add_task(Task("Walk",    duration_minutes=30, priority="high"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    pet.add_task(Task("Play",    duration_minutes=15, priority="medium"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner=owner, pet=pet).get_conflicts()
    assert conflicts == []
