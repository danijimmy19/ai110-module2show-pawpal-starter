from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, rows: list[dict[str, str]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for row in rows:
        print(
            f"{row['Date']} {row['Time']} | {row['Pet']:<7} | {row['Task']:<18} | "
            f"{row['Priority']:<10} | {row['Status']}"
        )


def main() -> None:
    owner = Owner(name="Jordan", email="jordan@example.com")
    mochi = Pet(name="Mochi", species="Dog", age=4, notes="Loves long walks")
    luna = Pet(name="Luna", species="Cat", age=2, notes="Needs evening medication")

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()
    mochi.add_task(
        Task(
            description="Morning walk",
            due_date=today,
            due_time=time(7, 30),
            frequency="daily",
            priority="high",
            duration_minutes=30,
            task_type="exercise",
        )
    )
    mochi.add_task(
        Task(
            description="Breakfast",
            due_date=today,
            due_time=time(8, 0),
            priority="high",
            duration_minutes=15,
            task_type="feeding",
        )
    )
    luna.add_task(
        Task(
            description="Vet appointment",
            due_date=today,
            due_time=time(8, 0),
            priority="medium",
            duration_minutes=45,
            task_type="appointment",
        )
    )
    luna.add_task(
        Task(
            description="Medication",
            due_date=today,
            due_time=time(18, 30),
            frequency="daily",
            priority="high",
            duration_minutes=10,
            task_type="medical",
        )
    )

    scheduler = Scheduler(owner)

    print_schedule("Today's Schedule (sorted by time)", scheduler.agenda_table(sort_mode="time"))
    print_schedule(
        "Today's Schedule (priority first)", scheduler.agenda_table(sort_mode="priority")
    )

    high_priority = scheduler.filter_tasks(priority="high", completed=False)
    print("\nHigh-priority pending tasks")
    print("---------------------------")
    for pet, task in high_priority:
        print(f"- {pet.name}: {task.description} at {task.due_time.strftime('%H:%M')}")

    conflicts = scheduler.detect_conflicts()
    print("\nConflict check")
    print("--------------")
    if conflicts:
        for warning in conflicts:
            print(f"! {warning}")
    else:
        print("No conflicts found.")

    scheduler.mark_task_complete("Mochi", "Morning walk")
    print("\nAfter completing Mochi's daily walk")
    print("-----------------------------------")
    for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
        print(
            f"- {task.description}: {task.due_date.isoformat()} {task.due_time.strftime('%H:%M')} "
            f"({task.formatted_status()}, {task.frequency})"
        )

    slot = scheduler.next_available_slot(today, duration_minutes=20)
    print("\nNext available 20-minute slot")
    print("-----------------------------")
    print(slot.strftime("%H:%M") if slot else "No slot available")


if __name__ == "__main__":
    main()
