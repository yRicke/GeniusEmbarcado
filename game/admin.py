from django.contrib import admin

from .models import GameAttempt, ScoreSummary


@admin.register(GameAttempt)
class GameAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "final_score",
        "rounds_completed",
        "failure_reason",
        "started_at",
        "ended_at",
    )
    list_filter = ("started_at", "ended_at")
    search_fields = ("failure_reason",)


@admin.register(ScoreSummary)
class ScoreSummaryAdmin(admin.ModelAdmin):
    list_display = ("key", "best_score", "total_attempts", "last_score", "updated_at")
