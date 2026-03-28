from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


DATA_FILE = Path("data.json")


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet-care planning with sorting, filtering, conflict warnings, and recurring tasks.")


@st.cache_data(show_spinner=False)
def today_label() -> str:
    return date.today().strftime("%A, %B %d, %Y")


def save_owner() -> None:
    st.session_state.owner.save_to_json(str(DATA_FILE))


def load_owner() -> Owner:
    if DATA_FILE.exists():
        return Owner.load_from_json(str(DATA_FILE))
    return Owner(name="Jordan", email="jordan@example.com")


if "owner" not in st.session_state:
    st.session_state.owner = load_owner()

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


with st.expander("About PawPal+", expanded=True):
    st.markdown(
        """
PawPal+ helps pet owners manage care tasks across multiple pets.

Current smart features:
- **Chronological sorting** across all pets
- **Priority-based scheduling** for urgent tasks
- **Filtering** by pet, status, and priority
- **Conflict detection** for overlapping start times
- **Recurring task regeneration** for daily and weekly routines
- **JSON persistence** so your pets/tasks can survive app restarts
        """
    )

st.subheader("Owner")
owner_name = st.text_input("Owner name", value=owner.name)
owner_email = st.text_input("Owner email", value=owner.email)
if st.button("Update owner profile"):
    owner.name = owner_name
    owner.email = owner_email
    save_owner()
    st.success("Owner profile updated.")

st.divider()

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["Dog", "Cat", "Other"])
    age = st.number_input("Age", min_value=0, max_value=40, value=1)
    notes = st.text_input("Notes", placeholder="Favorite treats, medication reminders, etc.")
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if not pet_name.strip():
        st.error("Pet name is required.")
    elif owner.get_pet(pet_name):
        st.warning(f"{pet_name.strip()} already exists.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age), notes=notes.strip()))
        save_owner()
        st.success(f"Added {pet_name.strip()} to PawPal+.")

if owner.pets:
    st.markdown("### Current pets")
    st.table(
        [
            {
                "Pet": pet.name,
                "Species": pet.species,
                "Age": pet.age,
                "Notes": pet.notes or "—",
                "Tasks": pet.task_count(),
            }
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets added yet.")

st.divider()

st.subheader("Add a Task")
if owner.pets:
    with st.form("add_task_form", clear_on_submit=True):
        chosen_pet = st.selectbox("Assign to pet", [pet.name for pet in owner.pets])
        description = st.text_input("Task description", placeholder="Morning walk")
        due_date = st.date_input("Due date", value=date.today())
        due_time = st.time_input("Due time", value=datetime.now().replace(second=0, microsecond=0).time())
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=30)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        task_type = st.selectbox(
            "Task type", ["feeding", "exercise", "medical", "grooming", "appointment", "general"]
        )
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        pet = owner.get_pet(chosen_pet)
        if pet is None:
            st.error("That pet could not be found.")
        elif not description.strip():
            st.error("Task description is required.")
        else:
            pet.add_task(
                Task(
                    description=description.strip(),
                    due_date=due_date,
                    due_time=due_time,
                    frequency=frequency,
                    priority=priority,
                    duration_minutes=int(duration),
                    task_type=task_type,
                )
            )
            save_owner()
            st.success(f"Added '{description.strip()}' for {chosen_pet}.")
else:
    st.info("Add a pet before creating tasks.")

st.divider()

st.subheader(f"Today's Schedule — {today_label()}")
if owner.pets and scheduler.get_all_tasks(include_completed=True):
    sort_mode = st.radio(
        "Schedule view",
        options=["time", "priority"],
        horizontal=True,
        format_func=lambda value: "Sort by time" if value == "time" else "Sort by priority",
    )
    show_completed = st.toggle("Show completed tasks", value=True)
    selected_pet = st.selectbox("Filter by pet", ["All pets"] + [pet.name for pet in owner.pets])
    selected_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    selected_priority = st.selectbox("Filter by priority", ["All", "low", "medium", "high"])

    rows = scheduler.agenda_table(sort_mode=sort_mode, include_completed=show_completed)

    if selected_pet != "All pets":
        rows = [row for row in rows if row["Pet"] == selected_pet]
    if selected_status != "All":
        desired = "✅ Complete" if selected_status == "Completed" else "⏳ Pending"
        rows = [row for row in rows if row["Status"] == desired]
    if selected_priority != "All":
        rows = [row for row in rows if selected_priority.title() in row["Priority"]]

    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No tasks match the current filters.")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")

    st.markdown("### Mark a task complete")
    pending_options = [
        f"{pet.name} — {task.description} ({task.due_date.isoformat()} {task.due_time.strftime('%H:%M')})"
        for pet, task in scheduler.get_all_tasks(include_completed=False)
    ]
    if pending_options:
        chosen_label = st.selectbox("Pending tasks", pending_options)
        if st.button("Complete selected task"):
            pet_name, remainder = chosen_label.split(" — ", maxsplit=1)
            description = remainder.split(" (", maxsplit=1)[0]
            updated = scheduler.mark_task_complete(pet_name, description)
            if updated:
                save_owner()
                st.success(f"Completed '{description}' for {pet_name}.")
                if updated.frequency != "once":
                    st.info(f"Recurring task regenerated for the next {updated.frequency} cycle.")
            else:
                st.error("Unable to complete that task.")
    else:
        st.info("There are no pending tasks to complete.")

    st.markdown("### Planning helper")
    with st.form("slot_form"):
        slot_date = st.date_input("Find next available slot on", value=date.today(), key="slot_date")
        slot_duration = st.number_input("Needed duration (minutes)", min_value=1, max_value=240, value=20)
        slot_submitted = st.form_submit_button("Find slot")
    if slot_submitted:
        slot = scheduler.next_available_slot(slot_date, int(slot_duration))
        if slot:
            st.success(f"Next available slot: {slot.strftime('%H:%M')}")
        else:
            st.warning("No open slot found in the default 08:00–20:00 planning window.")
else:
    st.info("Add pets and tasks to generate a schedule.")

st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("Save data now"):
        save_owner()
        st.success("Data saved to data.json.")
with col2:
    if st.button("Reload from saved data"):
        st.session_state.owner = load_owner()
        st.success("Reloaded owner, pets, and tasks from data.json.")
