"""Streamlit interface for creating pets, care tasks, and daily schedules."""

from datetime import date, time

import streamlit as st

from pawpal_system import FREQUENCIES, PRIORITY_ORDER, Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan care across all your pets, prioritize important tasks, and make time for each one.")

if "owner" not in st.session_state:
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", "dog"))
    st.session_state.owner = owner

owner: Owner = st.session_state.owner
owner.name = st.text_input("Owner name", value=owner.name)

with st.expander("Your pets", expanded=True):
    if owner.pets:
        st.write(", ".join(f"{pet.name} ({pet.species})" for pet in owner.pets))
    else:
        st.info("Add a pet to start planning care.")
    with st.form("add_pet_form", clear_on_submit=True):
        new_pet_name = st.text_input("Pet name")
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
        add_pet = st.form_submit_button("Add pet")
    if add_pet:
        try:
            owner.add_pet(Pet(new_pet_name, new_pet_species))
            st.success(f"Added {new_pet_name.strip()} to your pets.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

if owner.pets:
    st.subheader("Care tasks")
    pet_by_id = {pet.id: pet for pet in owner.pets}
    with st.form("add_task_form", clear_on_submit=True):
        pet_id = st.selectbox(
            "Pet",
            options=list(pet_by_id),
            format_func=lambda selected_id: pet_by_id[selected_id].name,
        )
        description = st.text_input("Task", placeholder="Morning walk")
        first, second, third = st.columns(3)
        with first:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, value=20)
        with second:
            priority = st.selectbox("Priority", list(PRIORITY_ORDER), index=0)
        with third:
            frequency = st.selectbox("Frequency", sorted(FREQUENCIES))
        preferred_time = st.time_input("Preferred start time", value=time(8, 0))
        due_date = st.date_input("Due date / weekday for weekly tasks", value=date.today())
        add_task = st.form_submit_button("Add task")
    if add_task:
        try:
            pet_by_id[pet_id].add_task(
                Task(
                    description,
                    time=preferred_time,
                    frequency=frequency,
                    duration_minutes=int(duration),
                    priority=priority,
                    due_date=due_date if frequency != "daily" else None,
                )
            )
            st.success("Task added.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    tasks = owner.get_all_tasks()
    if tasks:
        st.markdown("#### Current tasks")
        filter_pet = st.selectbox(
            "Filter by pet",
            options=["All pets", *[pet.name for pet in owner.pets]],
        )
        filter_status = st.selectbox(
            "Filter by status", ["All tasks", "Incomplete", "Complete"]
        )
        selected_status = {
            "All tasks": None,
            "Incomplete": False,
            "Complete": True,
        }[filter_status]
        displayed_tasks = Scheduler(owner).filter_tasks(
            pet_name=None if filter_pet == "All pets" else filter_pet,
            is_complete=selected_status,
        )
        displayed_tasks = Scheduler(owner).sort_by_time(displayed_tasks)
        if not displayed_tasks:
            st.info("No tasks match these filters.")
        for pet, task in displayed_tasks:
            with st.container(border=True):
                status = "Complete" if task.is_complete else "To do"
                st.markdown(
                    f"**{task.description}** — {pet.name} · {task.duration_minutes} min · "
                    f"{task.priority} priority · {task.frequency} · {status}"
                )
                if not task.is_complete and st.button(
                    "Mark complete", key=f"complete_{task.id}"
                ):
                    Scheduler(owner).complete_task(pet, task)
                    st.rerun()

        st.markdown("#### Edit a task")
        tasks_by_id = {task.id: (pet, task) for pet, task in tasks}
        selected_task_id = st.selectbox(
            "Choose a task",
            options=list(tasks_by_id),
            format_func=lambda task_id: (
                f"{tasks_by_id[task_id][1].description} "
                f"({tasks_by_id[task_id][0].name})"
            ),
        )
        selected_pet, selected_task = tasks_by_id[selected_task_id]
        with st.form(f"edit_task_{selected_task.id}"):
            edited_description = st.text_input(
                "Task description",
                value=selected_task.description,
                key=f"edit_description_{selected_task.id}",
            )
            edited_duration = st.number_input(
                "Duration in minutes",
                min_value=1,
                max_value=1440,
                value=selected_task.duration_minutes,
                key=f"edit_duration_{selected_task.id}",
            )
            edited_priority = st.selectbox(
                "Task priority",
                list(PRIORITY_ORDER),
                index=PRIORITY_ORDER[selected_task.priority],
                key=f"edit_priority_{selected_task.id}",
            )
            edited_frequency = st.selectbox(
                "Task frequency",
                sorted(FREQUENCIES),
                index=sorted(FREQUENCIES).index(selected_task.frequency),
                key=f"edit_frequency_{selected_task.id}",
            )
            edited_time = st.time_input(
                "Preferred start time",
                value=selected_task.time or time(8, 0),
                key=f"edit_time_{selected_task.id}",
            )
            edited_due_date = st.date_input(
                "Due date / weekday for weekly tasks",
                value=selected_task.due_date or date.today(),
                key=f"edit_due_date_{selected_task.id}",
            )
            save_task = st.form_submit_button("Save changes")
        if save_task:
            try:
                selected_task.update(
                    edited_description,
                    int(edited_duration),
                    edited_priority,
                    edited_time,
                    edited_frequency,
                    edited_due_date if edited_frequency != "daily" else None,
                )
                st.success("Task updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if st.button("Delete selected task", key=f"delete_{selected_task.id}"):
            selected_pet.remove_task(selected_task.id)
            st.rerun()

    st.divider()
    st.subheader("Build today's schedule")
    with st.form("schedule_form"):
        schedule_start = st.time_input("Start of available time", value=time(8, 0))
        available_minutes = st.number_input(
            "Available minutes", min_value=1, max_value=960, value=120
        )
        generate_schedule = st.form_submit_button("Generate schedule")
    if generate_schedule:
        try:
            plan = Scheduler(owner).generate_schedule(
                schedule_date=date.today(),
                day_start=schedule_start,
                available_minutes=int(available_minutes),
            )
            st.markdown(f"### Today's plan · {plan['total_minutes']} min scheduled")
            if plan["scheduled_tasks"]:
                for item in plan["scheduled_tasks"]:
                    st.markdown(
                        f"- **{item['start_time']:%H:%M}–{item['end_time']:%H:%M}** · "
                        f"{item['pet_name']}: {item['description']} "
                        f"({item['duration_minutes']} min, {item['priority']} priority)"
                    )
                    st.caption(item["reason"])
            if plan["conflicts"]:
                    st.warning("Some preferred task times overlap. The schedule below avoids conflicts:")
                    for conflict in plan["conflicts"]:
                        st.write(f"- {conflict['message']}")
            else:
                st.info("No incomplete tasks are due today.")
            if plan["unscheduled_tasks"]:
                st.warning("Some tasks did not fit in the available time:")
                for item in plan["unscheduled_tasks"]:
                    st.write(f"- {item['pet_name']}: {item['description']} — {item['reason']}")
        except ValueError as error:
            st.error(str(error))
else:
    st.info("Add a pet above to create tasks and build a schedule.")
