"""Tkinter front end for the Arrow Escape game.

The visual language follows the supplied reference: a dark blue-grey board,
dot-grid cells, colourful line arrows, compact status information and a clear
flight animation when an arrow leaves the board.
"""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox

from game_logic import LEVELS, ArrowSpec, Direction, GameEngine, Level


WINDOW_BG = "#10182c"
PANEL_BG = "#172440"
BOARD_BG = "#202943"
GRID_DOT = "#3a486b"
BOARD_BORDER = "#334365"
TEXT = "#f4f7ff"
MUTED = "#aebbd7"
ACCENT = "#55d6be"
ARROW_COLORS = {
    Direction.UP: "#ffcf5c",
    Direction.DOWN: "#ff8c69",
    Direction.LEFT: "#b38cff",
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
        self.timer_job: str | None = None
        self.level_started_at = time.monotonic()
        self.animation_active = False
        self._build_widgets()
        self.show_start()

    def _build_widgets(self) -> None:
        self.header = tk.Frame(self, bg=WINDOW_BG)
        self.header.pack(fill="x", padx=30, pady=(22, 10))
        tk.Label(
            self.header,
            text="一箭又一箭",
            font=("Microsoft YaHei UI", 25, "bold"),
            fg=TEXT,
            bg=WINDOW_BG,
        ).pack(side="left")
        tk.Label(
            self.header,
            text="ARROW ESCAPE",
            font=("Segoe UI", 11, "bold"),
            fg=ACCENT,
            bg=WINDOW_BG,
        ).pack(side="left", padx=(14, 0), pady=(9, 0))
        tk.Label(
            self.header,
            text="点击线段，让箭头安全离场",
            font=("Microsoft YaHei UI", 10),
            fg=MUTED,
            bg=WINDOW_BG,
        ).pack(side="right", pady=(9, 0))

        self.content = tk.Frame(self, bg=WINDOW_BG)
        self.content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.status_panel = tk.Frame(self.content, bg=PANEL_BG, width=220)
        self.status_panel.pack(side="left", fill="y", padx=(0, 20))
        self.status_panel.pack_propagate(False)
        tk.Label(self.status_panel, text="当前关卡", font=("Microsoft YaHei UI", 10), fg=MUTED, bg=PANEL_BG).pack(anchor="w", padx=20, pady=(25, 2))
        self.level_label = self._label(self.status_panel, "", 20, "bold", TEXT)
        self.level_label.pack(anchor="w", padx=20, pady=(0, 2))
        self.name_label = self._label(self.status_panel, "", 11, "normal", MUTED)
        self.name_label.pack(anchor="w", padx=20, pady=(0, 22))
        self.timer_label = self._label(self.status_panel, "⏱ 00:00", 12, "normal", TEXT)
        self.timer_label.pack(anchor="w", padx=20, pady=7)
        self.remaining_label = self._label(self.status_panel, "", 12, "normal", TEXT)
        self.remaining_label.pack(anchor="w", padx=20, pady=7)
        self.mistake_label = self._label(self.status_panel, "", 12, "normal", TEXT)
        self.mistake_label.pack(anchor="w", padx=20, pady=7)
        self.tip_label = self._label(self.status_panel, "前方没有其他箭头时，线段会飞出棋盘。", 10, "normal", MUTED)
        self.tip_label.pack(anchor="w", padx=20, pady=(28, 10), fill="x")
        self.restart_button = self._button(self.status_panel, "重新开始本关", self.restart_level)
        self.restart_button.pack(side="bottom", fill="x", padx=20, pady=20)

        self.board_frame = tk.Frame(self.content, bg=PANEL_BG)
        self.board_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(self.board_frame, bg=BOARD_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=18)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self.draw_board())

        self.feedback = tk.Label(
            self,
            text="",
            font=("Microsoft YaHei UI", 11),
            fg=TEXT,
            bg=WINDOW_BG,
            anchor="center",
        )
        self.feedback.pack(fill="x", padx=30, pady=(0, 18))

    @staticmethod
    def _label(parent: tk.Misc, text: str, size: int, weight: str, color: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Microsoft YaHei UI", size, weight), fg=color, bg=PANEL_BG)

    @staticmethod
    def _button(parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Microsoft YaHei UI", 11, "bold"),
            fg=WINDOW_BG,
            bg=ACCENT,
            activebackground="#7ae9d3",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
        )

    def show_start(self) -> None:
        self.mode = "start"
        self.status_panel.pack_forget()
        self.board_frame.pack_forget()
        self.feedback.configure(text="")
        self.start_card = tk.Frame(self.content, bg=PANEL_BG)
        self.start_card.pack(fill="both", expand=True)
        tk.Label(self.start_card, text="准备好清空棋盘了吗？", font=("Microsoft YaHei UI", 28, "bold"), fg=TEXT, bg=PANEL_BG).pack(pady=(115, 12))
        tk.Label(self.start_card, text="观察线段方向，规划顺序，让每一支箭头安全飞出。", font=("Microsoft YaHei UI", 13), fg=MUTED, bg=PANEL_BG).pack(pady=(0, 35))
        self._button(self.start_card, "开始游戏", self.start_game).pack(ipadx=30)
        tk.Label(self.start_card, text="规则：前方没有箭头才能飞出；碰撞会消耗一次机会。", font=("Microsoft YaHei UI", 10), fg=MUTED, bg=PANEL_BG).pack(pady=(75, 0))

    def start_game(self) -> None:
        for card_name in ("start_card", "victory_card"):
            card = getattr(self, card_name, None)
            if card is not None:
                card.destroy()
                setattr(self, card_name, None)
        self.current_level_index = 0
        self.mode = "playing"
        self.status_panel.pack(side="left", fill="y", padx=(0, 20))
        self.board_frame.pack(side="left", fill="both", expand=True)
        self.load_level(0)

    def load_level(self, index: int) -> None:
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.current_level_index = index
        self.engine = GameEngine(LEVELS[index])
        self.level_started_at = time.monotonic()
        self.mode = "playing"
        self.animation_active = False
        self.update_status()
        self.update_timer()
        self.feedback.configure(text=f"第 {self.engine.level.number} 关：{self.engine.level.name}", fg=ACCENT)
        self.draw_board()

    def update_status(self) -> None:
        if self.engine is None:
            return
        level = self.engine.level
        self.level_label.configure(text=f"第 {level.number} 关")
        self.name_label.configure(text=level.name)
        self.remaining_label.configure(text=f"剩余箭头：{self.engine.remaining_arrows}")
        hearts = "♥" * self.engine.mistakes_remaining + "♡" * (self.engine.max_mistakes - self.engine.mistakes_remaining)
        self.mistake_label.configure(text=f"失误机会：{hearts}", fg="#ff7180")

    def update_timer(self) -> None:
        if self.engine is None:
            return
        elapsed = int(time.monotonic() - self.level_started_at)
        minutes, seconds = divmod(elapsed, 60)
        self.timer_label.configure(text=f"⏱ {minutes:02d}:{seconds:02d}")
        if self.mode == "playing":
            self.timer_job = self.after(1000, self.update_timer)

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
        self.canvas.create_rectangle(left - 12, top - 12, left + size * cell + 12, top + size * cell + 12, outline=BOARD_BORDER, width=2)
        for row in range(size):
            for col in range(size):
                cx = left + (col + 0.5) * cell
                cy = top + (row + 0.5) * cell
                radius = max(2.5, cell * 0.045)
                self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=GRID_DOT, outline="")
        for arrow in self.engine.active.values():
            self.draw_arrow(arrow)

    def draw_arrow(self, arrow: ArrowSpec, tag: str = "arrow") -> None:
        """Draw the complete curved/orthogonal path and its terminal head."""

        left, top, cell = self.board_geometry()
        direction = arrow.direction
        color = ARROW_COLORS[direction]
        coordinates: list[float] = []
        for row, col in arrow.path:
            coordinates.extend((left + (col + 0.5) * cell, top + (row + 0.5) * cell))
        head_row, head_col = arrow.path[-1]
        head_x = left + (head_col + 0.5) * cell
        head_y = top + (head_row + 0.5) * cell
        coordinates.extend((head_x + direction.dc * cell * 0.42, head_y + direction.dr * cell * 0.42))
        width = max(5, int(cell * 0.075))
        self.canvas.create_line(*coordinates, fill="#121b31", width=width + 5, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags=tag)
        self.canvas.create_line(*coordinates, fill=color, width=width, capstyle=tk.ROUND, joinstyle=tk.ROUND, arrow=tk.LAST, arrowshape=(cell * 0.22, cell * 0.25, cell * 0.10), tags=tag)

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.engine is None or self.mode != "playing" or self.animation_active:
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
            self.after(520, self.advance_after_clear)

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
        cx = left + (col + 0.5) * cell
        cy = top + (row + 0.5) * cell
        pulse = self.canvas.create_oval(cx - cell * 0.34, cy - cell * 0.34, cx + cell * 0.34, cy + cell * 0.34, outline="#ff5e6c", width=4, tags="collision")
        self.after(260, lambda: self.canvas.delete(pulse))

    def animate_launch(self, row: int, col: int, level: Level) -> None:
        """Unwind a folded line along its own points before it exits.

        The path is not translated as one rigid shape.  Instead, its tail is
        progressively trimmed from point to point while the terminal arrow
        grows beyond the board.  This is the same visual language as the
        reference video: every bend participates in the launch trajectory.
        """

        arrow = next(a for a in level.arrows if a.row == row and a.col == col)
        direction = arrow.direction
        left, top, cell = self.board_geometry()
        size = level.size
        head_x = left + (col + 0.5) * cell
        head_y = top + (row + 0.5) * cell
        if direction.dc > 0:
            distance = (size - col) * cell + cell * 0.75
        elif direction.dc < 0:
            distance = (col + 1) * cell + cell * 0.75
        elif direction.dr > 0:
            distance = (size - row) * cell + cell * 0.75
        else:
            distance = (row + 1) * cell + cell * 0.75
        dx, dy = direction.dc, direction.dr
        frames = max(28, len(arrow.path) * 4)
        self.animation_active = True
        self.draw_board()
        current_items: list[int] = []

        def step(frame: int) -> None:
            for item in current_items:
                self.canvas.delete(item)
            current_items.clear()
            progress = min(1.0, frame / frames)
            eased = 1 - (1 - progress) ** 3
            cut_distance = eased * max(0, len(arrow.path) - 1)
            cut_index = min(int(cut_distance), len(arrow.path) - 1)
            cut_fraction = cut_distance - cut_index
            cut_row, cut_col = arrow.path[cut_index]
            if cut_index < len(arrow.path) - 1:
                next_row, next_col = arrow.path[cut_index + 1]
                cut_row += (next_row - cut_row) * cut_fraction
                cut_col += (next_col - cut_col) * cut_fraction

            coordinates: list[float] = [
                left + (cut_col + 0.5) * cell,
                top + (cut_row + 0.5) * cell,
            ]
            for path_row, path_col in arrow.path[cut_index + 1 :]:
                coordinates.extend((left + (path_col + 0.5) * cell, top + (path_row + 0.5) * cell))

            extension = cell * 0.42 + distance * eased
            tip_x = head_x + dx * extension
            tip_y = head_y + dy * extension
            coordinates.extend((tip_x, tip_y))
            color = ARROW_COLORS[direction]
            shadow = self.canvas.create_line(*coordinates, fill="#121b31", width=max(5, int(cell * 0.075)) + 5, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags="flight")
            line = self.canvas.create_line(*coordinates, fill=color, width=max(5, int(cell * 0.075)), capstyle=tk.ROUND, joinstyle=tk.ROUND, arrow=tk.LAST, arrowshape=(cell * 0.22, cell * 0.25, cell * 0.10), tags="flight")
            current_items.extend((shadow, line))
            if frame < frames:
                self.after(22, lambda: step(frame + 1))
            else:
                for item in current_items:
                    self.canvas.delete(item)
                current_items.clear()
                self.animation_active = False

        step(0)

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
        self.status_panel.pack_forget()
        self.board_frame.pack_forget()
        self.victory_card = tk.Frame(self.content, bg=PANEL_BG)
        self.victory_card.pack(fill="both", expand=True)
        tk.Label(self.victory_card, text="胜利！", font=("Microsoft YaHei UI", 32, "bold"), fg=ACCENT, bg=PANEL_BG).pack(pady=(105, 12))
        tk.Label(self.victory_card, text="你已经清空全部 3 个关卡。", font=("Microsoft YaHei UI", 14), fg=TEXT, bg=PANEL_BG).pack(pady=(0, 32))
        self._button(self.victory_card, "再挑战一次", self.start_game).pack(ipadx=25)
        self.feedback.configure(text="全部关卡完成！", fg=ACCENT)


if __name__ == "__main__":
    app = ArrowEscapeApp()
    app.mainloop()
