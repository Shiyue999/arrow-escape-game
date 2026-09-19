"""Core rules for the Arrow Escape game.

The rule engine is intentionally independent from Tkinter so that the most
important game behaviour can be tested without opening a window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Direction(Enum):
    """The four possible arrow directions."""

    UP = (-1, 0, "↑")
    DOWN = (1, 0, "↓")
    LEFT = (0, -1, "←")
    RIGHT = (0, 1, "→")

    @property
    def dr(self) -> int:
        return self.value[0]

    @property
    def dc(self) -> int:
        return self.value[1]

    @property
    def symbol(self) -> str:
        return self.value[2]


@dataclass(frozen=True)
class ArrowSpec:
    """An arrow's immutable position and direction in a level."""

    row: int
    col: int
    direction: Direction


@dataclass(frozen=True)
class Level:
    """A complete, data-driven level description."""

    number: int
    name: str
    arrows: tuple[ArrowSpec, ...]
    size: int = 7

    def __post_init__(self) -> None:
        positions = [(a.row, a.col) for a in self.arrows]
        if len(positions) != len(set(positions)):
            raise ValueError(f"Level {self.number} has overlapping arrows")
        for arrow in self.arrows:
            if not (0 <= arrow.row < self.size and 0 <= arrow.col < self.size):
                raise ValueError(f"Arrow outside board in level {self.number}")


@dataclass
class ClickResult:
    """The result of a player's click, consumed by the UI."""

    kind: str
    row: int
    col: int
    message: str
    remaining_mistakes: int
    remaining_arrows: int
    collision_at: tuple[int, int] | None = None


@dataclass
class GameEngine:
    """State machine implementing all rules required by the assignment."""

    level: Level
    max_mistakes: int = 3
    active: dict[tuple[int, int], Direction] = field(init=False)
    mistakes_remaining: int = field(init=False)
    status: str = field(init=False, default="playing")

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = {(a.row, a.col): a.direction for a in self.level.arrows}
        self.mistakes_remaining = self.max_mistakes
        self.status = "playing"

    @property
    def remaining_arrows(self) -> int:
        return len(self.active)

    def _first_blocker(self, row: int, col: int) -> tuple[int, int] | None:
        direction = self.active[(row, col)]
        next_row, next_col = row + direction.dr, col + direction.dc
        while 0 <= next_row < self.level.size and 0 <= next_col < self.level.size:
            if (next_row, next_col) in self.active:
                return next_row, next_col
            next_row += direction.dr
            next_col += direction.dc
        return None

    def click(self, row: int, col: int) -> ClickResult:
        """Process one grid click and return a UI-friendly event."""

        if self.status != "playing":
            return ClickResult("ignored", row, col, "当前关卡已结束，请重新开始。", self.mistakes_remaining, self.remaining_arrows)
        if (row, col) not in self.active:
            return ClickResult("empty", row, col, "请点击棋盘上的箭头。", self.mistakes_remaining, self.remaining_arrows)

        blocker = self._first_blocker(row, col)
        if blocker is not None:
            self.mistakes_remaining -= 1
            if self.mistakes_remaining <= 0:
                self.status = "lost"
                message = "失误次数耗尽，本关失败。"
            else:
                message = f"发生碰撞！前方的箭头挡住了去路，还剩 {self.mistakes_remaining} 次机会。"
            return ClickResult("collision", row, col, message, self.mistakes_remaining, self.remaining_arrows, blocker)

        direction = self.active.pop((row, col))
        if not self.active:
            self.status = "cleared"
            message = "本关全部箭头飞出，成功通关！"
        else:
            direction_text = {
                Direction.UP: "上",
                Direction.DOWN: "下",
                Direction.LEFT: "左",
                Direction.RIGHT: "右",
            }[direction]
            message = f"箭头向{direction_text}飞出！"
        return ClickResult("launched", row, col, message, self.mistakes_remaining, self.remaining_arrows)


def make_level(number: int, name: str, arrows: Iterable[tuple[int, int, Direction]]) -> Level:
    return Level(number, name, tuple(ArrowSpec(*item) for item in arrows))


LEVELS: tuple[Level, ...] = (
    make_level(1, "初识方向", (
        (1, 0, Direction.LEFT), (1, 3, Direction.LEFT), (3, 3, Direction.UP),
        (2, 5, Direction.RIGHT), (5, 5, Direction.UP), (4, 1, Direction.DOWN),
        (6, 3, Direction.UP),
    )),
    make_level(2, "交错路径", (
        (0, 4, Direction.UP), (2, 4, Direction.UP), (4, 4, Direction.UP),
        (1, 0, Direction.LEFT), (1, 1, Direction.LEFT), (4, 1, Direction.UP),
        (5, 2, Direction.LEFT), (5, 6, Direction.LEFT), (6, 3, Direction.UP),
        (4, 3, Direction.RIGHT),
    )),
    make_level(3, "最终连锁", (
        (0, 1, Direction.UP), (2, 1, Direction.UP), (4, 1, Direction.UP),
        (1, 5, Direction.RIGHT), (1, 3, Direction.RIGHT), (3, 5, Direction.UP),
        (6, 5, Direction.UP), (5, 0, Direction.LEFT), (5, 2, Direction.LEFT),
        (5, 4, Direction.LEFT), (6, 3, Direction.UP), (4, 3, Direction.RIGHT),
    )),
)


def find_solution(level: Level) -> list[tuple[int, int]] | None:
    """Return one valid solution order, useful for tests and level QA."""

    engine = GameEngine(level)
    solution: list[tuple[int, int]] = []
    changed = True
    while changed:
        changed = False
        for position in list(engine.active):
            result = engine.click(*position)
            if result.kind == "launched":
                solution.append(position)
                changed = True
        if engine.status == "cleared":
            return solution
    return None
