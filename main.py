"""
main.py – demo / smoke-test script for PawPal+ logic.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # ── Owner ──────────────────────────────────────────────────────────────
    jordan = Owner(name="Jordan", available_minutes=90)

    # ── Pets ───────────────────────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", age_years=3)
    luna  = Pet(name="Luna",  species="cat", age_years=5)

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Tasks for Mochi (dog) ──────────────────────────────────────────────
    mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="exercise"))
    mochi.add_task(Task("Breakfast",      duration_minutes=10, priority="high",   category="feeding"))
    mochi.add_task(Task("Fetch / play",   duration_minutes=20, priority="medium", category="enrichment"))
    mochi.add_task(Task("Grooming brush", duration_minutes=15, priority="low",    category="grooming"))

    # ── Tasks for Luna (cat) ───────────────────────────────────────────────
    luna.add_task(Task("Breakfast",       duration_minutes=5,  priority="high",   category="feeding"))
    luna.add_task(Task("Litter box",      duration_minutes=5,  priority="high",   category="hygiene"))
    luna.add_task(Task("Interactive play",duration_minutes=15, priority="medium", category="enrichment"))

    # ── Build and display schedules ────────────────────────────────────────
    print("=" * 55)
    print("  PawPal+  –  Today's Schedule")
    print("=" * 55)

    for pet in jordan.get_pets():
        scheduler = Scheduler(owner=jordan, pet=pet)
        plan      = scheduler.build_plan()
        print()
        print(scheduler.explain_plan(plan))

    # ── Summary across all pets ────────────────────────────────────────────
    all_tasks = jordan.get_all_tasks()
    print()
    print(f"Total tasks defined across all pets: {len(all_tasks)}")
    total_time = sum(t.duration_minutes for t in all_tasks)
    print(f"Total care time if all tasks are done: {total_time} min")


if __name__ == "__main__":
    main()
