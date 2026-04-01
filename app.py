import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# Challenge 2: load persisted Owner from data.json on first run so pets and
# tasks survive browser refreshes and app restarts.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json(DATA_FILE)  # None if no file yet


def _save() -> None:
    """Persist current owner state to data.json (Challenge 2)."""
    if st.session_state.owner is not None:
        st.session_state.owner.save_to_json(DATA_FILE)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+")
st.caption("A daily pet-care planner — weighted scheduling, conflict detection, and persistent data.")

# ---------------------------------------------------------------------------
# Section 1 – Owner setup
# ---------------------------------------------------------------------------

st.header("1. Owner info")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input(
            "Your name",
            value=st.session_state.owner.name if st.session_state.owner else "Jordan",
        )
    with col2:
        available_minutes = st.number_input(
            "Time available today (minutes)",
            min_value=10, max_value=480,
            value=st.session_state.owner.available_minutes if st.session_state.owner else 90,
            step=10,
        )
    save_owner = st.form_submit_button("Save owner")

if save_owner:
    existing_pets = st.session_state.owner.get_pets() if st.session_state.owner else []
    st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    _save()
    st.success(f"Owner saved: **{owner_name}** — {available_minutes} min available today.")

if st.session_state.owner is None:
    st.info("Fill in your name and save to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 – Add a pet
# ---------------------------------------------------------------------------

st.header("2. Add a pet")

with st.form("add_pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    notes = st.text_input("Notes (optional)", value="")
    add_pet_btn = st.form_submit_button("Add pet")

if add_pet_btn:
    existing_names = [p.name.lower() for p in owner.get_pets()]
    if pet_name.lower() in existing_names:
        st.warning(f"A pet named **{pet_name}** is already registered.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species, age_years=age, notes=notes))
        _save()
        st.success(f"Added {species} **{pet_name}**!")

pets = owner.get_pets()
if pets:
    st.write(f"**Registered pets ({len(pets)}):**")
    for p in pets:
        badge = {"dog": "🐶", "cat": "🐱"}.get(p.species, "🐾")
        note_str = f" · *{p.notes}*" if p.notes else ""
        st.write(f"  {badge} **{p.name}** — {p.species}, {p.age_years} yr{note_str}")
else:
    st.info("No pets yet — add one above.")

# ---------------------------------------------------------------------------
# Section 3 – Add a care task
# ---------------------------------------------------------------------------

st.header("3. Add a care task")

if not pets:
    st.info("Add at least one pet first.")
else:
    with st.form("add_task_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_pet = st.selectbox("For which pet?", [p.name for p in pets])
        with col2:
            task_title = st.text_input("Task title", value="Morning walk")
        col3, col4, col5, col6 = st.columns(4)
        with col3:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col4:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        with col5:
            category = st.selectbox(
                "Category",
                ["exercise", "feeding", "enrichment", "grooming", "hygiene", "medication", "general"],
            )
        with col6:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        add_task_btn = st.form_submit_button("Add task")

    if add_task_btn:
        pet_obj = next(p for p in pets if p.name == target_pet)
        pet_obj.add_task(
            Task(title=task_title, duration_minutes=int(duration),
                 priority=priority, category=category, frequency=frequency)
        )
        _save()
        st.success(f"Added **{task_title}** to {target_pet}.")

    # ── Conflict warnings ────────────────────────────────────────────────
    for pet in pets:
        for t1, t2 in Scheduler(owner=owner, pet=pet).get_conflicts():
            st.warning(
                f"⚠️ **Conflict on {pet.name}:** Two tasks share the name **\"{t1.title}\"**. "
                f"Consider renaming or removing one."
            )

    # ── Task list (Challenge 3: colour-coded priority icons) ─────────────
    st.write("**Current tasks:**")
    any_tasks = False
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    for pet in pets:
        tasks = pet.get_tasks()
        if tasks:
            any_tasks = True
            st.write(f"*{pet.name}*")
            rows = [
                {
                    "Priority": f"{priority_icon.get(t.priority, '')} {t.priority}",
                    "Title": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Category": t.category,
                    "Frequency": t.frequency,
                    "Score": t.weight(),
                    "Done": "✓" if t.completed else "",
                }
                for t in sorted(tasks, key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t.priority, 9))
            ]
            st.table(rows)
    if not any_tasks:
        st.info("No tasks yet — add some above.")

# ---------------------------------------------------------------------------
# Section 4 – Generate today's schedule
# ---------------------------------------------------------------------------

st.header("4. Generate today's schedule")

if not pets:
    st.info("Add pets and tasks first.")
else:
    selected_pet_name = st.selectbox("Schedule for:", [p.name for p in pets], key="schedule_pet")
    pet_to_schedule = next(p for p in pets if p.name == selected_pet_name)

    # Challenge 1: let user choose scheduling mode
    mode = st.radio(
        "Scheduling mode",
        ["Priority (high → medium → low)", "Weighted (priority + frequency + category)"],
        horizontal=True,
    )
    use_weighted = mode.startswith("Weighted")

    if st.button("Generate schedule"):
        scheduler = Scheduler(owner=owner, pet=pet_to_schedule)

        # Conflict check
        for t1, t2 in scheduler.get_conflicts():
            st.warning(
                f"⚠️ **Conflict:** Task **\"{t1.title}\"** appears twice. "
                f"First occurrence will be scheduled; duplicate skipped."
            )

        plan = scheduler.build_weighted_plan() if use_weighted else scheduler.build_plan()

        if not plan:
            st.warning(
                "No tasks could be scheduled. Either all tasks are already complete, "
                "or none fit within today's time budget."
            )
        else:
            total_min = sum(t.duration_minutes for t in plan)
            budget = owner.available_minutes
            label = "weighted score" if use_weighted else "priority"
            st.success(
                f"Scheduled **{len(plan)} task(s)** for {selected_pet_name} "
                f"using **{label}** ordering — {total_min} of {budget} min used."
            )

            # Schedule table (Challenge 3 & 4: colour-coded priority)
            rows = []
            hour, minute = 8, 0
            for task in plan:
                start = f"{hour:02d}:{minute:02d}"
                end_m = minute + task.duration_minutes
                end_h = hour + end_m // 60
                end_m = end_m % 60
                end = f"{end_h:02d}:{end_m:02d}"
                rows.append({
                    "Time":           f"{start} – {end}",
                    "Priority":       f"{priority_icon.get(task.priority, '')} {task.priority}",
                    "Score":          task.weight() if use_weighted else "—",
                    "Task":           task.title,
                    "Category":       task.category,
                    "Duration (min)": task.duration_minutes,
                    "Recurring":      task.frequency,
                })
                hour, minute = end_h, end_m

            st.table(rows)

            # Skipped tasks
            all_incomplete = [t for t in pet_to_schedule.get_tasks() if not t.completed]
            skipped = [t for t in all_incomplete if t not in plan]
            if skipped:
                skipped_names = ", ".join(f"**{t.title}**" for t in skipped)
                st.info(
                    f"ℹ️ {len(skipped)} task(s) skipped (didn't fit in budget): {skipped_names}."
                )

            with st.expander("Why was this plan chosen?"):
                st.text(scheduler.explain_plan(plan, weighted=use_weighted))

            # Mark complete + recurrence
            st.write("**Mark tasks complete:**")
            for task in plan:
                if not task.completed:
                    if st.button(f"✅ Done: {task.title}", key=f"done_{task.title}"):
                        task.mark_complete()
                        if task.frequency in ("daily", "weekly"):
                            pet_to_schedule.add_task(task.next_occurrence())
                            st.toast(
                                f"'{task.title}' done. Next {task.frequency} occurrence queued.",
                                icon="🔁",
                            )
                        _save()
                        st.rerun()
                else:
                    st.write(f"~~{task.title}~~ ✓")

# ---------------------------------------------------------------------------
# Sidebar – data management (Challenge 2)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("💾 Data")
    st.caption(f"Auto-saved to `{DATA_FILE}` after every change.")
    if st.button("🗑️ Reset all data"):
        import os
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.owner = None
        st.rerun()
