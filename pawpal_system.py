from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json


_PRIORITY_WEIGHTS = {"high": 0, "medium": 1, "low": 2}
_PRIORITY_EMOJIS = {"high": "🔴", "medium": "🟡", "low": "🟢"}


@dataclass
class Task:
    """Represents a single pet-care task with scheduling metadata."""

    description: str
    due_date: date
    due_time: time
    frequency: str = "once"
    priority: str = "medium"
    completed: bool = False
    duration_minutes: int = 30
    task_type: str = "general"

    def __post_init__(self) -> None:
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        self.task_type = self.task_type.lower()
        if self.priority not in _PRIORITY_WEIGHTS:
            raise ValueError("priority must be low, medium, or high")
        if self.frequency not in {"once", "daily", "weekly"}:
            raise ValueError("frequency must be once, daily, or weekly")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def due_datetime(self) -> datetime:
        """Return the combined due date and due time as a datetime."""
        return datetime.combine(self.due_date, self.due_time)

    def mark_complete(self) -> None:
        """Mark the task as complete."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Create the next instance for recurring tasks, if any."""
        if self.frequency == "once":
            return None

        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        return Task(
            description=self.description,
            due_date=self.due_date + delta,
            due_time=self.due_time,
            frequency=self.frequency,
            priority=self.priority,
            completed=False,
            duration_minutes=self.duration_minutes,
            task_type=self.task_type,
        )

    def priority_weight(self) -> int:
        """Return the numeric weight used for priority-based sorting."""
        return _PRIORITY_WEIGHTS[self.priority]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the task for JSON storage."""
        return {
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "due_time": self.due_time.strftime("%H:%M"),
            "frequency": self.frequency,
            "priority": self.priority,
            "completed": self.completed,
            "duration_minutes": self.duration_minutes,
            "task_type": self.task_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize a task from a dictionary."""
        return cls(
            description=data["description"],
            due_date=date.fromisoformat(data["due_date"]),
            due_time=datetime.strptime(data["due_time"], "%H:%M").time(),
            frequency=data.get("frequency", "once"),
            priority=data.get("priority", "medium"),
            completed=data.get("completed", False),
            duration_minutes=data.get("duration_minutes", 30),
            task_type=data.get("task_type", "general"),
        )

    def formatted_status(self) -> str:
        """Return a compact status string for CLI/UI display."""
        return "✅ Complete" if self.completed else "⏳ Pending"

    def formatted_priority(self) -> str:
        """Return the priority with an emoji for easy display."""
        return f"{_PRIORITY_EMOJIS[self.priority]} {self.priority.title()}"


