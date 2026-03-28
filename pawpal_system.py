from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Tuple


_PRIORITY_WEIGHTS = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

_PRIORITY_EMOJIS = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}


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
        """Validate and normalize task fields."""
        pass

    @property
    def due_datetime(self) -> datetime:
        """Return the combined due date and due time as a datetime."""
        raise NotImplementedError

    def mark_complete(self) -> None:
        """Mark the task as complete."""
        raise NotImplementedError

    def next_occurrence(self) -> Optional["Task"]:
        """Create the next instance for recurring tasks, if any."""
        raise NotImplementedError

    def priority_weight(self) -> int:
        """Return the numeric weight used for priority-based sorting."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the task for JSON storage."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize a task from a dictionary."""
        raise NotImplementedError

    def formatted_status(self) -> str:
        """Return a compact status string for CLI/UI display."""
        raise NotImplementedError

    def formatted_priority(self) -> str:
        """Return the priority with an emoji for easy display."""
        raise NotImplementedError


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
        raise NotImplementedError

    def list_tasks(self, include_completed: bool = True) -> List[Task]:
        """Return this pet's tasks, optionally excluding completed tasks."""
        raise NotImplementedError

    def task_count(self) -> int:
        """Return the number of tasks assigned to this pet."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the pet for JSON storage."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pet":
        """Deserialize a pet from a dictionary."""
        raise NotImplementedError


@dataclass
class Owner:
    """Represents the pet owner and the pets they manage."""

    name: str
    email: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        raise NotImplementedError

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return a pet by name if it exists."""
        raise NotImplementedError

    def all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all tasks across the owner's pets."""
        raise NotImplementedError

    def save_to_json(self, filepath: str) -> None:
        """Save the owner, pets, and tasks to disk as JSON."""
        raise NotImplementedError

    @classmethod
    def load_from_json(cls, filepath: str) -> "Owner":
        """Load an owner, pets, and tasks from a JSON file."""
        raise NotImplementedError


class Scheduler:
    """Coordinates task retrieval, sorting, filtering, and scheduling logic."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
        """Return all tasks across pets, optionally excluding completed tasks."""
        raise NotImplementedError

    def sort_tasks_by_time(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
        """Sort tasks chronologically across all pets."""
        raise NotImplementedError

    def sort_by_priority_then_time(
        self,
        include_completed: bool = True,
    ) -> List[Tuple[Pet, Task]]:
        """Sort tasks by priority first, then by due time."""
        raise NotImplementedError

    def filter_tasks(
        self,
        *,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Filter tasks across pets by pet name, status, and/or priority."""
        raise NotImplementedError

    def detect_conflicts(self) -> List[str]:
        """Return warnings for tasks scheduled at the exact same date/time."""
        raise NotImplementedError

    def mark_task_complete(self, pet_name: str, description: str) -> Optional[Task]:
        """Mark a task complete and create the next occurrence for recurring tasks."""
        raise NotImplementedError

    def next_available_slot(
        self,
        on_date: date,
        duration_minutes: int,
        start_hour: int = 8,
        end_hour: int = 20,
    ) -> Optional[time]:
        """Find the next open start time for a new task on a given date."""
        raise NotImplementedError

    def agenda_table(
        self,
        sort_mode: str = "time",
        include_completed: bool = True,
    ) -> List[Dict[str, str]]:
        """Return schedule rows formatted for terminal or UI display."""
        raise NotImplementedError


__all__ = ["Task", "Pet", "Owner", "Scheduler"]