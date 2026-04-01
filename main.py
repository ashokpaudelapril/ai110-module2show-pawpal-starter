"""
main.py – demo / smoke-test script for PawPal+ logic.

Demonstrates: scheduling, priority sorting, task filtering, conflict detection,
and recurring task behaviour.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def section(title: str) -> None:
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print('=' * 55)


def main() -> None:
    # ── Owner ──────────────────────────────────────────────────────────────
    jordan = Owner(name="Jordan", available_minutes=90)

    # ── Pets ───────────────────────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", age_years=3)
    luna  = Pet(name="Luna",  species="cat", age_years=5)

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Tasks added out of order (low priority first) ──────────────────────
    mochi.add_task(Task("Grooming brush", duration_minutes=15, priority="low",    category="grooming",    frequency="weekly"))
    mochi.add_task(Task("Fetch / play",   duration_minutes=20, priority="medium", category="enrichment",  frequency="daily"))
    mochi.add_task(Task("Breakfast",      duration_minutes=10, priority="high",   category="feeding",     frequency="daily"))
    mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="exercise",    frequency="daily"))

    luna.add_task(Task("Interactive play",duration_minutes=15, priority="medium", category="enrichment",  frequency="daily"))
    luna.add_task(Task("Litter box",      duration_minutes=5,  priority="high",   category="hygiene",     frequency="daily"))
    luna.add_task(Task("Breakfast",       duration_minutes=5,  priority="high",   category="feeding",     frequency="daily"))

    # ── 1. Priority-sorted daily schedules ────────────────────────────────
    section("1. Today's Schedule (sorted high → low priority)")
    for pet in jordan.get_pets():
        scheduler = Scheduler(owner=jordan, pet=pet)
        plan = scheduler.build_plan()
        print()
        print(scheduler.explain_plan(plan))

    # ── 2. Filtering demo ─────────────────────────────────────────────────
    section("2. Filtering demo")

    mochi_sched = Scheduler(owner=jordan, pet=mochi)

    # Mark one task complete to show filtering
    mochi.tasks[2].mark_complete()   # Breakfast marked done

    incomplete = mochi_sched.filter_tasks(completed=False)
    done       = mochi_sched.filter_tasks(completed=True)
    print(f"\nMochi — incomplete tasks ({len(incomplete)}):")
    for t in incomplete:
        print(f"  • {t.title} [{t.priority}]")
    print(f"\nMochi — completed tasks ({len(done)}):")
    for t in done:
        print(f"  ✓ {t.title}")

    # Filter by pet name via owner's scheduler
    luna_tasks = mochi_sched.filter_tasks(pet_name="Luna")
    print(f"\nLuna's tasks via filter_tasks(pet_name='Luna') ({len(luna_tasks)}):")
    for t in luna_tasks:
        print(f"  • {t.title} [{t.priority}]")

    # ── 3. Conflict detection demo ────────────────────────────────────────
    section("3. Conflict detection demo")

    # Add a duplicate task to trigger a conflict
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high", category="exercise"))
    conflicts = Scheduler(owner=jordan, pet=mochi).get_conflicts()
    if conflicts:
        for t1, t2 in conflicts:
            print(f"  ⚠ Conflict: '{t1.title}' appears twice on {mochi.name}'s task list")
    mochi.remove_task("Morning walk")   # clean up duplicate
    mochi.remove_task("Morning walk")   # remove original too, then re-add
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high", category="exercise", frequency="daily"))
    print("  Conflict resolved — duplicate removed.")

    # ── 4. Recurrence demo ────────────────────────────────────────────────
    section("4. Recurrence demo")

    walk = next(t for t in mochi.get_tasks() if t.title == "Morning walk")
    print(f"\nBefore: '{walk.title}' completed={walk.completed}")
    walk.mark_complete()
    next_walk = walk.next_occurrence()
    print(f"After mark_complete: completed={walk.completed}")
    print(f"next_occurrence(): '{next_walk.title}' completed={next_walk.completed} frequency={next_walk.frequency}")

    # ── 5. Summary ────────────────────────────────────────────────────────
    section("5. Summary")
    all_tasks = jordan.get_all_tasks()
    print(f"\nTotal tasks across all pets : {len(all_tasks)}")
    total_time = sum(t.duration_minutes for t in all_tasks)
    print(f"Total care time (all tasks) : {total_time} min")
    print(f"Jordan's daily budget       : {jordan.available_minutes} min")


if __name__ == "__main__":
    main()
