from __future__ import annotations

from datetime import datetime
import tkinter as tk


class ReminderManager:
    def __init__(self, root: tk.Tk, tasks: list[dict], persistence) -> None:
        self.root = root
        self.tasks = tasks
        self.persistence = persistence
        self.interval_ms = 60_000

    def start(self) -> None:
        self.root.after(5_000, self.poll)

    def poll(self) -> None:
        now = datetime.utcnow()
        hour_min = now.strftime("%H:%M")
        for task in self.tasks:
            if task.get("completed"):
                continue
            should_notify = False
            if task.get("duration") and not task.get("last_reminder"):
                should_notify = True
            if task.get("reminder_time") == hour_min:
                should_notify = True
            if task["type"] == "health_required" and task["current_stage"] < task["stages"]:
                should_notify = True
            if should_notify:
                self.show_popup(task)
                task["last_reminder"] = now.isoformat()
                current = self.persistence.load_today()
                current["tasks"] = self.tasks
                self.persistence.save_today(current)
        self.root.after(self.interval_ms, self.poll)

    def show_popup(self, task: dict) -> None:
        popup = tk.Toplevel(self.root)
        popup.title("DEVQUEST REMINDER")
        popup.configure(bg="black")
        popup.geometry("320x120")
        label = tk.Label(
            popup,
            text=f"{task['name']} ({task['current_stage']}/{task['stages']})\n{task.get('prompt', 'Stay on quest.')}",
            bg="black",
            fg="#33ff33",
            font=("Courier New", 10),
            justify="left",
        )
        label.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Button(popup, text="Acknowledge", command=popup.destroy, font=("Courier New", 10)).pack(pady=4)
