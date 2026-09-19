"""Core rules and data-driven paths for the Arrow Escape game.

An arrow is a continuous orthogonal path made from board points.  Its final
point is the arrow head; the head direction decides whether the whole path
can leave the board.  Keeping path geometry in the rule engine means the
rendered line and the collision rules always describe the same object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable


Position = tuple[int, int]


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
    """One continuous path and the direction of its terminal arrow head."""

    row: int
    col: int
    direction: Direction
    path: tuple[Position, ...] = ()

    def __post_init__(self) -> None:
        normalized_path = self.path or ((self.row, self.col),)
        if normalized_path[-1] != (self.row, self.col):
            raise ValueError("Arrow head must be the final point in path")
        for previous, current in zip(normalized_path, normalized_path[1:]):
            if abs(previous[0] - current[0]) + abs(previous[1] - current[1]) != 1:
                raise ValueError(f"Arrow path must move orthogonally: {previous} -> {current}")
        if len(normalized_path) != len(set(normalized_path)):
            raise ValueError("Arrow path cannot visit a point twice")
        object.__setattr__(self, "path", tuple(normalized_path))


@dataclass(frozen=True)
class Level:
    """A complete, non-overlapping path layout."""

    number: int
    name: str
    arrows: tuple[ArrowSpec, ...]
    size: int = 7

    def __post_init__(self) -> None:
        heads = [(a.row, a.col) for a in self.arrows]
        if len(heads) != len(set(heads)):
            raise ValueError(f"Level {self.number} has overlapping arrow heads")
        occupied: set[Position] = set()
        for arrow in self.arrows:
            for row, col in arrow.path:
                if not (0 <= row < self.size and 0 <= col < self.size):
                    raise ValueError(f"Arrow outside board in level {self.number}")
                if (row, col) in occupied:
                    raise ValueError(f"Arrow paths overlap at {(row, col)}")
                occupied.add((row, col))


@dataclass
class ClickResult:
    """The result of a player's click, consumed by the UI."""

    kind: str
    row: int
    col: int
    message: str
    remaining_mistakes: int
    remaining_arrows: int
    collision_at: Position | None = None


@dataclass
class GameEngine:
    """State machine implementing the path-based game rules."""

    level: Level
    max_mistakes: int = 3
    active: dict[Position, ArrowSpec] = field(init=False)
    mistakes_remaining: int = field(init=False)
    status: str = field(init=False, default="playing")

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = {(arrow.row, arrow.col): arrow for arrow in self.level.arrows}
        self.mistakes_remaining = self.max_mistakes
        self.status = "playing"

    @property
    def remaining_arrows(self) -> int:
        return len(self.active)

    def _head_for_cell(self, row: int, col: int) -> Position | None:
        if (row, col) in self.active:
            return row, col
        for head, arrow in self.active.items():
            if (row, col) in arrow.path:
                return head
        return None

    def _first_blocker(self, row: int, col: int) -> Position | None:
        arrow = self.active[(row, col)]
        next_row, next_col = row + arrow.direction.dr, col + arrow.direction.dc
        occupied_by_others = {
            point
            for head, other in self.active.items()
            if head != (row, col)
            for point in other.path
        }
        while 0 <= next_row < self.level.size and 0 <= next_col < self.level.size:
            if (next_row, next_col) in occupied_by_others:
                return next_row, next_col
            next_row += arrow.direction.dr
            next_col += arrow.direction.dc
        return None

    def click(self, row: int, col: int) -> ClickResult:
        """Process a click on a path or its head.

        Clicking any occupied path point is accepted and resolves to that
        path's head, making the long lines easy to select while preserving the
        intended arrow-head interaction.
        """

        if self.status != "playing":
            return ClickResult("ignored", row, col, "当前关卡已结束，请重新开始。", self.mistakes_remaining, self.remaining_arrows)
        head = self._head_for_cell(row, col)
        if head is None:
            return ClickResult("empty", row, col, "请点击棋盘上的彩色线段。", self.mistakes_remaining, self.remaining_arrows)
        row, col = head

        blocker = self._first_blocker(row, col)
        if blocker is not None:
            self.mistakes_remaining -= 1
            if self.mistakes_remaining <= 0:
                self.status = "lost"
                message = "失误次数耗尽，本关失败。"
            else:
                message = f"发生碰撞！前方的线段挡住了去路，还剩 {self.mistakes_remaining} 次机会。"
            return ClickResult("collision", row, col, message, self.mistakes_remaining, self.remaining_arrows, blocker)

        arrow = self.active.pop((row, col))
        if not self.active:
            self.status = "cleared"
            message = "本关全部线段飞出，成功通关！"
        else:
            direction_text = {
                Direction.UP: "上",
                Direction.DOWN: "下",
                Direction.LEFT: "左",
                Direction.RIGHT: "右",
            }[arrow.direction]
            message = f"线段向{direction_text}飞出！"
        return ClickResult("launched", row, col, message, self.mistakes_remaining, self.remaining_arrows)


