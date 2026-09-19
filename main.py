"""Tkinter front end for the Arrow Escape game."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from game_logic import LEVELS, Direction, GameEngine, Level


WINDOW_BG = "#10182c"
PANEL_BG = "#172440"
BOARD_BG = "#0d1426"
GRID_LINE = "#29395d"
TEXT = "#f4f7ff"
MUTED = "#aebbd7"
ACCENT = "#55d6be"
ARROW_COLORS = {
    Direction.UP: "#ffcf5c",
    Direction.DOWN: "#ff8c69",
    Direction.LEFT: "#a889ff",
    Direction.RIGHT: "#61b6ff",
}


class ArrowEscapeApp(tk.Tk):
    """A compact, keyboard-friendly graphical game."""

    def __init__(self) -> None:
        super().__init__()
        self.title("一箭又一箭 · Arrow Escape")
        self.geometry("930x760")
        self.minsize(760, 650)
        self.configure(bg=WINDOW_BG)
        self.current_level_index = 0
        self.engine: GameEngine | None = None
        self.mode = "start"
        self.feedback_job: str | None = None
        self._build_widgets()
        self.show_start()

    def _build_widgets(self) -> None:
        self.header = tk.Frame(self, bg=WINDOW_BG)
        self.header.pack(fill="x", padx=30, pady=(24, 10))
        tk.Label(self.header, text="一箭又一箭", font=("Microsoft YaHei UI", 25, "bold"), fg=TEXT, bg=WINDOW_BG).pack(side="left")
        tk.Label(self.header, text="ARROW ESCAPE", font=("Segoe UI", 11, "bold"), fg=ACCENT, bg=WINDOW_BG).pack(side="left", padx=(14, 0), pady=(9, 0))

        self.content = tk.Frame(self, bg=WINDOW_BG)
        self.content.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        self.status_panel = tk.Frame(self.content, bg=PANEL_BG, width=220)
        self.status_panel.pack(side="left", fill="y", padx=(0, 20))
        self.status_panel.pack_propagate(False)
        self.level_label = self._label(self.status_panel, "", 16, "bold", TEXT)
        self.level_label.pack(anchor="w", padx=20, pady=(25, 4))
        self.name_label = self._label(self.status_panel, "", 11, "normal", MUTED)
        self.name_label.pack(anchor="w", padx=20, pady=(0, 24))
        self.remaining_label = self._label(self.status_panel, "", 12, "normal", TEXT)
        self.remaining_label.pack(anchor="w", padx=20, pady=8)
        self.mistake_label = self._label(self.status_panel, "", 12, "normal", TEXT)
        self.mistake_label.pack(anchor="w", padx=20, pady=8)
        self.tip_label = self._label(self.status_panel, "点击箭头，让它沿方向飞出棋盘。", 10, "normal", MUTED)
        self.tip_label.pack(anchor="w", padx=20, pady=(28, 10), fill="x")
        self.restart_button = self._button(self.status_panel, "重新开始本关", self.restart_level)
        self.restart_button.pack(side="bottom", fill="x", padx=20, pady=20)

        self.board_frame = tk.Frame(self.content, bg=PANEL_BG)
        self.board_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(self.board_frame, bg=BOARD_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=18)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self.draw_board())

        self.feedback = tk.Label(self, text="", font=("Microsoft YaHei UI", 11), fg=TEXT, bg=WINDOW_BG, anchor="center")
        self.feedback.pack(fill="x", padx=30, pady=(0, 18))

    @staticmethod
    def _label(parent: tk.Misc, text: str, size: int, weight: str, color: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Microsoft YaHei UI", size, weight), fg=color, bg=PANEL_BG)

    @staticmethod
    def _button(parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(parent, text=text, command=command, font=("Microsoft YaHei UI", 11, "bold"), fg=WINDOW_BG, bg=ACCENT, activebackground="#7ae9d3", relief="flat", cursor="hand2", padx=10, pady=8)

    def show_start(self) -> None:
        self.mode = "start"
        self.status_panel.pack_forget()
        self.board_frame.pack_forget()
        self.feedback.configure(text="")
        self.start_card = tk.Frame(self.content, bg=PANEL_BG)
        self.start_card.pack(fill="both", expand=True)
        tk.Label(self.start_card, text="准备好清空棋盘了吗？", font=("Microsoft YaHei UI", 28, "bold"), fg=TEXT, bg=PANEL_BG).pack(pady=(115, 12))
        tk.Label(self.start_card, text="观察方向，规划顺序，让每一支箭头安全飞出。", font=("Microsoft YaHei UI", 13), fg=MUTED, bg=PANEL_BG).pack(pady=(0, 35))
        self._button(self.start_card, "开始游戏", self.start_game).pack(ipadx=30)
        tk.Label(self.start_card, text="规则：前方没有箭头才能飞出；碰撞会消耗一次机会。", font=("Microsoft YaHei UI", 10), fg=MUTED, bg=PANEL_BG).pack(pady=(75, 0))

    def start_game(self) -> None:
        if hasattr(self, "start_card"):
            self.start_card.destroy()
        self.current_level_index = 0
        self.mode = "playing"
        self.status_panel.pack(side="left", fill="y", padx=(0, 20))
        self.board_frame.pack(side="left", fill="both", expand=True)
        self.load_level(0)

    def load_level(self, index: int) -> None:
        self.current_level_index = index
        self.engine = GameEngine(LEVELS[index])
        self.mode = "playing"
        self.update_status()
        self.feedback.configure(text=f"第 {self.engine.level.number} 关：{self.engine.level.name}", fg=ACCENT)
        self.draw_board()

    def update_status(self) -> None:
        if self.engine is None:
            return
        level = self.engine.level
        self.level_label.configure(text=f"第 {level.number} 关")
        self.name_label.configure(text=level.name)
        self.remaining_label.configure(text=f"剩余箭头：{self.engine.remaining_arrows}")
        hearts = "●" * self.engine.mistakes_remaining + "○" * (self.engine.max_mistakes - self.engine.mistakes_remaining)
        self.mistake_label.configure(text=f"失误机会：{hearts}", fg="#ff8c69" if self.engine.mistakes_remaining < 3 else TEXT)

    def board_geometry(self) -> tuple[float, float, float]:
        assert self.engine is not None
        size = self.engine.level.size
        width = max(200, self.canvas.winfo_width())
        height = max(200, self.canvas.winfo_height())
        cell = min(width, height) / size
        return (width - cell * size) / 2, (height - cell * size) / 2, cell

    def draw_board(self) -> None:
        if self.engine is None or self.mode not in {"playing", "lost", "victory"}:
            return
        self.canvas.delete("all")
        left, top, cell = self.board_geometry()
        size = self.engine.level.size
        for row in range(size):
            for col in range(size):
                x0, y0 = left + col * cell, top + row * cell
                self.canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell, outline=GRID_LINE, width=1)
        for (row, col), direction in self.engine.active.items():
            self.draw_arrow(row, col, direction)

    def draw_arrow(self, row: int, col: int, direction: Direction, tag: str = "arrow") -> None:
        left, top, cell = self.board_geometry()
        cx = left + (col + 0.5) * cell
        cy = top + (row + 0.5) * cell
        color = ARROW_COLORS[direction]
        self.canvas.create_oval(cx - cell * 0.30, cy - cell * 0.30, cx + cell * 0.30, cy + cell * 0.30, fill="#1c2d4d", outline=color, width=2, tags=tag)
        dx, dy = direction.dc, direction.dr
        start_x, start_y = cx - dx * cell * 0.22, cy - dy * cell * 0.22
        end_x, end_y = cx + dx * cell * 0.25, cy + dy * cell * 0.25
        self.canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=max(3, int(cell * 0.09)), arrow=tk.LAST, arrowshape=(cell * 0.20, cell * 0.24, cell * 0.10), tags=tag)
        self.canvas.create_text(cx, cy - cell * 0.38, text=direction.symbol, fill=color, font=("Segoe UI Symbol", max(12, int(cell * 0.22)), "bold"), tags=tag)

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.engine is None or self.mode != "playing":
            return
        left, top, cell = self.board_geometry()
        col = int((event.x - left) // cell)
        row = int((event.y - top) // cell)
        if not (0 <= row < self.engine.level.size and 0 <= col < self.engine.level.size):
            return
        result = self.engine.click(row, col)
        self.show_feedback(result.message, "#ff8c69" if result.kind == "collision" else ACCENT)
        if result.kind == "collision":
            self.flash_collision(result.collision_at)
        elif result.kind == "launched":
            self.animate_launch(result.row, result.col, self.engine.level)
        self.update_status()
        if self.engine.status == "lost":
            self.after(450, self.show_lost)
        elif self.engine.status == "cleared":
            self.after(450, self.advance_after_clear)

    def show_feedback(self, text: str, color: str = TEXT) -> None:
        if self.feedback_job is not None:
            self.after_cancel(self.feedback_job)
        self.feedback.configure(text=text, fg=color)
        self.feedback_job = self.after(3000, lambda: self.feedback.configure(text=""))

    def flash_collision(self, position: tuple[int, int] | None) -> None:
        if position is None:
            return
        left, top, cell = self.board_geometry()
        row, col = position
        x0, y0 = left + col * cell, top + row * cell
        rect = self.canvas.create_rectangle(x0 + 4, y0 + 4, x0 + cell - 4, y0 + cell - 4, outline="#ff5e6c", width=4, tags="collision")
        self.after(220, lambda: self.canvas.delete(rect))

    def animate_launch(self, row: int, col: int, level: Level) -> None:
        direction = next(a.direction for a in level.arrows if a.row == row and a.col == col)
        left, top, cell = self.board_geometry()
        cx = left + (col + 0.5) * cell
        cy = top + (row + 0.5) * cell
        end_x = cx + direction.dc * cell * 0.42
        end_y = cy + direction.dr * cell * 0.42
        pulse = self.canvas.create_line(cx, cy, end_x, end_y, fill=ARROW_COLORS[direction], width=max(3, int(cell * 0.10)), arrow=tk.LAST, tags="pulse")
        self.after(180, lambda: self.canvas.delete(pulse))
        self.after(190, self.draw_board)

    def restart_level(self) -> None:
        if self.engine is None:
            self.start_game()
            return
        self.load_level(self.current_level_index)

    def advance_after_clear(self) -> None:
        if self.engine is None or self.engine.status != "cleared":
            return
        if self.current_level_index + 1 < len(LEVELS):
            self.load_level(self.current_level_index + 1)
        else:
            self.show_victory()

    def show_lost(self) -> None:
        if self.engine is None or self.engine.status != "lost":
            return
        self.mode = "lost"
        self.draw_board()
        self.feedback.configure(text="本关失败，点击“重新开始本关”再试一次。", fg="#ff8c69")
        messagebox.showinfo("本关失败", "失误次数已经用完。\n重新观察方向后再挑战吧！")

    def show_victory(self) -> None:
        self.mode = "victory"
        self.feedback.configure(text="恭喜完成全部 3 关！", fg=ACCENT)
        messagebox.showinfo("全部通关", "恭喜！你已经完成全部关卡。")


if __name__ == "__main__":
    app = ArrowEscapeApp()
    app.mainloop()
