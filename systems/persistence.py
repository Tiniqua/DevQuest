from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_PLAYER = {
    "xp": 0,
    "level": 0,
    "health": 100,
    "weight": 0,
    "stats": {"visibility": 0, "discipline": 0, "health": 0},
    "unclaimed_rewards": 0,
    "claimed_unlocks": [],
    "spent_rewards": [],
}

DEFAULT_TODAY = {"date": "", "tasks": [], "notes": "", "summaries": []}


class PersistenceManager:
    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.data_dir = self.base / "data"
        self.save_dir = self.base / "save"
        self.player_path = self.save_dir / "player.json"
        self.today_path = self.save_dir / "today.json"
        self.history_path = self.save_dir / "history.log"
        self.rewards_path = self.data_dir / "rewards.json"

    def today_date(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _load_json(self, path: Path, fallback: Any) -> Any:
        if not path.exists():
            return fallback
        return json.loads(path.read_text())

    def _save_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))

    def load_player(self) -> dict:
        player = self._load_json(self.player_path, DEFAULT_PLAYER.copy())
        merged = DEFAULT_PLAYER.copy()
        merged.update(player)
        merged["stats"] = {**DEFAULT_PLAYER["stats"], **player.get("stats", {})}
        return merged

    def save_player(self, player: dict) -> None:
        self._save_json(self.player_path, player)

    def load_today(self) -> dict:
        today = self._load_json(self.today_path, DEFAULT_TODAY.copy())
        merged = DEFAULT_TODAY.copy()
        merged.update(today)
        return merged

    def save_today(self, today: dict) -> None:
        self._save_json(self.today_path, today)

    def load_data(self, filename: str) -> list[dict]:
        return self._load_json(self.data_dir / filename, [])

    def append_history(self, today: dict, player: dict) -> None:
        entry = {
            "date": today.get("date"),
            "xp": player.get("xp", 0),
            "health_end": player.get("health", 0),
            "tasks_completed": sum(1 for task in today.get("tasks", []) if task.get("completed")),
            "tasks_failed": sum(1 for task in today.get("tasks", []) if task.get("failed")),
            "weight": player.get("weight", 0),
            "sleep_hours": today.get("sleep_hours", 0),
        }
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def reward_catalog(self) -> list[dict]:
        return self.load_data("rewards.json")

    def list_reward_status(self, player: dict) -> list[str]:
        lines = []
        for reward in self.reward_catalog():
            if reward["type"] in {"unlock", "milestone"}:
                status = "UNLOCKED" if player["level"] >= reward.get("level", 0) else f"LOCKED@L{reward.get('level', 0)}"
                if reward["name"] in player.get("claimed_unlocks", []):
                    status = "CLAIMED"
                lines.append(f"{reward['name']} [{reward['type']}] - {status}")
            else:
                lines.append(f"{reward['name']} [instant] - cost {reward.get('cost_xp', 0)} XP")
        lines.append(f"Unclaimed level rewards: {player.get('unclaimed_rewards', 0)}")
        return lines

    def claim_next_reward(self, player: dict) -> str | None:
        if player.get("unclaimed_rewards", 0) <= 0:
            return None
        for reward in self.reward_catalog():
            if reward["type"] in {"unlock", "milestone"} and player["level"] >= reward.get("level", 0):
                if reward["name"] not in player.get("claimed_unlocks", []):
                    player.setdefault("claimed_unlocks", []).append(reward["name"])
                    player["unclaimed_rewards"] -= 1
                    return f"Unlocked reward: {reward['name']}"
        return None

    def spend_xp_reward(self, player: dict, amount: int) -> str | None:
        if player.get("xp", 0) < amount:
            return None
        for reward in self.reward_catalog():
            if reward["type"] == "instant" and reward.get("cost_xp") == amount:
                player["xp"] -= amount
                player.setdefault("spent_rewards", []).append(reward["name"])
                return f"Spent {amount} XP on {reward['name']}"
        return None
