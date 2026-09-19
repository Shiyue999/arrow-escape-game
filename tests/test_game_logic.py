import unittest

from game_logic import GameEngine, LEVELS, find_solution


class GameLogicTests(unittest.TestCase):
    def test_paths_are_long_and_arrow_heads_continue_straight(self):
        for level in LEVELS:
            for arrow in level.arrows:
                self.assertGreaterEqual(len(arrow.path), 4)
                previous, head = arrow.path[-2:]
                final_step = (head[0] - previous[0], head[1] - previous[1])
                self.assertEqual(final_step, (arrow.direction.dr, arrow.direction.dc))

    def test_first_level_covers_every_board_point_once(self):
        occupied = {point for arrow in LEVELS[0].arrows for point in arrow.path}
        self.assertEqual(len(occupied), 49)
        self.assertEqual(sum(len(arrow.path) for arrow in LEVELS[0].arrows), 49)

    def test_all_levels_have_a_valid_solution(self):
        for level in LEVELS:
            solution = find_solution(level)
            self.assertIsNotNone(solution, level.name)
            self.assertEqual(len(solution), len(level.arrows))
            engine = GameEngine(level)
            for position in solution:
                self.assertEqual(engine.click(*position).kind, "launched")
            self.assertEqual(engine.status, "cleared")

    def test_clear_arrow_when_path_is_empty(self):
        engine = GameEngine(LEVELS[0])
        result = engine.click(3, 0)
        self.assertEqual(result.kind, "launched")
        self.assertNotIn((3, 1), engine.active)
        self.assertEqual(engine.mistakes_remaining, 3)

    def test_collision_keeps_arrow_and_consumes_one_mistake(self):
        engine = GameEngine(LEVELS[0])
        result = engine.click(2, 2)
        self.assertEqual(result.kind, "collision")
        self.assertIn((2, 2), engine.active)
        self.assertEqual(result.collision_at, (3, 2))
        self.assertEqual(engine.mistakes_remaining, 2)

    def test_three_collisions_end_the_level(self):
        engine = GameEngine(LEVELS[0])
        for _ in range(3):
            result = engine.click(2, 2)
        self.assertEqual(result.kind, "collision")
        self.assertEqual(engine.status, "lost")
        self.assertEqual(engine.mistakes_remaining, 0)
        self.assertEqual(engine.remaining_arrows, len(LEVELS[0].arrows))

    def test_reset_restores_arrows_and_mistakes(self):
        engine = GameEngine(LEVELS[0])
        engine.click(3, 0)
        engine.click(2, 2)
        engine.reset()
        self.assertEqual(engine.status, "playing")
        self.assertEqual(engine.mistakes_remaining, 3)
        self.assertEqual(engine.remaining_arrows, len(LEVELS[0].arrows))

    def test_empty_click_does_not_change_state(self):
        engine = GameEngine(LEVELS[0])
        result = engine.click(-1, -1)
        self.assertEqual(result.kind, "empty")
        self.assertEqual(engine.mistakes_remaining, 3)
        self.assertEqual(engine.remaining_arrows, len(LEVELS[0].arrows))


if __name__ == "__main__":
    unittest.main()
