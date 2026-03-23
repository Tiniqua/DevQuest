from __future__ import annotations

from typing import Iterable


GENERAL_TYPES = {"health_required", "health_optional", "exercise"}
CAREER_TYPES = {"career"}
QUEST_TYPES = {"side", "relationship"}


def build_runtime_task(definition: dict) -> dict:
    stages = definition.get("stages", 1)
    task = {
        **definition,
        "stages": stages,
        "current_stage": 0,
        "completed": False,
        "failed": False,
        "last_reminder": None,
    }
    if stages > 1 and "xp_per_stage" not in task:
        task["xp_per_stage"] = definition.get("xp", 0) // stages
        task["xp"] = definition.get("xp", 0) % stages
    return task


def format_task_progress(task: dict) -> str:
    flags = []
    if task.get("completed"):
        flags.append("DONE")
    if task.get("failed"):
        flags.append("FAIL")
    flag_text = f" [{' '.join(flags)}]" if flags else ""
    prompt = f" | prompt: {task['prompt']}" if task.get("prompt") else ""
    return (
        f"{task['name']} ({task['type']}) {task['current_stage']}/{task['stages']}"
        f" | xp:{task.get('xp', 0)}"
        f"{prompt}{flag_text}"
    )


def categorize_tasks(tasks: Iterable[dict]) -> dict[str, list[dict]]:
    categories = {"general": [], "career": [], "quests": []}
    for task in tasks:
        if task["type"] in GENERAL_TYPES:
            categories["general"].append(task)
        elif task["type"] in CAREER_TYPES:
            categories["career"].append(task)
        elif task["type"] in QUEST_TYPES:
            categories["quests"].append(task)
    return categories
