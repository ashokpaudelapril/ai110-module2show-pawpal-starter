# PawPal+ Project Reflection

## 1. System Design

**Core user actions (identified from the scenario):**

1. **Add a pet** – the owner enters a pet's name, species, and age so the system knows who it is scheduling for.
2. **Add / edit care tasks** – the owner defines tasks (walk, feeding, meds, grooming, enrichment) with a duration and priority so the scheduler has something to work with.
3. **Generate a daily plan** – the owner clicks "Generate schedule" and receives an ordered list of tasks that fit within their available time, with a plain-language explanation of the choices.

**a. Initial design**

The initial UML includes four classes:

| Class | Responsibility |
|---|---|
| `Task` | Holds a single care item: title, duration, priority, category, and completion status. It is a pure data object with no dependencies. |
| `Pet` | Owns a list of `Task` objects and provides methods to add/remove tasks. Carries identity info (name, species, age). |
| `Owner` | Aggregates one or more `Pet` objects and stores the owner's daily time budget and preferences. |
| `Scheduler` | References one `Owner` and one `Pet`; its `build_plan()` method selects tasks that fit the time budget ordered by priority, and `explain_plan()` narrates the result. |

Relationships:
- `Owner` has 1-to-many `Pet`
- `Pet` has 0-to-many `Task`
- `Scheduler` references both `Owner` (for the time budget) and `Pet` (for the task list)

Python dataclasses are used for `Task`, `Pet`, `Owner`, and `Scheduler` to keep the code concise and readable.

**b. Design changes**

No changes yet — this section will be updated during implementation if the design evolves.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
