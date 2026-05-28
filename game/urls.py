from django.urls import path

from game import views

app_name = "game"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/state/", views.game_state, name="game_state"),
    path("api/button/<str:color>/", views.manual_button_event, name="manual_button_event"),
]
