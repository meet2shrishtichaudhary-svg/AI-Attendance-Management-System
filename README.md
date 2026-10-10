# AI Attendance Management System (Hugging Face)

Terminal-based Python project. Hugging Face interprets natural-language requests; Python validates dates, calculates percentages, and updates `attendance.json`.

## Setup (Windows)

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal > New Terminal.
4. Create an environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
5. Install packages:
   ```bash
   python -m pip install -r requirements.txt
   ```
6. Create a Hugging Face token:
   - Open https://huggingface.co/settings/tokens
   - Create a token with permission to make calls to Inference Providers.
   - Keep it private.
7. Copy `.env.example` to a new file named `.env`. Replace the sample value with your actual token. Never share or upload `.env`.
8. Run:
   ```bash
   python main.py
   ```

## Example terminal requests

- `show all attendance`
- `show report for roll 101`
- `was roll 102 present on 9 Oct 2026?`
- `mark roll 101 absent on 9 Oct 2026`
- `mark roll 103 present on 12 Oct 2026`
- `remove attendance for roll 101 on 9 Oct 2026`
- `class average`
- `exit`

## Data and safeguards

- Sample JSON has five example students and records for 8–14 October 2026. Replace sample names/records with authorized real data before use.
- Attendance changes are written to `attendance.json`.
- Only dates in the configured range are accepted.
- Python calculates percentages from recorded Present/Absent days. Removed/unrecorded days are not included in that student's denominator.
- This is a learning project; review AI-interpreted actions before using it for official records.
- Hugging Face inference availability, model routing, and billing/free limits depend on your account and the selected model/provider.
