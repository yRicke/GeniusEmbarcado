from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from game.services import arduino_listener, game_engine


def _ensure_listener_started() -> None:
    if settings.GENIUS_RUNTIME_MODE != "server":
        return
    arduino_listener.start(lambda color: game_engine.register_input(color=color, source="arduino"))


@require_GET
def index(request):
    if settings.GENIUS_RUNTIME_MODE == "server":
        _ensure_listener_started()
    return render(request, "game/index.html", {"runtime_mode": settings.GENIUS_RUNTIME_MODE})


@require_GET
def game_state(request):
    _ensure_listener_started()
    state = game_engine.get_state()
    return JsonResponse(state)


@csrf_exempt
@require_POST
def manual_button_event(request, color: str):
    """Optional endpoint for tests without Arduino."""
    _ensure_listener_started()
    state = game_engine.register_input(color=color, source="manual")
    return JsonResponse(state)
