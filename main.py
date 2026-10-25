"""Run a small multi-pet PawPal+ schedule in the terminal."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(
        Task("Morning walk", time="08:00", duration_minutes=30, priority="high")
    )
    mochi.add_task(Task("Breakfast", time="08:45", duration_minutes=10, priority="high"))
    luna.add_task(Task("Medication", time="08:00", duration_minutes=5, priority="high"))
    luna.add_task(Task("Dinner", time="18:00", duration_minutes=10, priority="low"))

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule(
        schedule_date=date.today(), day_start=time(8, 0), available_minutes=120
    )
    print(f"Today's Schedule for {owner.name} ({schedule['date']:%A, %B %d}):")
    print("Scheduled by priority and preferred time:")
    for item in schedule["scheduled_tasks"]:
        print(
            f"  {item['start_time']:%H:%M} - {item['end_time']:%H:%M} | "
            f"{item['pet_name']}: {item['description']} "
            f"({item['duration_minutes']} min, {item['priority']} priority)"
        )
    print("\nTasks sorted by preferred time:")
    for pet, task in scheduler.sort_by_time():
        preferred = task.time.strftime("%H:%M") if task.time else "not set"
        print(f"  {preferred} | {pet.name}: {task.description}")
    print("\nIncomplete tasks for Mochi:")
    for pet, task in scheduler.filter_tasks(pet_name="Mochi", is_complete=False):
        print(f"  {pet.name}: {task.description}")
    if schedule["conflicts"]:
        print("\nSchedule warnings:")
        for conflict in schedule["conflicts"]:
            print(f"  Warning: {conflict['message']}")
    if schedule["unscheduled_tasks"]:
        print("Tasks that did not fit:")
        for item in schedule["unscheduled_tasks"]:
            print(f"  {item['pet_name']}: {item['description']} - {item['reason']}")


if __name__ == "__main__":
    main()
