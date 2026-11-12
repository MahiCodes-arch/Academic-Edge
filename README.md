# ACADEMIC EDGE ✿

A local Streamlit app for attendance, syllabus progress, ML-assisted study planning, and daily study tracking. It uses one shared SQLite database on your computer; no account, cloud service, chatbot, or notifications are included.

The overview includes a selectable animated study buddy and shortcut cards for opening each module. The buddy choice lasts for the current app session. The visual style pairs lavender with rose, sage, and buttercream pastels, with handwritten display headings, clean sans-serif content text, and coordinated accent colors for each module.

A floating **Quick guide** button stays available across the app with a short setup path for all four modules.

You can remove subjects or individual chapters from **Syllabus → Manage your list**. Removing a subject also clears its attendance total and chapters; study diary entries remain and become “General study.”

Attendance is recorded through one consistent class check-in: choose a subject, mark present or absent, and save.

## Start the app

1. Install Python 3.10 or newer.
2. Open a terminal in this `SEM_SURVIVOR` folder.
3. (Recommended) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies and run:

   ```powershell
   python -m pip install -r requirements.txt
   streamlit run app.py
   ```

The app opens in your browser. Your data is saved in `database/sem_survivor.db`. Keep this file to preserve your records; deleting it resets the app data.

## Project map

```text
app.py                         Main screen, sidebar, and overview
modules/bunk_calculator.py     Manual attendance and absence calculations
modules/syllabus_tracker.py    Subjects, chapters, and progress chart
modules/study_planner.py      Exam aware daily study suggestions
modules/daily_tracker.py      Study logs and weekly/monthly analytics
database/db.py                 Shared SQLite operations
database/schema.sql            Tables and data constraints
ml/priority_model.py           Small scikit-learn urgency model
assets/style.css               Lavender and pastel styling
requirements.txt               Python packages
```

## How the planner's ML works

The planner uses pending chapter count, days until an exam, and attendance percentage as inputs to a Random Forest classifier. To keep this project self contained, the model trains on a reproducible set of example records labelled by a simple urgency rule. It helps order the subjects; it does not learn from private data or predict grades. The planner builds a seven-day timetable with 50-minute focus blocks and 10-minute resets, scheduling a learn session and a practice-and-recall session for each unfinished chapter. Subjects without an exam date are clearly shown as “Not set” and receive steady review priority.

## Study the project after delivery

Try learning it in this order:

1. Read `app.py` to understand how navigation selects one module and how the dashboard combines summaries.
2. Read `database/schema.sql` and `database/db.py` to see how all modules share SQLite tables.
3. Follow one action end to end: for example, `Present` in the attendance screen calls `attendance_update`, which updates SQLite, then the dashboard reads the new totals.
4. Explore each file in `modules/` and match its form inputs to the database calls.
5. Read `ml/priority_model.py`, then see how `study_planner.py` prepares features and displays priorities.
6. Compare a few study logs in the Daily Tracker and its Plotly graph.

The source includes comments and descriptive names so you can change it as you learn. The first run creates the database automatically. There are no sample records, so the overview starts empty until you add your own subjects and study data.
