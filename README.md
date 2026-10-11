GitHub Team Rules

1. Create a Branch for Each Task

Do not work directly on main.

Create a branch for your task:

git checkout -b <task-name>

Example:

git checkout -b use-case-diagram

2. Commit Your Work

After finishing your task:

git add .
git commit -m "Add <task-name>"

3. Push Your Branch

git push origin <branch-name>

4. Create a Pull Request

Create a Pull Request from your branch to main.

Make sure your work is complete before submitting.

5. Task Documentation Structure

Each task must follow the structure below. Place the task number, task name, responsible person, and phase at the beginning of each task.

Task [Task Number] – [Task Name]

Responsible: [Name]
Phase: [Phase Name]

Project Structure

EgySpy/
│
├── docs/
│   ├── proposal/
│   ├── requirements/
│   ├── diagrams/
│   └── README.md
