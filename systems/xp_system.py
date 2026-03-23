from __future__ import annotations


def spend_xp(player: dict) -> dict:
    old_level = player.get("level", 0)
    new_level = player.get("xp", 0) // 100
    player["level"] = new_level
    if new_level > old_level:
        player.setdefault("unclaimed_rewards", 0)
        player["unclaimed_rewards"] += new_level - old_level
    return player
