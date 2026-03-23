from __future__ import annotations

REQUIRED_PENALTIES = {
    "brush_teeth": 10,
    "water_goal": 10,
    "exercise_daily": 15,
}


SPECIAL_NAMES = {
    "brush teeth": "brush_teeth",
    "drink water": "water_goal",
    "exercise": "exercise_daily",
}


def apply_end_of_day_penalties(player: dict, today: dict) -> dict:
    for task in today.get("tasks", []):
        if task.get("completed"):
            continue
        if task["type"] in {"health_required", "exercise"}:
            task["failed"] = True
            key = task.get("penalty_key") or SPECIAL_NAMES.get(task["name"].lower())
            damage = REQUIRED_PENALTIES.get(key, task.get("damage_on_fail", 0))
            player["health"] = max(0, player.get("health", 100) - damage)
    return today
