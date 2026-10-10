import json
import re
from datetime import date
from pathlib import Path

from transformers import pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "attendance.json"
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print("Loading Hugging Face model...")
ai = pipeline("text-generation", model=MODEL_NAME, device=-1)
print("Model loaded successfully.")


def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_student(data, roll_no):
    return next(
        (s for s in data["students"]
         if str(s["roll_no"]) == str(roll_no)),
        None
    )


def valid_date(data, day):
    try:
        selected = date.fromisoformat(day)
        start = date.fromisoformat(data["date_range"]["start"])
        end = date.fromisoformat(data["date_range"]["end"])
        return start <= selected <= end
    except (ValueError, TypeError):
        return False


def attendance_stats(student, data):
    records = [
        status
        for day, status in student["attendance"].items()
        if valid_date(data, day) and status in ("Present", "Absent")
    ]

    present = records.count("Present")
    total = len(records)
    percentage = present * 100 / total if total else 0.0

    return present, total, percentage


def show_all(data):
    percentages = []

    print("\nROLL NO. | NAME | PRESENT/TOTAL | ATTENDANCE")
    print("-" * 55)

    for student in data["students"]:
        present, total, percentage = attendance_stats(student, data)
        percentages.append(percentage)

        print(
            f"{student['roll_no']} | {student['name']} | "
            f"{present}/{total} | {percentage:.2f}%"
        )

    average = sum(percentages) / len(percentages) if percentages else 0
    print("-" * 55)
    print(f"Class average: {average:.2f}%")


def show_report(student, data):
    present, total, percentage = attendance_stats(student, data)

    print(f"\nStudent: {student['name']}")
    print(f"Roll number: {student['roll_no']}")
    print(f"Present: {present}/{total} recorded days")
    print(f"Attendance: {percentage:.2f}%")

    for day, status in sorted(student["attendance"].items()):
        print(f"{day}: {status}")


def understand_request(text, data):
    roster = [
        {"roll_no": s["roll_no"], "name": s["name"]}
        for s in data["students"]
    ]

    instructions = f"""
Convert the user's attendance request into one JSON object.
Return JSON only, with no Markdown.

Students: {json.dumps(roster)}
Allowed dates: {data['date_range']['start']} to {data['date_range']['end']}

Actions:
list, report, check, mark, remove, average, help

JSON fields:
action, roll_no, date, status

Rules:
- Use only the listed students and their exact roll numbers.
- Use dates in YYYY-MM-DD format.
- status must be Present or Absent.
- report requires a roll number.
- check requires a roll number and date.
- mark requires a roll number, date and status.
- remove requires a roll number and date.
- If details are missing or unclear, use help.
- Never invent missing information.

Example:
{{"action":"check","roll_no":"101","date":"2026-10-08","status":null}}
"""

    prompt = ai.tokenizer.apply_chat_template(
        [
            {"role": "system", "content": instructions},
            {"role": "user", "content": text}
        ],
        tokenize=False,
        add_generation_prompt=True
    )

    output = ai(
        prompt,
        max_new_tokens=120,
        do_sample=False,
        return_full_text=False
    )[0]["generated_text"]

    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        return {"action": "help"}

    try:
        command = json.loads(match.group())
    except json.JSONDecodeError:
        return {"action": "help"}

    allowed = {"list", "report", "check", "mark", "remove", "average", "help"}
    if command.get("action") not in allowed:
        return {"action": "help"}

    return command


def handle_request(command, data):
    action = command.get("action")

    if action == "list":
        show_all(data)
        return

    if action == "average":
        values = [attendance_stats(s, data)[2] for s in data["students"]]
        average = sum(values) / len(values) if values else 0
        print(f"Class average attendance: {average:.2f}%")
        return

    if action == "help":
        print(
            'Try: "show all attendance", "class average", '
            '"report roll 101", "check roll 101 on 2026-10-08", '
            '"mark roll 101 present on 2026-10-09", '
            'or "remove roll 101 attendance on 2026-10-09".'
        )
        return

    roll_no = command.get("roll_no")
    student = get_student(data, roll_no)

    if student is None:
        print("Student not found. Check the roll number.")
        return

    if action == "report":
        show_report(student, data)
        return

    day = command.get("date")
    if not valid_date(data, day):
        print(
            f"Invalid date. Allowed range: "
            f"{data['date_range']['start']} to {data['date_range']['end']}."
        )
        return

    if action == "check":
        status = student["attendance"].get(day, "No record")
        print(f"{student['name']} on {day}: {status}")

    elif action == "mark":
        status = command.get("status")
        if status not in ("Present", "Absent"):
            print("Specify Present or Absent.")
            return

        student["attendance"][day] = status
        save_data(data)
        print(f"Saved: {student['name']} — {day}: {status}")

    elif action == "remove":
        if day not in student["attendance"]:
            print("No attendance record exists for that date.")
            return

        del student["attendance"][day]
        save_data(data)
        print(f"Attendance removed for {student['name']} on {day}.")


def main():
    try:
        data = load_data()
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot load attendance.json: {error}")
        return

    print(
        f"\nAI Attendance Management System\n"
        f"Date range: {data['date_range']['start']} "
        f"to {data['date_range']['end']}\n"
        "Type 'help' for commands or 'exit' to quit."
    )

    while True:
        text = input("\nAttendance > ").strip()

        if text.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not text:
            continue

        try:
            command = understand_request(text, data)
            handle_request(command, data)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as error:
            print(f"Request failed: {error}")


if __name__ == "__main__":
    main()