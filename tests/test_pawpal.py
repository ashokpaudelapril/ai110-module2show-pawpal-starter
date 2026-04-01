"""
tests/test_pawpal.py – unit tests for PawPal+ core logic.

Run with:  python -m pytest
"""

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Task tests ─────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_reset_clears_completed_status():
    """reset() should flip completed back to False."""
    task = Task(title="Breakfast", duration_minutes=10, priority="high")
    task.mark_complete()
    task.reset()
    assert task.completed is False


# ── Pet tests ──────────────────────────────────────────────────────────────

def test_add_task_increases_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    assert len(pet.get_tasks()) == 1


def test_remove_task_decreases_count():
    """remove_task() should remove the matching task from the pet."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Breakfast", duration_minutes=5, priority="high"))
    pet.add_task(Task("Play", duration_minutes=15, priority="medium"))
    pet.remove_task("Breakfast")
    titles = [t.title for t in pet.get_tasks()]
    assert "Breakfast" not in titles
    assert len(titles) == 1


# ── Owner tests ────────────────────────────────────────────────────────────

def test_owner_add_pet_increases_count():
    """add_pet() should register the pet under the owner."""
    owner = Owner(name="Jordan", available_minutes=60)
    assert len(owner.get_pets()) == 0
    owner.add_pet(Pet(name="Mochi", species="dog"))
    assert len(owner.get_pets()) == 1


def test_owner_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() should return tasks from every pet."""
    owner = Owner(name="Jordan", available_minutes=90)
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna",  species="cat")
    dog.add_task(Task("Walk",      duration_minutes=30, priority="high"))
    cat.add_task(Task("Litter box",duration_minutes=5,  priority="high"))
    cat.add_task(Task("Play",      duration_minutes=15, priority="medium"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 3


# ── Scheduler tests ────────────────────────────────────────────────────────

def test_scheduler_respects_time_budget():
    """build_plan() must not exceed the available time budget."""
    owner = Owner(name="Jordan", available_minutes=40)
    pet   = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk",    duration_minutes=30, priority="high"))
    pet.add_task(Task("Play",    duration_minutes=20, priority="medium"))  # won't fit
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, pet=pet)
    plan = scheduler.build_plan()
    total = sum(t.duration_minutes for t in plan)
    assert total <= 40


def test_scheduler_prioritises_high_tasks_first():
    """High-priority tasks should appear before lower-priority ones in the plan."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet   = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Play",    duration_minutes=10, priority="low"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    pet.add_task(Task("Brush",   duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, pet=pet)
    plan = scheduler.build_plan()
    priorities = [t.priority for t in plan]
    # high must come before medium, medium before low
    assert priorities.index("high") < priorities.index("medium")
    assert priorities.index("medium") < priorities.index("low")


def test_completed_tasks_excluded_from_plan():
    """Tasks already marked complete should not appear in the plan."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet   = Pet(name="Mochi", species="dog")
    done  = Task("Walk", duration_minutes=30, priority="high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, pet=pet)
    plan = scheduler.build_plan()
    assert all(not t.completed for t in plan)
    assert "Walk" not in [t.title for t in plan]
