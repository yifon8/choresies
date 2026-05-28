ReadMe created from conclusions of chat session by Claude Chat



\# Chore Wheel 🎡



!\[Platform: Windows + Mac](https://img.shields.io/badge/platform-Windows%20%7C%20Mac-blue)

!\[Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

!\[GUI: tkinter](https://img.shields.io/badge/GUI-tkinter-lightgrey)

!\[License: MIT](https://img.shields.io/badge/license-MIT-green)



A desktop chore wheel app built with Python and tkinter. Spin the wheel to pick a chore, drag a wedge out to mark it done, and let recurring chores return automatically on their schedule.



> \*\*No internet required. Runs entirely on your machine.\*\*



\---



\## Demo



\*(Screen recording GIF — wheel spinning and wedge pull in action)\*



\---



\## Features



\- \*\*Spinning color wheel\*\* — each wedge is an undone chore; spin to pick one at random

\- \*\*Wedge pull\*\* — drag a wedge outward to mark it done (or click Done in the list)

\- \*\*Recurring chores\*\* — set a daily/weekly/monthly interval; chore returns to the wheel automatically

\- \*\*Redo button\*\* — skip the wait and return any done chore to the wheel immediately

\- \*\*Recur button\*\* — add or edit recurrence on any done chore after the fact

\- \*\*Completion counter\*\* — tracks how many times each chore has been completed

\- \*\*Persistent state\*\* — all data saved to a local JSON file; picks up exactly where you left off



\---



\## Architecture



\### Why one `mark\_done()` function?



Both the wedge-pull gesture and the Done button in the list call the same `mark\_done(chore\_id)` function in `app.py`. The UI panels hold no state and mutate nothing directly — they receive callbacks from `App` and call them. This means there is exactly one place where "what happens when a chore is completed" is defined, making it trivial to add a third entry point (e.g. a keyboard shortcut) without risking divergent behavior.



\### Why JSON instead of a database?



The data set is small (tens of chores at most), the schema is flat, and the app is single-user. JSON satisfies all requirements with zero dependencies, human-readable files the user can inspect or edit, and trivial backup (just copy the file). A database would add complexity and an installer dependency for no practical gain.



\---



\## File structure



```

choresies/

├── main.py              # Entry point

├── app.py               # App class, layout, mark\_done / redo\_chore callbacks

├── wheel/

│   ├── canvas.py        # WheelCanvas — drawing, spin animation, wedge pull

│   └── colors.py        # Adjacency-safe color palette assignment

├── chores/

│   ├── model.py         # Chore dataclass + state logic

│   └── store.py         # JSON load/save + recurring auto-return

├── ui/

│   ├── add\_form.py      # Add chore row with optional recurrence

│   ├── undone\_list.py   # Scrollable undone chores list

│   └── done\_list.py     # Scrollable done list with Recur / Redo buttons

├── data/

│   └── chores.json      # Runtime data (auto-created on first run)

├── build/

│   ├── build\_windows.spec

│   └── build\_mac.spec

└── tests/

&#x20;   ├── test\_colors.py

&#x20;   ├── test\_model.py

&#x20;   └── test\_store.py

```



\---



\## Installation



\### Run from source



```bash

\# Clone

git clone https://github.com/yifon8/choresies.git

cd choresies



\# Create a virtual environment (recommended)

python -m venv .venv

source .venv/bin/activate   # Windows: .venv\\Scripts\\activate



\# Install dependencies

pip install -r requirements.txt



\# Run

python main.py

```



> \*\*tkinter\*\* ships with most Python distributions. If it's missing on Linux:

> ```bash

> sudo apt install python3-tk

> ```



\---



\## Build a standalone executable



\### Windows (.exe)



```bash

pip install pyinstaller

pyinstaller build/build\_windows.spec

\# Output: dist/ChoreWheel.exe

```



\### Mac (.app)



```bash

pip install pyinstaller

pyinstaller build/build\_mac.spec

\# Output: dist/ChoreWheel.app

```



\---



\## Running tests



```bash

pip install pytest

pytest tests/

```



\---



\## Future ideas



\- \*\*Chore history log\*\* — timestamped record of every completion

\- \*\*Streak tracking\*\* — consecutive on-time completions per chore

\- \*\*Household multi-user mode\*\* — assign chores to people, track who did what

\- \*\*Notifications\*\* — system tray alert when a recurring chore comes due

\- \*\*Themes\*\* — light/dark mode and custom color palettes



\---



\## License



MIT



