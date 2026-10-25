"""Core pet-care models and daily scheduling logic for PawPal+."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import uuid4


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"daily", "weekly", "once"}


def _parse_time(value: time | str | None) -> time | None:
    if value is None or isinstance(value, time):
        return value
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as error:
        raise ValueError("Task time must use 24-hour HH:MM format.") from error


@dataclass
class Task:
    """Represent a pet-care activity and its scheduling requirements."""

    description: str
    time: time | str | None = None
    frequency: str = "daily"
    duration_minutes: int = 15
    priority: str = "medium"
    is_complete: bool = False
    due_date: date | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        self.description = self.description.strip()
        if not self.description:
            raise ValueError("Task description cannot be empty.")
        self.time = _parse_time(self.time)
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"Frequency must be one of: {', '.join(sorted(FREQUENCIES))}.")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError("Priority must be low, medium, or high.")
        if (
            isinstance(self.duration_minutes, bool)
            or not isinstance(self.duration_minutes, int)
            or self.duration_minutes <= 0
        ):
            raise ValueError("Task duration must be a positive number of minutes.")
        if self.frequency != "daily" and self.due_date is None:
            self.due_date = date.today()

    def mark_complete(self) -> None:
        """Mark the task as complete."""
        self.is_complete = True

    def update(
        self,
        description: str,
        duration_minutes: int,
        priority: str,
        task_time: time | str | None,
        frequency: str,
        due_date: date | None = None,
    ) -> None:
        """Update the task after validating its replacement values."""
        updated = Task(
            description=description,
            duration_minutes=duration_minutes,
            priority=priority,
            time=task_time,
            frequency=frequency,
            due_date=due_date,
            is_complete=self.is_complete,
            id=self.id,
        )
        self.description = updated.description
        self.duration_minutes = updated.duration_minutes
        self.priority = updated.priority
        self.time = updated.time
        self.frequency = updated.frequency
        self.due_date = updated.due_date


@dataclass
class Pet:
    """Store a pet's details and care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.species = self.species.strip()
        if not self.name or not self.species:
            raise ValueError("Pet name and species cannot be empty.")

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        if any(existing.id == task.id for existing in self.tasks):
            raise ValueError("This task has already been added to the pet.")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its unique identifier."""
        for index, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[index]
                return
        raise ValueError(f"No task with id {task_id!r} belongs to {self.name}.")


@dataclass
class Owner:
    """Manage an owner's pets and provide their combined task list."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Owner name cannot be empty.")

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's care."""
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError("This pet has already been added to the owner.")
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Build a priority-aware daily schedule across all of an owner's pets."""

    owner: Owner

    def sort_by_time(
        self, tasks: list[tuple[Pet, Task]] | None = None
    ) -> list[tuple[Pet, Task]]:
        """Return pet/task pairs in preferred-time order, keeping untimed tasks last."""
        entries = list(self.owner.get_all_tasks() if tasks is None else tasks)
        return sorted(
            entries,
            key=lambda entry: (
                entry[1].time is None,
                entry[1].time or time.max,
            ),
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        is_complete: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter the owner's tasks by pet name and/or completion status."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (pet_name is None or pet.name.casefold() == pet_name.strip().casefold())
            and (is_complete is None or task.is_complete is is_complete)
        ]

    def complete_task(
        self,
        pet: Pet,
        task: Task,
        completed_on: date | None = None,
    ) -> Task | None:
        """Complete a pet's task and add its next daily or weekly occurrence."""
        if pet not in self.owner.pets or not any(
            existing.id == task.id for existing in pet.tasks
        ):
            raise ValueError("The task must belong to one of this owner's pets.")
        if task.is_complete:
            raise ValueError("This task is already complete.")

        task.mark_complete()
        if task.frequency == "once":
            return None

        completed_on = completed_on or date.today()
        if task.frequency == "weekly":
            next_due_date = completed_on + timedelta(days=7)
        else:
            next_due_date = completed_on + timedelta(days=1)
        next_task = Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            due_date=next_due_date,
        )
        pet.add_task(next_task)
        return next_task

    def detect_conflicts(
        self,
        schedule_date: date | None = None,
        day_start: time = time(7, 0),
    ) -> list[dict[str, str]]:
        """Report overlapping preferred-time windows for due, incomplete tasks."""
        schedule_date = schedule_date or date.today()
        day_start = _parse_time(day_start)
        if day_start is None:
            raise ValueError("The schedule must have a start time.")
        entries = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if self._is_due(task, schedule_date) and not task.is_complete
        ]
        conflicts: list[dict[str, str]] = []
        for index, (first_pet, first_task) in enumerate(entries):
            first_start = first_task.time or day_start
            first_start_minutes = first_start.hour * 60 + first_start.minute
            first_end_minutes = first_start_minutes + first_task.duration_minutes
            for second_pet, second_task in entries[index + 1 :]:
                second_start = second_task.time or day_start
                second_start_minutes = second_start.hour * 60 + second_start.minute
                second_end_minutes = second_start_minutes + second_task.duration_minutes
                if (
                    first_start_minutes < second_end_minutes
                    and second_start_minutes < first_end_minutes
                ):
                    conflicts.append(
                        {
                            "first_pet": first_pet.name,
                            "first_task": first_task.description,
                            "second_pet": second_pet.name,
                            "second_task": second_task.description,
                            "message": (
                                f"{first_pet.name}'s {first_task.description} and "
                                f"{second_pet.name}'s {second_task.description} have "
                                "overlapping preferred times."
                            ),
                        }
                    )
        return conflicts

    def generate_schedule(
        self,
        schedule_date: date | None = None,
        day_start: time = time(7, 0),
        available_minutes: int = 480,
    ) -> dict[str, Any]:
        """Schedule due tasks within the owner's time and duration limits."""
        if isinstance(available_minutes, bool) or available_minutes <= 0:
            raise ValueError("Available time must be a positive number of minutes.")
        schedule_date = schedule_date or date.today()
        day_start = _parse_time(day_start)
        if day_start is None:
            raise ValueError("The schedule must have a start time.")

        day_start_minutes = day_start.hour * 60 + day_start.minute
        window_minutes = min(available_minutes, 1440 - day_start_minutes)
        day_end_minutes = day_start_minutes + window_minutes
        entries = [
            (pet, task, position)
            for position, (pet, task) in enumerate(self.owner.get_all_tasks())
            if self._is_due(task, schedule_date) and not task.is_complete
        ]
        entries.sort(
            key=lambda entry: (
                PRIORITY_ORDER[entry[1].priority],
                entry[1].time or day_start,
                entry[2],
            )
        )

        scheduled: list[dict[str, Any]] = []
        unscheduled: list[dict[str, str]] = []
        cursor = day_start_minutes
        remaining_minutes = window_minutes

        for pet, task, _ in entries:
            preferred_minutes = (
                task.time.hour * 60 + task.time.minute
                if isinstance(task.time, time)
                else day_start_minutes
            )
            start_minutes = max(cursor, preferred_minutes)
            end_minutes = start_minutes + task.duration_minutes
            if task.duration_minutes > remaining_minutes or end_minutes > day_end_minutes:
                unscheduled.append(
                    {
                        "pet_name": pet.name,
                        "description": task.description,
                        "reason": "Not enough time remains in the available schedule.",
                    }
                )
                continue

            end_time = time(end_minutes // 60, end_minutes % 60)
            start_time = time(start_minutes // 60, start_minutes % 60)
            scheduled.append(
                {
                    "pet_name": pet.name,
                    "description": task.description,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "reason": (
                        f"{task.priority.title()} priority; fits the available "
                        "time without overlapping another task."
                    ),
                }
            )
            cursor = end_minutes
            remaining_minutes -= task.duration_minutes

        return {
            "date": schedule_date,
            "start_time": day_start,
            "available_minutes": window_minutes,
            "total_minutes": window_minutes - remaining_minutes,
            "scheduled_tasks": scheduled,
            "unscheduled_tasks": unscheduled,
            "conflicts": self.detect_conflicts(schedule_date, day_start),
        }

    @staticmethod
    def _is_due(task: Task, schedule_date: date) -> bool:
        if task.frequency == "once":
            return task.due_date == schedule_date
        if task.frequency == "weekly" and task.due_date is not None:
            return (
                schedule_date >= task.due_date
                and (schedule_date - task.due_date).days % 7 == 0
            )
        return task.due_date is None or task.due_date <= schedule_date
