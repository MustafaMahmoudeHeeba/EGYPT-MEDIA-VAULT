# GitHub Team Rules

## 1. Create a Branch for Each Collaborator

Do not work directly on `main`.

Each collaborator must create their own branch and use it for all their assigned tasks.

Create your branch using your name or GitHub username:

```bash
git checkout -b <username>
```

Example:

```bash
git checkout -b mustafa-mahmoud
```

**Rules:**

- Each collaborator must work on their own branch.
- Use the same branch for all your assigned tasks.
- Do not create a new branch for every task.
- Do not work directly on `main`.

## 2. Commit Your Work

After finishing a task or completing a meaningful part of your work:

```bash
git add .
git commit -m "Add <task-name>"
```

Example:

```bash
git commit -m "Add use case diagram"
```

## 3. Push Your Branch

Push your changes to your own branch on GitHub:

```bash
git push origin <username>
```

Example:

```bash
git push origin mustafa-mahmoud
```

## 4. Create a Pull Request

- Create a Pull Request from your branch to `main`.
- Make sure your work is complete before submitting.
- Include a clear description of your changes.

## 5. Task Documentation Structure

Each task must follow the structure below. Place the task number, task name, responsible person, and phase at the beginning of each task.

```markdown
# Task [Task Number] – [Task Name]

**Responsible:** [Name]  
**Phase:** [Phase Name]
```

## 6. Project Structure

```text
EGYPT-MEDIA-VAULT/
│
│
└── docs/
    │
    ├── project planning/
    │
    ├── requirements gathering/
    │
    └── system analysis & design/
```

## 7. Task File Organization

Upload your task deliverables to the appropriate folder based on the phase the task belongs to.

- **project planning/** – Project plans, timelines, and task assignment documents.
- **requirements gathering/** – Requirements gathering documents and deliverables.
- **system analysis & design/** – System analysis documents, diagrams, and design deliverables.

**Important:**

- Always upload your task files to the appropriate folder according to its phase.
- Do not upload task deliverables directly to the root directory.
- Use clear and meaningful file names.
- If you are unsure which folder your task belongs to, confirm the phase before uploading.
