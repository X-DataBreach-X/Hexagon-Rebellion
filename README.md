# Hexagon Rebellion

Destroy all the triangles

## Instructions for Build and Use

Steps to build and/or run the software:

1. Clone the repo and go into the folder:
   ```
   git clone https://github.com/X-DataBreach-X/Hexagon-Rebellion.git
   cd Hexagon-Rebellion
   ```
2. Create the virtual environment with Python 3.13:
   ```
   py -3.13 -m venv .venv
   ```
3. Activate it (the prompt should start with `(.venv)`):
   ```
   .venv\Scripts\Activate.ps1          # PowerShell
   .venv\Scripts\activate.bat          # Command Prompt
   source .venv/Scripts/activate       # Git Bash
   ```
   If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.
4. Install the project's packages:
   ```
   pip install -r requirements.txt
   ```

Instructions for using the software:

1. Activate the virtual environment (build step 3) if it isn't already active.
2. Run the game:
   ```
   python main.py
   ```
3. After the first setup, these two steps are all you need each time you play.

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* Python 3.13 — install from python.org (or `winget install Python.Python.3.13`). Don't use 3.14 — Arcade's physics library (pymunk) doesn't install on it yet.
* Arcade 3.3.3
* NumPy 2.5.3
* Git (to clone the repository)

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [Claude by Anthropic](https://claude.com/)

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] I would like to add more weapons to the game as well as armor and have it be more structured.
* [ ] I'd also like to add different types of enemies with different abilities.
* [ ] I need to add levels to the game that the user can complete. 
