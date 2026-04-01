"""
main.py – demo / smoke-test script for PawPal+ logic.

Demonstrates: weighted scheduling, priority sorting, filtering,
conflict detection, recurrence, JSON persistence, and tabulate CLI output.

Run with:  python main.py
"""

from tabulate import tabulate

from pawpal_system import Owner, Pet, Task, Scheduler

DATA_FILE = "demo_data.json"


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main() -> None:
    # ── Owner + pets ───────────────────────────────────────────────────────
    jordan = Owner(name="Jordan", available_minutes=90)
    mochi  = Pet(name="Mochi", species="dog", age_years=3)
    luna   = Pet(name="Luna",  species="cat", age_years=5)
    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # Tasks added out of order (low priority first) to prove sorting works
    mochi.add_task(Task("Grooming brush", 15, "low",    "grooming",    frequency="weekly"))
    mochi.add_task(Task("Fetch / play",   20, "medium", "enrichment",  frequency="daily"))
    mochi.add_task(Task("Medication",     10, "high",   "medication",  frequency="daily"))
    mochi.add_task(Task("Breakfast",      10, "high",   "feeding",     frequency="daily"))
    mochi.add_task(Task("Morning walk",   30, "high",   "exercise",    frequency="daily"))

    luna.add_task(Task("Interactive play", 15, "medium", "enrichment", frequency="daily"))
    luna.add_task(Task("Litter box",        5, "high",   "hygiene",    frequency="daily"))
    luna.add_task(Task("Breakfast",         5, "high",   "feeding",    frequency="daily"))

    # ── 1. Priority-based schedule ─────────────────────────────────────────
    section("1. Priority-based schedule (high → medium → low)")
    for pet in jordan.get_pets():
        s    = Scheduler(owner=jordan, pet=pet)
        plan = s.build_plan()
        rows = []
        hour, minute = 8, 0
        for t in plan:
            start = f"{hour:02d}:{minute:02d}"
            em = minute + t.duration_minutes
            eh = hour + em // 60
            em = em % 60
            rows.append([f"{start}–{eh:02d}:{em:02d}", t.priority, t.title,
                          t.category, t.duration_minutes, t.frequency])
            hour, minute = eh, em
        print(f"\n{pet.name}")
        print(tabulate(rows, headers=["Time", "Priority", "Task", "Category", "Min", "Freq"],
                       tablefmt="rounded_outline"))

    # ── 2. Weighted schedule ───────────────────────────────────────────────
    section("2. Weighted schedule (priority + frequency + category score)")
    s    = Scheduler(owner=jordan, pet=mochi)
    plan = s.build_weighted_plan()
    rows = []
    hour, minute = 8, 0
    for t in plan:
        start = f"{hour:02d}:{minute:02d}"
        em = minute + t.duration_minutes
        eh = hour + em // 60
        em = em % 60
        rows.append([f"{start}–{eh:02d}:{em:02d}", t.weight(), t.priority,
                      t.title, t.category, t.duration_minutes])
        hour, minute = eh, em
    print(f"\n{mochi.name} (weighted)")
    print(tabulate(rows, headers=["Time", "Score", "Priority", "Task", "Category", "Min"],
                   tablefmt="rounded_outline"))

    # ── 3. Filtering ───────────────────────────────────────────────────────
    section("3. Filtering demo")
    mochi.tasks[2].mark_complete()   # mark Medication done
    incomplete = s.filter_tasks(completed=False)
    done       = s.filter_tasks(completed=True)
    print(f"\nIncomplete ({len(incomplete)}): {[t.title for t in incomplete]}")
    print(f"Completed  ({len(done)}):   {[t.title for t in done]}")

    # ── 4. Conflict detection ──────────────────────────────────────────────
    section("4. Conflict detection demo")
    mochi.add_task(Task("Morning walk", 30, "high", "exercise"))   # duplicate
    for t1, t2 in Scheduler(owner=jordan, pet=mochi).get_conflicts():
        print(f"  ⚠  Conflict: '{t1.title}' appears twice on {mochi.name}'s list")
    mochi.remove_task("Morning walk")
    mochi.remove_task("Morning walk")
    mochi.add_task(Task("Morning walk", 30, "high", "exercise", frequency="daily"))
    print("  Resolved.")

    # ── 5. Recurrence ─────────────────────────────────────────────────────
    section("5. Recurrence demo")
    walk = next(t for t in mochi.get_tasks() if t.title == "Morning walk")
    walk.mark_complete()
    nxt = walk.next_occurrence()
    print(tabulate(
        [[walk.title, walk.completed, walk.frequency],
         [nxt.title,  nxt.completed,  nxt.frequency]],
        headers=["Task", "Completed", "Frequency"],
        tablefmt="rounded_outline",
    ))

    # ── 6. JSON persistence ────────────────────────────────────────────────
    section("6. JSON persistence (Challenge 2)")
    jordan.save_to_json(DATA_FILE)
    print(f"  Saved to {DATA_FILE}")
    loaded = Owner.load_from_json(DATA_FILE)
    print(f"  Loaded:  {loaded.name}, {len(loaded.get_pets())} pets, "
          f"{len(loaded.get_all_tasks())} tasks")

    # ── 7. Summary ────────────────────────────────────────────────────────
    section("7. Summary")
    all_tasks = jordan.get_all_tasks()
    print(tabulate(
        [[jordan.name, jordan.available_minutes, len(jordan.get_pets()),
          len(all_tasks), sum(t.duration_minutes for t in all_tasks)]],
        headers=["Owner", "Budget (min)", "Pets", "Total tasks", "Total care time (min)"],
        tablefmt="rounded_outline",
    ))


if __name__ == "__main__":
    main()
