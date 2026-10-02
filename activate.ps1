# Activates the project's virtual environment (.venv) in PowerShell.
#
# Run it from the project folder with:
#
#     .\activate.ps1
#
# Unlike bash, PowerShell scripts can change the current folder and
# environment of the terminal that runs them, so no "source" is needed.

# Go to the project folder (where this file lives), wherever it was run from.
Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"
Write-Host "Activated .venv - run the game with: python main.py"