@dataclass
class Pet:
    """Represents a pet and the care tasks assigned to it."""

    name: str
    species: str
    age: int
    notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's schedule."""
        self.tasks.append(task)

    def list_tasks(self, include_completed: bool = True) -> List[Task]:
        """Return this pet's tasks, optionally excluding completed tasks."""
        if include_completed:
            return list(self.tasks)
        return [task for task in self.tasks if not task.completed]

    def task_count(self) -> int:
        """Return the number of tasks assigned to this pet."""
        return len(self.tasks)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the pet for JSON storage."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "notes": self.notes,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pet":
        """Deserialize a pet from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data.get("age", 0),
            notes=data.get("notes", ""),
        )
        pet.tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return pet


@dataclass
class Owner:
    """Represents the pet owner and the pets they manage."""

    name: str
    email: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return a pet by name if it exists."""
        normalized = pet_name.strip().lower()
        for pet in self.pets:
            if pet.name.lower() == normalized:
                return pet
        return None

    def all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all tasks across the owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def save_to_json(self, filepath: str) -> None:
        """Save the owner, pets, and tasks to disk as JSON."""
        payload = {
            "name": self.name,
            "email": self.email,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> "Owner":
        """Load an owner, pets, and tasks from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as file:
            payload = json.load(file)
        owner = cls(
            name=payload["name"],
            email=payload.get("email", ""),
            preferences=payload.get("preferences", {}),
        )
        owner.pets = [Pet.from_dict(pet_data) for pet_data in payload.get("pets", [])]
        return owner


class Scheduler:
    """Coordinates task retrieval, sorting, filtering, and scheduling logic."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
        """Return all tasks across pets, optionally excluding completed tasks."""
        tasks = self.owner.all_tasks()
        if include_completed:
            return tasks
        return [(pet, task) for pet, task in tasks if not task.completed]

    def sort_tasks_by_time(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
        """Sort tasks chronologically across all pets."""
        return sorted(
            self.get_all_tasks(include_completed=include_completed),
            key=lambda item: item[1].due_datetime,
        )

    def sort_by_priority_then_time(
        self, include_completed: bool = True
    ) -> List[Tuple[Pet, Task]]:
        """Sort tasks by priority first, then by due time."""
        return sorted(
            self.get_all_tasks(include_completed=include_completed),
            key=lambda item: (item[1].priority_weight(), item[1].due_datetime),
        )

    def filter_tasks(
        self,
        *,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Filter tasks across pets by pet name, status, and/or priority."""
        filtered = self.get_all_tasks(include_completed=True)

        if pet_name is not None:
            normalized = pet_name.strip().lower()
            filtered = [(pet, task) for pet, task in filtered if pet.name.lower() == normalized]

        if completed is not None:
            filtered = [(pet, task) for pet, task in filtered if task.completed == completed]

        if priority is not None:
            priority = priority.lower()
            filtered = [(pet, task) for pet, task in filtered if task.priority == priority]

        return filtered

    def detect_conflicts(self) -> List[str]:
        """Return warnings for tasks scheduled at the exact same date/time."""
        warnings: List[str] = []
        ordered = self.sort_tasks_by_time(include_completed=False)

        for index, (pet_a, task_a) in enumerate(ordered):
            for pet_b, task_b in ordered[index + 1 :]:
                if task_a.due_datetime != task_b.due_datetime:
                    break
                warnings.append(
                    f"Conflict: {pet_a.name} has '{task_a.description}' and {pet_b.name} has "
                    f"'{task_b.description}' at {task_a.due_datetime.strftime('%Y-%m-%d %H:%M')}"
                )
        return warnings

    def mark_task_complete(self, pet_name: str, description: str) -> Optional[Task]:
        """Mark a task complete and create the next occurrence for recurring tasks."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None

        for task in pet.tasks:
            if task.description.lower() == description.lower() and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return task
        return None

    def next_available_slot(
        self,
        on_date: date,
        duration_minutes: int,
        start_hour: int = 8,
        end_hour: int = 20,
    ) -> Optional[time]:
        """Find the next open start time for a new task on a given date."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        existing = []
        for _, task in self.get_all_tasks(include_completed=False):
            if task.due_date == on_date:
                start_dt = task.due_datetime
                end_dt = start_dt + timedelta(minutes=task.duration_minutes)
                existing.append((start_dt, end_dt))

        existing.sort(key=lambda window: window[0])
        cursor = datetime.combine(on_date, time(start_hour, 0))
        day_end = datetime.combine(on_date, time(end_hour, 0))
        requested_end = cursor + timedelta(minutes=duration_minutes)

        if not existing and requested_end <= day_end:
            return cursor.time()

        for start_dt, end_dt in existing:
            if cursor + timedelta(minutes=duration_minutes) <= start_dt:
                return cursor.time()
            if end_dt > cursor:
                cursor = end_dt

        if cursor + timedelta(minutes=duration_minutes) <= day_end:
            return cursor.time()
        return None

    def agenda_table(
        self, sort_mode: str = "time", include_completed: bool = True
    ) -> List[Dict[str, str]]:
        """Return schedule rows formatted for terminal or Streamlit display."""
        if sort_mode == "priority":
            ordered = self.sort_by_priority_then_time(include_completed=include_completed)
        else:
            ordered = self.sort_tasks_by_time(include_completed=include_completed)

        rows = []
        for pet, task in ordered:
            rows.append(
                {
                    "Pet": pet.name,
                    "Species": pet.species,
                    "Task": task.description,
                    "Type": task.task_type.title(),
                    "Date": task.due_date.isoformat(),
                    "Time": task.due_time.strftime("%H:%M"),
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": task.formatted_priority(),
                    "Status": task.formatted_status(),
                    "Frequency": task.frequency.title(),
                }
            )
        return rows


__all__ = ["Task", "Pet", "Owner", "Scheduler"]