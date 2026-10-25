from datetime import date, time

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status() -> None:
    task = Task("Feed the cat")

    task.mark_complete()

    assert task.is_complete is True


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet("Mochi", "dog")

    pet.add_task(Task("Morning walk"))

    assert len(pet.tasks) == 1


def test_scheduler_includes_tasks_from_every_pet() -> None:
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    dog.add_task(Task("Walk", time="08:00", duration_minutes=20))
    cat.add_task(Task("Feed", time="08:30", duration_minutes=10))
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).generate_schedule(
        schedule_date=date(2026, 10, 24), day_start=time(8, 0)
    )

    assert [item["pet_name"] for item in result["scheduled_tasks"]] == ["Mochi", "Luna"]
    assert len(owner.get_all_tasks()) == 2


def test_scheduler_prioritizes_high_priority_when_time_is_limited() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Long low priority", duration_minutes=45, priority="low"))
    pet.add_task(Task("Short high priority", duration_minutes=15, priority="high"))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule(available_minutes=20)

    assert [item["description"] for item in result["scheduled_tasks"]] == [
        "Short high priority"
    ]
    assert result["unscheduled_tasks"][0]["description"] == "Long low priority"


def test_scheduler_skips_completed_and_not_due_tasks() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    completed = Task("Already done")
    completed.mark_complete()
    pet.add_task(completed)
    pet.add_task(Task("Future one-off", frequency="once", due_date=date(2026, 10, 25)))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule(schedule_date=date(2026, 10, 24))

    assert result["scheduled_tasks"] == []
    assert result["unscheduled_tasks"] == []


def test_weekly_task_is_due_on_its_anchor_weekday() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(
        Task("Weekly grooming", frequency="weekly", due_date=date(2026, 10, 24))
    )
    owner.add_pet(pet)

    due = Scheduler(owner).generate_schedule(schedule_date=date(2026, 10, 31))
    not_due = Scheduler(owner).generate_schedule(schedule_date=date(2026, 10, 30))

    assert len(due["scheduled_tasks"]) == 1
    assert not_due["scheduled_tasks"] == []


def test_scheduler_sorts_tasks_by_preferred_time() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    late = Task("Evening walk", time="18:00")
    early = Task("Breakfast", time="08:00")
    untimed = Task("Grooming")
    for task in (late, untimed, early):
        pet.add_task(task)
    owner.add_pet(pet)

    result = Scheduler(owner).sort_by_time()

    assert [task.description for _, task in result] == [
        "Breakfast",
        "Evening walk",
        "Grooming",
    ]


def test_scheduler_filters_by_pet_and_completion_status() -> None:
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    dog.add_task(Task("Walk"))
    completed = Task("Feed")
    completed.mark_complete()
    cat.add_task(completed)
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).filter_tasks(pet_name="mochi", is_complete=False)

    assert [(pet.name, task.description) for pet, task in result] == [
        ("Mochi", "Walk")
    ]


def test_completing_daily_task_creates_next_occurrence() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    task = Task("Walk", time="08:00", frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)

    next_task = Scheduler(owner).complete_task(pet, task, date(2026, 10, 24))

    assert task.is_complete
    assert next_task is not None
    assert next_task is not task
    assert next_task.due_date == date(2026, 10, 25)
    assert len(pet.tasks) == 2


def test_completing_weekly_task_creates_next_week_occurrence() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    task = Task("Grooming", frequency="weekly", due_date=date(2026, 10, 24))
    pet.add_task(task)
    owner.add_pet(pet)

    next_task = Scheduler(owner).complete_task(pet, task, date(2026, 10, 24))

    assert next_task is not None
    assert next_task.due_date == date(2026, 10, 31)


def test_completing_one_off_task_does_not_create_another() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    task = Task("Vet visit", frequency="once", due_date=date(2026, 10, 24))
    pet.add_task(task)
    owner.add_pet(pet)

    next_task = Scheduler(owner).complete_task(pet, task, date(2026, 10, 24))

    assert next_task is None
    assert task.is_complete
    assert len(pet.tasks) == 1


def test_scheduler_detects_overlapping_preferred_times_across_pets() -> None:
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    dog.add_task(Task("Walk", time="08:00", duration_minutes=30))
    cat.add_task(Task("Medication", time="08:15", duration_minutes=5))
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).detect_conflicts(schedule_date=date.today())

    assert len(result) == 1
    assert "overlapping preferred times" in result[0]["message"]


def test_one_off_task_without_date_defaults_to_today() -> None:
    task = Task("One-time visit", frequency="once")

    assert task.due_date == date.today()


def test_scheduler_avoids_overlap_and_explains_selection() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", time="08:00", duration_minutes=30, priority="high"))
    pet.add_task(Task("Breakfast", time="08:10", duration_minutes=10))
    owner.add_pet(pet)

    result = Scheduler(owner).generate_schedule(day_start=time(8, 0))
    tasks = result["scheduled_tasks"]

    assert tasks[0]["start_time"] == time(8, 0)
    assert tasks[1]["start_time"] == time(8, 30)
    assert all(item["reason"] for item in tasks)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"description": " "}, "description cannot be empty"),
        ({"description": "Walk", "duration_minutes": 0}, "positive number"),
        ({"description": "Walk", "priority": "urgent"}, "Priority must"),
        ({"description": "Walk", "frequency": "monthly"}, "Frequency must"),
    ],
)
def test_task_rejects_invalid_values(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Task(**kwargs)


def test_scheduler_rejects_non_positive_availability() -> None:
    with pytest.raises(ValueError, match="positive number"):
        Scheduler(Owner("Jordan")).generate_schedule(available_minutes=0)
