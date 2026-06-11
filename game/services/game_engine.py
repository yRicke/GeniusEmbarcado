import math
import random
import threading
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from game.constants import (
    COLORS,
    COUNTDOWN_SECONDS,
    FIRST_INPUT_LIMIT_SECONDS,
    GAME_OVER_SECONDS,
    MIN_INPUT_LIMIT_SECONDS,
    ROUND_RESULT_DELAY_SECONDS,
    SHOW_COLOR_SECONDS,
    SHOW_GAP_SECONDS,
)
from game.repositories import get_recent_attempts, get_summary_snapshot, record_failed_attempt


class GeniusGameEngine:
    """Keeps Genius game state and processes button events."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {}
        self._reset_state()

    def _now(self) -> datetime:
        return timezone.now()

    def _reset_state(self) -> None:
        self._state = {
            "phase": "waiting_start",
            "message": "Clique qualquer cor para iniciar.",
            "score": 0,
            "round_number": 0,
            "sequence": [],
            "user_progress": [],
            "expected_index": 0,
            "deadline": None,
            "countdown_end": None,
            "show_sequence_end": None,
            "show_sequence_start": None,
            "round_result_end": None,
            "game_over_end": None,
            "last_input": None,
            "last_error": None,
            "updated_at": self._now(),
        }

    def _input_time_limit(self, index: int) -> int:
        if index <= 0:
            return FIRST_INPUT_LIMIT_SECONDS
        return max(MIN_INPUT_LIMIT_SECONDS, FIRST_INPUT_LIMIT_SECONDS - index)

    def _show_duration(self) -> float:
        per_color = SHOW_COLOR_SECONDS + SHOW_GAP_SECONDS
        return len(self._state["sequence"]) * per_color

    def _next_round(self) -> None:
        self._state["round_number"] += 1
        self._state["sequence"].append(random.choice(COLORS))
        self._state["user_progress"] = []
        self._state["expected_index"] = 0
        self._state["phase"] = "showing_sequence"

        now = self._now()
        self._state["show_sequence_start"] = now
        self._state["show_sequence_end"] = now + timedelta(seconds=self._show_duration())
        self._state["message"] = f"Rodada {self._state['round_number']}: memorize a sequencia."

    def _begin_input_phase(self) -> None:
        self._state["phase"] = "waiting_input"
        self._state["expected_index"] = 0
        self._state["show_sequence_start"] = None
        self._state["show_sequence_end"] = None

        first_limit = self._input_time_limit(0)
        self._state["deadline"] = self._now() + timedelta(seconds=first_limit)
        self._state["message"] = f"Repita a sequencia. Voce tem {first_limit}s para o proximo clique."

    def _start_countdown(self) -> None:
        self._state["phase"] = "countdown"
        self._state["countdown_end"] = self._now() + timedelta(seconds=COUNTDOWN_SECONDS)
        self._state["message"] = "Preparar..."

    def _to_game_over(self, reason: str) -> None:
        previous_score = self._state["score"]
        rounds_completed = self._state["round_number"]
        sequence_snapshot = list(self._state["sequence"])

        record_failed_attempt(
            score=previous_score,
            rounds_completed=rounds_completed,
            reason=reason,
            sequence=sequence_snapshot,
        )

        self._state["phase"] = "game_over"
        self._state["score"] = 0
        self._state["round_number"] = 0
        self._state["sequence"] = []
        self._state["user_progress"] = []
        self._state["expected_index"] = 0
        self._state["deadline"] = None
        self._state["countdown_end"] = None
        self._state["show_sequence_start"] = None
        self._state["show_sequence_end"] = None
        self._state["round_result_end"] = None
        self._state["game_over_end"] = self._now() + timedelta(seconds=GAME_OVER_SECONDS)
        self._state["message"] = "Voce perdeu"
        self._state["last_error"] = reason

    def _move_game_over_to_waiting(self) -> None:
        if self._state["phase"] != "game_over":
            return

        if not self._state["game_over_end"] or self._now() < self._state["game_over_end"]:
            return

        self._reset_state()

    def _sync_time(self) -> None:
        now = self._now()

        if self._state["phase"] == "countdown" and self._state["countdown_end"] and now >= self._state["countdown_end"]:
            self._state["countdown_end"] = None
            self._next_round()

        if (
            self._state["phase"] == "showing_sequence"
            and self._state["show_sequence_end"]
            and now >= self._state["show_sequence_end"]
        ):
            self._begin_input_phase()

        if self._state["phase"] == "waiting_input" and self._state["deadline"] and now > self._state["deadline"]:
            self._to_game_over("Tempo esgotado")

        if (
            self._state["phase"] == "round_result"
            and self._state["round_result_end"]
            and now >= self._state["round_result_end"]
        ):
            self._state["round_result_end"] = None
            self._next_round()

        self._move_game_over_to_waiting()

    def register_input(self, color: str, source: str = "arduino") -> dict[str, Any]:
        normalized = color.strip().lower()
        if normalized not in COLORS:
            return self.get_state()

        with self._lock:
            self._sync_time()

            if self._state["phase"] == "waiting_start":
                self._state["last_input"] = {"color": normalized, "source": source}
                self._start_countdown()
                self._state["updated_at"] = self._now()
                return self._build_payload()

            if self._state["phase"] == "game_over":
                self._reset_state()
                self._state["last_input"] = {"color": normalized, "source": source}
                self._start_countdown()
                self._state["updated_at"] = self._now()
                return self._build_payload()

            if self._state["phase"] != "waiting_input":
                return self._build_payload()

            expected_index = self._state["expected_index"]
            expected_color = self._state["sequence"][expected_index]
            self._state["last_input"] = {"color": normalized, "source": source}

            if normalized != expected_color:
                self._to_game_over("Voce errou a sequencia")
                self._state["updated_at"] = self._now()
                return self._build_payload()

            self._state["user_progress"].append(normalized)
            self._state["expected_index"] += 1

            if self._state["expected_index"] >= len(self._state["sequence"]):
                self._state["score"] += 1
                self._state["phase"] = "round_result"
                self._state["round_result_end"] = self._now() + timedelta(seconds=ROUND_RESULT_DELAY_SECONDS)
                self._state["deadline"] = None
                self._state["message"] = "Acertou! Proxima rodada..."
            else:
                next_index = self._state["expected_index"]
                next_limit = self._input_time_limit(next_index)
                self._state["deadline"] = self._now() + timedelta(seconds=next_limit)
                self._state["message"] = (
                    f"Correta. Proximo clique em ate {next_limit}s "
                    f"({next_index + 1}/{len(self._state['sequence'])})."
                )

            self._state["updated_at"] = self._now()
            return self._build_payload()

    def _seconds_left(self, until: datetime | None) -> float | None:
        if not until:
            return None
        remaining = (until - self._now()).total_seconds()
        return round(max(remaining, 0), 2)

    def _countdown_value(self) -> int | None:
        if self._state["phase"] != "countdown":
            return None
        seconds_left = self._seconds_left(self._state["countdown_end"])
        if seconds_left is None:
            return None
        return max(1, math.ceil(seconds_left))

    def _sequence_flash_color(self) -> str | None:
        if self._state["phase"] != "showing_sequence":
            return None

        start = self._state["show_sequence_start"]
        if not start:
            return None

        elapsed = (self._now() - start).total_seconds()
        if elapsed < 0:
            return None

        slot = SHOW_COLOR_SECONDS + SHOW_GAP_SECONDS
        index = int(elapsed // slot)
        if index < 0 or index >= len(self._state["sequence"]):
            return None

        offset = elapsed - (index * slot)
        if SHOW_GAP_SECONDS <= 0:
            return self._state["sequence"][index]

        if offset < SHOW_COLOR_SECONDS:
            return self._state["sequence"][index]
        return None

    def _build_payload(self) -> dict[str, Any]:
        summary = get_summary_snapshot()
        return {
            "phase": self._state["phase"],
            "message": self._state["message"],
            "score": self._state["score"],
            "round_number": self._state["round_number"],
            "sequence": self._state["sequence"],
            "user_progress": self._state["user_progress"],
            "expected_index": self._state["expected_index"],
            "countdown_seconds_left": self._seconds_left(self._state["countdown_end"]),
            "show_seconds_left": self._seconds_left(self._state["show_sequence_end"]),
            "input_seconds_left": self._seconds_left(self._state["deadline"]),
            "game_over_seconds_left": self._seconds_left(self._state["game_over_end"]),
            "countdown_value": self._countdown_value(),
            "flash_color": self._sequence_flash_color(),
            "last_input": self._state["last_input"],
            "last_error": self._state["last_error"],
            "summary": summary,
            "recent_attempts": get_recent_attempts(),
        }

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            self._sync_time()
            return self._build_payload()


game_engine = GeniusGameEngine()