def path_arrow(path: Iterable[Position], direction: Direction) -> ArrowSpec:
    points = tuple(path)
    if not points:
        raise ValueError("Arrow path cannot be empty")
    return ArrowSpec(points[-1][0], points[-1][1], direction, points)


def make_level(number: int, name: str, arrows: Iterable[ArrowSpec]) -> Level:
    return Level(number, name, tuple(arrows))


def _rotate_position(position: Position) -> Position:
    row, col = position
    return col, 6 - row


def _mirror_position(position: Position) -> Position:
    row, col = position
    return row, 6 - col


def _rotate_direction(direction: Direction) -> Direction:
    return {
        Direction.UP: Direction.RIGHT,
        Direction.RIGHT: Direction.DOWN,
        Direction.DOWN: Direction.LEFT,
        Direction.LEFT: Direction.UP,
    }[direction]


def _mirror_direction(direction: Direction) -> Direction:
    return {
        Direction.UP: Direction.UP,
        Direction.DOWN: Direction.DOWN,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }[direction]


def _transform_level(
    source: Level,
    number: int,
    name: str,
    transform_position: Callable[[Position], Position],
    transform_direction: Callable[[Direction], Direction],
) -> Level:
    transformed = []
    for arrow in source.arrows:
        transformed_path = tuple(transform_position(point) for point in arrow.path)
        transformed.append(path_arrow(transformed_path, transform_direction(arrow.direction)))
    return make_level(number, name, transformed)


# The first layout covers every point in the 7x7 board exactly once.  The
# long paths deliberately turn several times, so the player sees a full
# connected maze rather than isolated single-cell arrows.
_BASE_LEVEL = make_level(
    1,
    "全盘连线",
    (
        path_arrow(((2, 0), (2, 1), (1, 1), (1, 0), (0, 0), (0, 1), (0, 2), (1, 2), (2, 2)), Direction.DOWN),
        path_arrow(((2, 5), (2, 4), (2, 3), (1, 3), (0, 3), (0, 4), (1, 4), (1, 5), (0, 5)), Direction.UP),
        path_arrow(((0, 6), (1, 6), (2, 6), (3, 6), (3, 5), (3, 4), (3, 3)), Direction.LEFT),
        path_arrow(((3, 0), (4, 0), (5, 0), (5, 1), (4, 1), (4, 2), (3, 2), (3, 1)), Direction.LEFT),
        path_arrow(((4, 3), (4, 4), (4, 5), (4, 6), (5, 6), (6, 6), (6, 5), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0)), Direction.LEFT),
        path_arrow(((5, 2), (5, 3), (5, 4), (5, 5)), Direction.RIGHT),
    ),
)


LEVELS: tuple[Level, ...] = (
    _BASE_LEVEL,
    _transform_level(_BASE_LEVEL, 2, "旋转回路", _rotate_position, _rotate_direction),
    _transform_level(_BASE_LEVEL, 3, "镜像连锁", _mirror_position, _mirror_direction),
)


def find_solution(level: Level) -> list[Position] | None:
    """Return one valid solution order, useful for tests and level QA."""

    engine = GameEngine(level)
    solution: list[Position] = []
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
