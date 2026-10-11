# GitHub Team Rules

## 1. Create a Branch for Each Task

Do not work directly on `main`.

Create a branch for your task:

```bash
git checkout -b <task-name>
```

Example:

```bash
git checkout -b use-case-diagram
```

## 2. Commit Your Work

After finishing your task:

```bash
git add .
git commit -m "Add <task-name>"
```

## 3. Push Your Branch

```bash
git push origin <branch-name>
```

## 4. Create a Pull Request

- Create a Pull Request from your branch to `main`.
- Make sure your work is complete before submitting.

## 5. Task Documentation Structure

Each task must follow the structure below. Place the task number, task name, responsible person, and phase at the beginning of each task.

# Task [Task Number] – [Task Name]

**Responsible:** [Name]
**Phase:** [Phase Name]

## Project Structure

```text
EGYPT-MEDIA-VAULT/
│
├── README.md
│
└── docs/
    │
    ├── project planning/
    │
    ├── requirements gathering/
    │
    └── system analysis & design/
```

## 6. Task File Organization

Upload your task deliverables to the appropriate folder based on the phase the task belongs to.

- **project planning/** – For project planning documents, timelines, and task assignment plans.
- **requirements gathering/** – For requirements gathering documents and deliverables.
- **system analysis & design/** – For system analysis documents, diagrams, and design deliverables.

**Important:**

- Always upload your task files to the appropriate folder according to the task's phase.
- Do not upload task deliverables directly to the root directory.
- Use clear and meaningful file names.
- If you are unsure which folder your task belongs to, confirm the phase before uploading.
