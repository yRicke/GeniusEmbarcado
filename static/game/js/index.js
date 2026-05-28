const scoreEl = document.getElementById("score");
const roundEl = document.getElementById("round");
const timerEl = document.getElementById("timer");
const stageTimerEl = document.getElementById("stage-timer");
const stageScreenEl = document.getElementById("stage-screen");
const stageTextEl = document.getElementById("stage-text");
const messageEl = document.getElementById("message");
const bestScoreEl = document.getElementById("best-score");
const lastScoreEl = document.getElementById("last-score");
const attemptsEl = document.getElementById("attempts");
const attemptsListEl = document.getElementById("attempts-list");
const KEY_TO_COLOR = {
  1: "azul",
  2: "verde",
  3: "vermelho",
  4: "amarelo",
};

function readTimer(state) {
  if (state.phase === "countdown") return state.countdown_seconds_left;
  if (state.phase === "showing_sequence") return state.show_seconds_left;
  if (state.phase === "waiting_input") return state.input_seconds_left;
  if (state.phase === "game_over") return state.game_over_seconds_left;
  return null;
}

function timerText(value) {
  if (value === null || value === undefined) return "-";
  return `${value.toFixed(2)}s`;
}

function stageConfig(state) {
  if (state.phase === "countdown") {
    return {
      className: "black",
      text: `${state.countdown_value ?? 1}`,
      hideTimer: true,
    };
  }

  if (state.phase === "showing_sequence") {
    if (state.flash_color) {
      return {
        className: state.flash_color,
        text: "",
        hideTimer: false,
      };
    }
    return {
      className: "black",
      text: "",
      hideTimer: false,
    };
  }

  if (state.phase === "game_over") {
    return {
      className: "black",
      text: "VOCE PERDEU",
      hideTimer: true,
    };
  }

  if (state.phase === "waiting_input") {
    return {
      className: "neutral",
      text: "SUA VEZ",
      hideTimer: false,
    };
  }

  if (state.phase === "round_result") {
    return {
      className: "success",
      text: "ACERTOU",
      hideTimer: false,
    };
  }

  return {
    className: "black",
    text: "CLIQUE PARA INICIAR",
    hideTimer: true,
  };
}

function renderAttempts(items) {
  if (!items || items.length === 0) {
    attemptsListEl.innerHTML = '<div class="attempt-empty">Sem tentativas registradas.</div>';
    return;
  }

  attemptsListEl.innerHTML = items
    .map(
      (attempt) =>
        `<div class="attempt-row">#${attempt.id} | score: ${attempt.score} | rodada: ${attempt.rounds_completed} | seq: ${attempt.sequence_size} | motivo: ${attempt.failure_reason} | fim: ${attempt.ended_at}</div>`,
    )
    .join("");
}

function renderState(state) {
  const timer = readTimer(state);
  const config = stageConfig(state);

  scoreEl.textContent = state.score;
  roundEl.textContent = state.round_number;
  timerEl.textContent = timerText(timer);

  stageScreenEl.className = `stage-screen ${config.className}`;
  stageTextEl.textContent = config.text;

  if (config.hideTimer) {
    stageTimerEl.classList.add("hidden");
  } else {
    stageTimerEl.classList.remove("hidden");
    stageTimerEl.textContent = timerText(timer);
  }

  messageEl.textContent = state.message;
  bestScoreEl.textContent = state.summary.best_score;
  lastScoreEl.textContent = state.summary.last_score;
  attemptsEl.textContent = state.summary.total_attempts;
  renderAttempts(state.recent_attempts);
}

async function fetchState() {
  try {
    const response = await fetch("/api/state/");
    const data = await response.json();
    renderState(data);
  } catch {
    messageEl.textContent = "Falha ao consultar estado do jogo.";
  }
}

async function sendManual(color) {
  try {
    await fetch(`/api/button/${color}/`, { method: "POST" });
  } finally {
    await fetchState();
  }
}

window.addEventListener("keydown", (event) => {
  if (event.repeat) return;
  const color = KEY_TO_COLOR[event.key];
  if (!color) return;
  sendManual(color);
});

setInterval(fetchState, 120);
fetchState();
