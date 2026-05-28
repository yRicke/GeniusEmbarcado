from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from game.services.game_engine import GeniusGameEngine


class GeniusGameEngineTests(TestCase):
    def setUp(self) -> None:
        self.engine = GeniusGameEngine()

    def test_first_button_starts_countdown(self):
        state = self.engine.register_input("azul")

        self.assertEqual(state["phase"], "countdown")
        self.assertIsNotNone(state["countdown_seconds_left"])
        self.assertEqual(state["countdown_value"], 3)

    def test_correct_sequence_increments_score(self):
        self.engine._state["phase"] = "waiting_input"
        self.engine._state["sequence"] = ["azul"]
        self.engine._state["expected_index"] = 0
        self.engine._state["deadline"] = timezone.now() + timedelta(seconds=5)

        state = self.engine.register_input("azul")

        self.assertEqual(state["score"], 1)
        self.assertEqual(state["phase"], "round_result")

    def test_wrong_sequence_moves_to_game_over(self):
        self.engine._state["phase"] = "waiting_input"
        self.engine._state["sequence"] = ["azul"]
        self.engine._state["score"] = 3
        self.engine._state["round_number"] = 3
        self.engine._state["expected_index"] = 0
        self.engine._state["deadline"] = timezone.now() + timedelta(seconds=5)

        state = self.engine.register_input("verde")

        self.assertEqual(state["phase"], "game_over")
        self.assertEqual(state["score"], 0)
        self.assertEqual(state["message"], "Voce perdeu")
