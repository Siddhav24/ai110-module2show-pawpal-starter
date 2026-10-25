# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The UML contains four classes. `Task` stores a care activity, preferred time,
recurrence, duration, priority, due date, and completion status. `Pet` owns a list of
tasks, `Owner` manages multiple pets and returns all pet/task pairs, and `Scheduler`
builds one plan from the owner's combined task list.

**b. Design changes**

I kept the four core classes and made each scheduled result include its pet, actual
start/end time, and an explanation. This was necessary to show multi-pet schedules
clearly and report tasks that could not fit. The UML was updated to match the final
implementation.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler filters completed and not-yet-due one-off tasks, ranks high priority
before medium and low, respects the available time and each task's preferred earliest
start, and schedules tasks without overlap. Priority comes first so that a short window
still includes the most important care.

**b. Tradeoffs**

The scheduler can delay a task past its preferred time when an earlier task runs long.
Treating the preference as an earliest start avoids overlapping care while still
preserving the requested order. If time is scarce, lower-priority tasks can be left out
and reported rather than silently exceeding the limit.

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI coding assistant to translate the project requirements into a class
diagram, implement the Python backend and Streamlit connection, and create tests and
documentation. Asking for a complete CLI-first implementation that still used the
same multi-pet scheduler in the UI helped keep the project consistent. Direct file
editing, repository inspection, and running pytest in the activated virtual
environment were the most useful assistant capabilities.

**b. Judgment and verification**

I did not use a scheduler that only took one pet or returned raw task objects: that
would not explain which pet needed care or why a task was chosen. I used
`Owner.get_all_tasks()` to provide pet/task pairs and tested schedules with two pets,
limited time, and overlapping preferred times. I kept this work in one assistant
session rather than opening separate chats; separating the work into requirement,
implementation, and verification steps kept the changes organized.

---

## 4. Testing and Verification

**a. What you tested**

Tests cover marking a task complete, adding a pet task, chronological sorting,
filtering, daily and weekly recurrence, one-off completion, scheduling across
multiple pets, priority when time is limited, completed and not-yet-due filtering,
conflict reporting, non-overlap, and invalid input. These checks exercise the core
behavior and important constraints rather than only checking that the app starts.

**b. Confidence**

I have good confidence in the covered cases because the tests and CLI demo run in the
project virtual environment. Next I would test the Streamlit app interactively and
add more cases for weekly recurrence, tasks near midnight, and daylight-saving
transitions.

---

## 5. Reflection

**a. What went well**

The same scheduler supports both the terminal demo and the multi-pet UI, and the plan
explains why tasks are included or left out.

**b. What you would improve**

I would persist owner and pet data between app sessions and add richer recurrence
options such as selecting specific weekdays.

**c. Key takeaway**

I learned that a scheduler needs pet-task relationships as well as a list of times:
carrying that relationship through the owner's combined task method makes both
multi-pet planning and readable explanations possible. AI-generated logic still needs
to be checked against explicit requirements and tested at its boundaries.
