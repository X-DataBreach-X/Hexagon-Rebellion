# Hexagon Rebellion

Destroy all the triangles

## Instructions for Build and Use

Steps to build and/or run the software:

1. First step here
2.
3.

Instructions for using the software:

1. First step here
2.
3.

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* First thing here
*
*

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [Website Title](Link)
*
*

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] First thing here
* [ ]
* [ ]

## Setup on a New Machine

1. Install Python 3.13 from python.org (or `winget install Python.Python.3.13`). Don't use 3.14 — Arcade's physics library (pymunk) doesn't install on it yet.
2. Clone the repo and go into the folder:
   ```
   git clone <your-repo-url>
   cd Hexagon-Rebellion
   ```
3. Create the virtual environment with Python 3.13:
   ```
   py -3.13 -m venv .venv
   ```
4. Activate it (the prompt should start with `(.venv)`):
   ```
   .venv\Scripts\Activate.ps1          # PowerShell
   .venv\Scripts\activate.bat          # Command Prompt
   source .venv/Scripts/activate       # Git Bash
   ```
   If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.
5. Install the project's packages:
   ```
   pip install -r requirements.txt
   ```
6. Run the game:
   ```
   python main.py
   ```

After the first setup, you only need to activate (step 4) and run the game (step 6).
