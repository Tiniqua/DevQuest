from __future__ import annotations

import random
from collections import defaultdict

from systems.task_system import build_runtime_task


class DailyTaskGenerator:
    def __init__(self, persistence) -> None:
        self.persistence = persistence

    def generate(self, current_date: str, player: dict) -> dict:
        health = self.persistence.load_data("tasks_health.json")
        exercises = self.persistence.load_data("exercises.json")
        career = self.persistence.load_data("tasks_career.json")
        side = self.persistence.load_data("side_quests.json")
        relationship = self.persistence.load_data("relationship_quests.json")
        today_tasks = []

        required = [task for task in health if task["type"] == "health_required"]
        optional = [task for task in health if task["type"] == "health_optional"]
        today_tasks.extend(build_runtime_task(task) for task in required)
        today_tasks.extend(build_runtime_task(task) for task in random.sample(optional, k=min(3, len(optional))))
        if exercises:
            today_tasks.append(build_runtime_task(random.choice(exercises)))

        career_candidates = [task for task in career if self.matches_frequency(task, current_date)]
        for task in random.sample(career_candidates, k=min(random.randint(1, 2), len(career_candidates))):
            today_tasks.append(build_runtime_task(task))

        weighted_side = self.weighted_side(side)
        side_count = min(random.randint(1, 2), len(weighted_side))
        if side_count:
            sampled = random.sample(weighted_side, k=side_count)
            seen = set()
            for task in sampled:
                if task["id"] not in seen:
                    today_tasks.append(build_runtime_task(task))
                    seen.add(task["id"])
        if relationship:
            today_tasks.append(build_runtime_task(random.choice(relationship)))

        return {"date": current_date, "tasks": today_tasks, "notes": "", "summaries": []}

    def matches_frequency(self, task: dict, current_date: str) -> bool:
        day = int(current_date[-2:])
        frequency = task.get("frequency", "daily")
        if frequency == "daily":
            return True
        if frequency == "alternate":
            return day % 2 == 0
        if frequency == "weekly":
            return day % 7 == 0 or day % 7 == 1
        return True

    def weighted_side(self, side_quests: list[dict]) -> list[dict]:
        weighted = []
        rarity_weights = defaultdict(lambda: 1, {"common": 4, "uncommon": 2, "rare": 1})
        for quest in side_quests:
            weighted.extend([quest] * rarity_weights[quest.get("rarity", "common")])
        return weighted
