from django.db import OperationalError, ProgrammingError

from .models import GameAttempt, ScoreSummary


def record_failed_attempt(score: int, rounds_completed: int, reason: str, sequence: list[str]) -> None:
    try:
        GameAttempt.objects.create(
            final_score=max(score, 0),
            rounds_completed=max(rounds_completed, 0),
            failure_reason=reason,
            generated_sequence=sequence,
        )

        summary, _ = ScoreSummary.objects.get_or_create(key="global")
        summary.total_attempts += 1
        summary.last_score = max(score, 0)
        summary.best_score = max(summary.best_score, score)
        summary.save(update_fields=["total_attempts", "last_score", "best_score", "updated_at"])
    except (OperationalError, ProgrammingError):
        # Database may not be migrated in first run.
        pass


def get_summary_snapshot() -> dict:
    try:
        summary, _ = ScoreSummary.objects.get_or_create(key="global")
        return {
            "best_score": summary.best_score,
            "total_attempts": summary.total_attempts,
            "last_score": summary.last_score,
        }
    except (OperationalError, ProgrammingError):
        return {"best_score": 0, "total_attempts": 0, "last_score": 0}


def get_recent_attempts(limit: int = 12) -> list[dict]:
    try:
        attempts = GameAttempt.objects.all()[:limit]
        return [
            {
                "id": attempt.id,
                "score": attempt.final_score,
                "rounds_completed": attempt.rounds_completed,
                "failure_reason": attempt.failure_reason,
                "sequence_size": len(attempt.generated_sequence or []),
                "ended_at": attempt.ended_at.strftime("%d/%m %H:%M:%S"),
            }
            for attempt in attempts
        ]
    except (OperationalError, ProgrammingError):
        return []
