from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def build_scheduler() -> Scheduler:
    owner = Owner(name="Taylor")
    dog = Pet(name="Milo", species="Dog", age=5)
    cat = Pet(name="Nori", species="Cat", age=3)
    owner.add_pet(dog)
    owner.add_pet(cat)

    today = date.today()
    dog.add_task(
        Task(
            description="Walk",
            due_date=today,
            due_time=time(9, 0),
            frequency="daily",
            priority="medium",
            duration_minutes=30,
        )
    )
    cat.add_task(
        Task(
            description="Feed",
            due_date=today,
            due_time=time(8, 0),
            priority="high",
            duration_minutes=10,
        )
    )
    return Scheduler(owner)


def test_mark_complete_updates_status() -> None:
    scheduler = build_scheduler()

    completed_task = scheduler.mark_task_complete("Milo", "Walk")

    assert completed_task is not None
    assert completed_task.completed is True


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet(name="Clover", species="Dog", age=1)
    initial_count = pet.task_count()

    pet.add_task(
        Task(
            description="Bath",
            due_date=date.today(),
            due_time=time(14, 0),
        )
    )

    assert pet.task_count() == initial_count + 1


def test_sorting_returns_tasks_in_chronological_order() -> None:
    scheduler = build_scheduler()

    ordered = scheduler.sort_tasks_by_time()

    assert [task.description for _, task in ordered] == ["Feed", "Walk"]


def test_daily_recurrence_creates_next_day_task() -> None:
    scheduler = build_scheduler()
    scheduler.mark_task_complete("Milo", "Walk")
    milo_tasks = scheduler.filter_tasks(pet_name="Milo")

    assert len(milo_tasks) == 2
    new_task = [task for _, task in milo_tasks if not task.completed][0]
    assert new_task.due_date == date.today() + timedelta(days=1)
    assert new_task.description == "Walk"


def test_conflict_detection_flags_duplicate_times() -> None:
    owner = Owner(name="Jamie")
    dog = Pet(name="Pepper", species="Dog", age=6)
    cat = Pet(name="Olive", species="Cat", age=4)
    owner.add_pet(dog)
    owner.add_pet(cat)

    same_day = date.today()
    same_time = time(10, 30)
    dog.add_task(Task("Walk", same_day, same_time))
    cat.add_task(Task("Medication", same_day, same_time))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "Conflict:" in conflicts[0]


def test_next_available_slot_skips_existing_task_blocks() -> None:
    scheduler = build_scheduler()

    slot = scheduler.next_available_slot(date.today(), duration_minutes=20, start_hour=8, end_hour=12)

    assert slot.strftime("%H:%M") == "08:10"
