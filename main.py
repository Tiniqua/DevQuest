from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from systems.persistence import PersistenceManager
from systems.task_system import categorize_tasks, format_task_progress
from systems.xp_system import spend_xp
from systems.generator import DailyTaskGenerator
from systems.health_system import apply_end_of_day_penalties
from systems.reminder_system import ReminderManager

APP_TITLE = "DEVQUEST"
MONO_FONT = ("Courier New", 10)
HEADER_FONT = ("Courier New", 12, "bold")
NOTE_XP = 5


class DevQuestApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.configure(bg="black")
        self.root.geometry("980x700")

        self.persistence = PersistenceManager(base_dir=".")
        self.generator = DailyTaskGenerator(self.persistence)
        self.player = self.persistence.load_player()
        self.today = self.persistence.load_today()
        self.handle_daily_cycle()
        self.tasks_by_id = {task["id"]: task for task in self.today["tasks"]}
        self.reminder_manager = ReminderManager(root, self.today["tasks"], self.persistence)

        self.status_text = tk.StringVar()
        self.task_list_var = tk.StringVar(value=[])
        self.career_list_var = tk.StringVar(value=[])
        self.quest_list_var = tk.StringVar(value=[])
        self.rewards_var = tk.StringVar(value=[])

        self.build_ui()
        self.refresh_all_views()
        self.reminder_manager.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def handle_daily_cycle(self) -> None:
        current_date = self.persistence.today_date()
        if self.today.get("date") != current_date:
            if self.today.get("date"):
                finalized = apply_end_of_day_penalties(self.player, self.today)
                self.persistence.append_history(finalized, self.player)
            self.player["health"] = 100
            self.today = self.generator.generate(current_date, self.player)
            self.persistence.save_player(self.player)
            self.persistence.save_today(self.today)

    def build_ui(self) -> None:
        banner = tk.Label(
            self.root,
            text="+------------------------------+\n|          DEVQUEST            |\n+------------------------------+",
            font=HEADER_FONT,
            justify="left",
            fg="#33ff33",
            bg="black",
        )
        banner.pack(anchor="w", padx=12, pady=12)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="black", borderwidth=0)
        style.configure("TNotebook.Tab", font=MONO_FONT)

        self.status_tab = self.make_tab(notebook, "[STATUS]")
        self.tasks_tab = self.make_tab(notebook, "[TASKS]")
        self.career_tab = self.make_tab(notebook, "[CAREER]")
        self.quests_tab = self.make_tab(notebook, "[QUESTS]")
        self.notes_tab = self.make_tab(notebook, "[NOTES]")

        self.build_status_tab()
        self.build_tasks_tab()
        self.build_career_tab()
        self.build_quests_tab()
        self.build_notes_tab()

    def make_tab(self, notebook: ttk.Notebook, title: str) -> tk.Frame:
        frame = tk.Frame(notebook, bg="black")
        notebook.add(frame, text=title)
        return frame

    def build_status_tab(self) -> None:
        tk.Label(self.status_tab, textvariable=self.status_text, justify="left", font=MONO_FONT, fg="#33ff33", bg="black").pack(anchor="w", padx=12, pady=12)
        self.reward_listbox = tk.Listbox(self.status_tab, listvariable=self.rewards_var, font=MONO_FONT, width=80, height=10, bg="#111111", fg="#33ff33")
        self.reward_listbox.pack(anchor="w", padx=12, pady=12)
        reward_frame = tk.Frame(self.status_tab, bg="black")
        reward_frame.pack(anchor="w", padx=12, pady=6)
        tk.Button(reward_frame, text="Claim Unlock", command=self.claim_reward, font=MONO_FONT).pack(side="left", padx=4)
        tk.Button(reward_frame, text="Spend 25 XP", command=lambda: self.spend_xp_for_reward(25), font=MONO_FONT).pack(side="left", padx=4)

    def build_tasks_tab(self) -> None:
        self.task_listbox = tk.Listbox(self.tasks_tab, listvariable=self.task_list_var, font=MONO_FONT, width=110, height=22, bg="#111111", fg="#33ff33")
        self.task_listbox.pack(anchor="w", padx=12, pady=12)
        button_frame = tk.Frame(self.tasks_tab, bg="black")
        button_frame.pack(anchor="w", padx=12, pady=6)
        tk.Button(button_frame, text="Complete Stage", command=self.complete_stage, font=MONO_FONT).pack(side="left", padx=4)
        tk.Button(button_frame, text="Mark Complete", command=self.mark_complete, font=MONO_FONT).pack(side="left", padx=4)

    def build_career_tab(self) -> None:
        tk.Label(self.career_tab, text="Career prompts and visibility actions", font=MONO_FONT, fg="#33ff33", bg="black").pack(anchor="w", padx=12, pady=6)
        self.career_listbox = tk.Listbox(self.career_tab, listvariable=self.career_list_var, font=MONO_FONT, width=110, height=24, bg="#111111", fg="#33ff33")
        self.career_listbox.pack(anchor="w", padx=12, pady=12)

    def build_quests_tab(self) -> None:
        tk.Label(self.quests_tab, text="Side quests and relationship quests", font=MONO_FONT, fg="#33ff33", bg="black").pack(anchor="w", padx=12, pady=6)
        self.quest_listbox = tk.Listbox(self.quests_tab, listvariable=self.quest_list_var, font=MONO_FONT, width=110, height=24, bg="#111111", fg="#33ff33")
        self.quest_listbox.pack(anchor="w", padx=12, pady=12)

    def build_notes_tab(self) -> None:
        frame = tk.Frame(self.notes_tab, bg="black")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(frame, text="Daily Notes / Summary", font=MONO_FONT, fg="#33ff33", bg="black").pack(anchor="w", pady=4)
        self.notes_text = tk.Text(frame, font=MONO_FONT, width=100, height=24, bg="#111111", fg="#33ff33", insertbackground="#33ff33")
        self.notes_text.pack(fill="both", expand=True, pady=6)
        self.notes_text.insert("1.0", self.today.get("notes", ""))
        tk.Button(frame, text="Save Note (+5 XP)", command=self.save_notes, font=MONO_FONT).pack(anchor="w", pady=6)

    def render_bar(self, current: int, maximum: int = 100, width: int = 20) -> str:
        filled = max(0, min(width, int((current / maximum) * width))) if maximum else 0
        return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"

    def refresh_all_views(self) -> None:
        categories = categorize_tasks(self.today["tasks"])
        xp_remaining = 100 - (self.player["xp"] % 100)
        self.status_text.set(
            f"Date: {self.today['date']}\n"
            f"Level : {self.player['level']}\n"
            f"XP    : {self.player['xp']} {self.render_bar(self.player['xp'] % 100)} -> next in {xp_remaining}\n"
            f"Health: {self.player['health']} {self.render_bar(self.player['health'])}\n"
            f"Weight: {self.player.get('weight', 0)}\n"
            f"Stats : {self.player.get('stats', {})}"
        )
        self.task_list_var.set([format_task_progress(task) for task in self.today["tasks"]])
        self.career_list_var.set([format_task_progress(task) for task in categories["career"]])
        self.quest_list_var.set([format_task_progress(task) for task in categories["quests"]])
        self.rewards_var.set(self.persistence.list_reward_status(self.player))

    def selected_task(self, listbox: tk.Listbox, bucket: list[dict]) -> dict | None:
        if not listbox.curselection():
            return None
        index = listbox.curselection()[0]
        if index >= len(bucket):
            return None
        return bucket[index]

    def complete_stage(self) -> None:
        task = self.selected_task(self.task_listbox, self.today["tasks"])
        if not task:
            return
        if task["completed"]:
            messagebox.showinfo(APP_TITLE, "Task already complete.")
            return
        task["current_stage"] += 1
        stage_xp = task.get("xp_per_stage", 0)
        if stage_xp:
            self.player["xp"] += stage_xp
        if task["current_stage"] >= task["stages"]:
            self.finish_task(task)
        self.after_progress_update()

    def mark_complete(self) -> None:
        task = self.selected_task(self.task_listbox, self.today["tasks"])
        if not task:
            return
        self.finish_task(task)
        self.after_progress_update()

    def finish_task(self, task: dict) -> None:
        if task["completed"]:
            return
        task["completed"] = True
        task["current_stage"] = task["stages"]
        self.player["xp"] += task.get("xp", 0)
        self.player["stats"]["discipline"] = self.player["stats"].get("discipline", 0) + 1

    def after_progress_update(self) -> None:
        self.player = spend_xp(self.player)
        self.persistence.save_player(self.player)
        self.persistence.save_today(self.today)
        self.refresh_all_views()

    def save_notes(self) -> None:
        note = self.notes_text.get("1.0", "end").strip()
        self.today["notes"] = note
        self.today.setdefault("summaries", []).append({"text": note, "xp_awarded": NOTE_XP})
        self.player["xp"] += NOTE_XP
        self.player = spend_xp(self.player)
        self.persistence.save_player(self.player)
        self.persistence.save_today(self.today)
        self.refresh_all_views()
        messagebox.showinfo(APP_TITLE, "Notes saved. +5 XP")

    def claim_reward(self) -> None:
        unlocked = self.persistence.claim_next_reward(self.player)
        if unlocked:
            messagebox.showinfo(APP_TITLE, unlocked)
            self.persistence.save_player(self.player)
            self.refresh_all_views()
            return
        messagebox.showinfo(APP_TITLE, "No unclaimed reward available.")

    def spend_xp_for_reward(self, amount: int) -> None:
        result = self.persistence.spend_xp_reward(self.player, amount)
        if result:
            self.persistence.save_player(self.player)
            self.refresh_all_views()
            messagebox.showinfo(APP_TITLE, result)
        else:
            messagebox.showinfo(APP_TITLE, "Not enough XP or no instant reward matched.")

    def on_close(self) -> None:
        self.persistence.save_player(self.player)
        self.persistence.save_today(self.today)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = DevQuestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
