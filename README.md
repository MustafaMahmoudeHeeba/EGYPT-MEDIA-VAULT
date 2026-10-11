# GitHub Team Rules

## 1. Create a Branch for Each Task

Do not work directly on `main`.

Create a branch for your task:

```bash
git checkout -b <task-name>
```

Examples:

```bash
git checkout -b project-proposal
```

## 2. Commit Your Work

After finishing your task, commit your changes:

```bash
git add .
git commit -m "Add <task-name>"
```

Examples:

```bash
git commit -m "Add project proposal"
```

## 3. Push Your Branch

Push your branch to GitHub:

```bash
git push -u origin <branch-name>
```

## 4. Create a Pull Request

Create a Pull Request from your branch to `main`.

Ask another team member to review your work before merging.

## 5. Keep Files Organized

Put each task in its appropriate folder under `docs/`.

```text
docs/
├── project planning/
├── requirements gathering/
└── system analysis & design/
```

Keep the existing folder names consistent, and do not place project documents randomly in the repository.

## 6. Task Workflow

```text
Choose a Task
      ↓
Create a Branch
      ↓
Do the Work
      ↓
Commit Changes
      ↓
Push the Branch
      ↓
Create a Pull Request
      ↓
Review & Merge
```

**Important:** Do not push directly to `main`. All changes should be submitted through a Pull Request.
