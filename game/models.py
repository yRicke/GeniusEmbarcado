from django.db import models


class GameAttempt(models.Model):
    final_score = models.PositiveIntegerField(default=0)
    rounds_completed = models.PositiveIntegerField(default=0)
    failure_reason = models.CharField(max_length=120, blank=True)
    generated_sequence = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Tentativa {self.pk} - score {self.final_score}"


class ScoreSummary(models.Model):
    key = models.CharField(max_length=20, unique=True, default="global")
    best_score = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    last_score = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return (
            f"Resumo ({self.key}) - best: {self.best_score}, "
            f"tentativas: {self.total_attempts}"
        )
