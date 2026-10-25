# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

```
Today's Schedule for Jordan (Saturday, October 24):
Scheduled by priority and preferred time:
  08:00 - 08:30 | Mochi: Morning walk (30 min, high priority)
  08:30 - 08:35 | Luna: Medication (5 min, high priority)
  08:45 - 08:55 | Mochi: Breakfast (10 min, high priority)

Tasks sorted by preferred time:
  08:00 | Mochi: Morning walk
  08:00 | Luna: Medication
  08:45 | Mochi: Breakfast
  18:00 | Luna: Dinner

Incomplete tasks for Mochi:
  Mochi: Morning walk
  Mochi: Breakfast

Schedule warnings:
  Warning: Mochi's Morning walk and Luna's Medication have overlapping preferred times.
Tasks that did not fit:
  Luna: Dinner - Not enough time remains in the available schedule.
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The tests cover task completion and addition, chronological sorting, pet/status
filtering, daily and weekly recurrence, one-off completion, multi-pet scheduling,
priority under time constraints, conflict detection, completion/due-date filtering,
non-overlapping schedules, and invalid input.

```
19 passed
```

Reliability confidence: ⭐⭐⭐⭐☆ (4/5), based on the automated tests and CLI/UI smoke checks.

## 📐 Smarter Scheduling

| Feature | Behavior |
|---------|----------|
| Sorting | `Scheduler.sort_by_time()` sorts tasks chronologically by preferred time, with untimed tasks last. |
| Filtering | `Scheduler.filter_tasks()` filters by pet name and/or completion status; the UI exposes both filters. |
| Priority | High-priority tasks are considered first, then medium and low. |
| Time constraints | Tasks are skipped with an explanation when their duration or requested start time does not fit. |
| Conflict handling | `Scheduler.detect_conflicts()` warns about overlapping preferred-time windows; generated tasks are still scheduled without overlap. |
| Recurrence | `Scheduler.complete_task()` creates the next daily or weekly occurrence; one-off tasks do not repeat. |
| Completion | Completed tasks are excluded from the generated plan. |

The scheduler uses `Owner.get_all_tasks()` to consider tasks belonging to every pet.
For tasks that cannot fit, it reports the pet, task, and reason. A task's preferred time
can be delayed when an earlier task runs long.

## 🚶 Demo walkthrough

1. Enter the owner's name and add one or more pets in the Streamlit app.
2. Add care tasks with a duration, priority, recurrence, and preferred start time.
3. Filter the task list by pet and completion state; sort it by preferred time.
4. Mark a recurring task complete to create its next dated occurrence, or edit/remove a task.
5. Generate today's schedule to see priority ordering, conflict warnings, explanations, and tasks that did not fit.
6. Run `python main.py` for a CLI example showing sorting, filtering, warnings, and time limits.

## 🧱 Implementation summary

`Task` validates and tracks an individual care activity. `Pet` manages its task list,
and `Owner` manages multiple pets and provides their combined pet/task pairs through
`get_all_tasks()`. `Scheduler` reads that combined list, filters completed or not-due
tasks, prioritizes the rest, avoids overlaps, observes the available time, and explains
scheduled and unscheduled tasks. The Streamlit app and terminal demo both use these
same backend classes.

Run the terminal demonstration with `python main.py`, or start the interactive app with
`streamlit run app.py`.

The final class diagram is in [`diagrams/uml_final.mmd`](./diagrams/uml_final.mmd).
