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

const runtimeMode = window.GENIUS_RUNTIME_MODE || "server";
const STORAGE_KEY = "genius-demo-state";
const COLORS = ["azul", "verde", "vermelho", "amarelo"];
const COUNTDOWN_SECONDS = 3;
const FIRST_INPUT_LIMIT_SECONDS = 5;
const MIN_INPUT_LIMIT_SECONDS = 2;
const ROUND_RESULT_DELAY_SECONDS = 1.5;
const SHOW_COLOR_SECONDS = 0.75;
const SHOW_GAP_SECONDS = 0.1;
const GAME_OVER_SECONDS = 3;

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
    text: "CLIQUE QUALQUER COR PARA INICIAR",
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

function demoNow() {
  return Date.now();
}

function demoReadStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function demoWriteStorage(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function demoSummarySnapshot() {
  const storage = demoReadStorage();
  return {
    best_score: storage.best_score || 0,
    last_score: storage.last_score || 0,
    total_attempts: storage.total_attempts || 0,
  };
}

function demoRecentAttempts() {
  const storage = demoReadStorage();
  return Array.isArray(storage.attempts) ? storage.attempts : [];
}

function createDemoEngine() {
  const state = {
    phase: "waiting_start",
    message: "Clique qualquer cor para iniciar.",
    score: 0,
    round_number: 0,
    sequence: [],
    user_progress: [],
    expected_index: 0,
    countdown_end_at: null,
    show_sequence_start_at: null,
    show_sequence_end_at: null,
    deadline_at: null,
    round_result_end_at: null,
    game_over_end_at: null,
    last_input: null,
    last_error: null,
  };

  function inputTimeLimit(index) {
    if (index <= 0) return FIRST_INPUT_LIMIT_SECONDS;
    return Math.max(MIN_INPUT_LIMIT_SECONDS, FIRST_INPUT_LIMIT_SECONDS - index);
  }

  function showDuration() {
    return state.sequence.length * (SHOW_COLOR_SECONDS + SHOW_GAP_SECONDS) * 1000;
  }

  function resetState() {
    state.phase = "waiting_start";
    state.message = "Clique qualquer cor para iniciar.";
    state.score = 0;
    state.round_number = 0;
    state.sequence = [];
    state.user_progress = [];
    state.expected_index = 0;
    state.countdown_end_at = null;
    state.show_sequence_start_at = null;
    state.show_sequence_end_at = null;
    state.deadline_at = null;
    state.round_result_end_at = null;
    state.game_over_end_at = null;
    state.last_input = null;
    state.last_error = null;
  }

  function recordAttempt(reason) {
    const storage = demoReadStorage();
    const attempts = Array.isArray(storage.attempts) ? storage.attempts : [];
    const score = Math.max(state.score, 0);
    const roundNumber = Math.max(state.round_number, 0);
    const lastId = storage.last_id || 0;
    const nextAttempt = {
      id: lastId + 1,
      score,
      rounds_completed: roundNumber,
      failure_reason: reason,
      sequence_size: state.sequence.length,
      ended_at: new Date().toLocaleString("pt-BR"),
    };

    demoWriteStorage({
      attempts: [nextAttempt, ...attempts].slice(0, 12),
      last_id: nextAttempt.id,
      total_attempts: (storage.total_attempts || 0) + 1,
      last_score: score,
      best_score: Math.max(storage.best_score || 0, score),
    });
  }

  function startCountdown() {
    state.phase = "countdown";
    state.countdown_end_at = demoNow() + COUNTDOWN_SECONDS * 1000;
    state.message = "Preparar...";
  }

  function nextRound() {
    state.round_number += 1;
    state.sequence.push(COLORS[Math.floor(Math.random() * COLORS.length)]);
    state.user_progress = [];
    state.expected_index = 0;
    state.phase = "showing_sequence";
    state.show_sequence_start_at = demoNow();
    state.show_sequence_end_at = state.show_sequence_start_at + showDuration();
    state.message = `Rodada ${state.round_number}: memorize a sequencia.`;
  }

  function beginInputPhase() {
    state.phase = "waiting_input";
    state.expected_index = 0;
    state.show_sequence_start_at = null;
    state.show_sequence_end_at = null;
    const limit = inputTimeLimit(0);
    state.deadline_at = demoNow() + limit * 1000;
    state.message = `Repita a sequencia. Voce tem ${limit}s para o proximo clique.`;
  }

  function toGameOver(reason) {
    recordAttempt(reason);
    state.phase = "game_over";
    state.message = "Voce perdeu";
    state.score = 0;
    state.round_number = 0;
    state.sequence = [];
    state.user_progress = [];
    state.expected_index = 0;
    state.countdown_end_at = null;
    state.show_sequence_start_at = null;
    state.show_sequence_end_at = null;
    state.deadline_at = null;
    state.round_result_end_at = null;
    state.game_over_end_at = demoNow() + GAME_OVER_SECONDS * 1000;
    state.last_error = reason;
  }

  function secondsLeft(timestamp) {
    if (!timestamp) return null;
    return Math.max(0, Number(((timestamp - demoNow()) / 1000).toFixed(2)));
  }

  function countdownValue() {
    if (state.phase !== "countdown" || !state.countdown_end_at) return null;
    return Math.max(1, Math.ceil((state.countdown_end_at - demoNow()) / 1000));
  }

  function flashColor() {
    if (state.phase !== "showing_sequence" || !state.show_sequence_start_at) return null;

    const elapsed = (demoNow() - state.show_sequence_start_at) / 1000;
    if (elapsed < 0) return null;

    const slot = SHOW_COLOR_SECONDS + SHOW_GAP_SECONDS;
    const index = Math.floor(elapsed / slot);
    if (index < 0 || index >= state.sequence.length) return null;

    const offset = elapsed - index * slot;
    return offset < SHOW_COLOR_SECONDS ? state.sequence[index] : null;
  }

  function syncTime() {
    const now = demoNow();

    if (state.phase === "countdown" && state.countdown_end_at && now >= state.countdown_end_at) {
      state.countdown_end_at = null;
      nextRound();
    }

    if (state.phase === "showing_sequence" && state.show_sequence_end_at && now >= state.show_sequence_end_at) {
      beginInputPhase();
    }

    if (state.phase === "waiting_input" && state.deadline_at && now > state.deadline_at) {
      toGameOver("Tempo esgotado");
    }

    if (state.phase === "round_result" && state.round_result_end_at && now >= state.round_result_end_at) {
      state.round_result_end_at = null;
      nextRound();
    }

    if (state.phase === "game_over" && state.game_over_end_at && now >= state.game_over_end_at) {
      resetState();
    }
  }

  function buildPayload() {
    return {
      phase: state.phase,
      message: state.message,
      score: state.score,
      round_number: state.round_number,
      sequence: state.sequence,
      user_progress: state.user_progress,
      expected_index: state.expected_index,
      countdown_seconds_left: secondsLeft(state.countdown_end_at),
      show_seconds_left: secondsLeft(state.show_sequence_end_at),
      input_seconds_left: secondsLeft(state.deadline_at),
      game_over_seconds_left: secondsLeft(state.game_over_end_at),
      countdown_value: countdownValue(),
      flash_color: flashColor(),
      last_input: state.last_input,
      last_error: state.last_error,
      summary: demoSummarySnapshot(),
      recent_attempts: demoRecentAttempts(),
    };
  }

  function getState() {
    syncTime();
    return buildPayload();
  }

  function registerInput(color, source = "manual") {
    const normalized = String(color || "")
      .trim()
      .toLowerCase();

    if (!COLORS.includes(normalized)) return getState();

    syncTime();

    if (state.phase === "waiting_start" || state.phase === "game_over") {
      if (state.phase === "game_over") resetState();
      state.last_input = { color: normalized, source };
      startCountdown();
      return buildPayload();
    }

    if (state.phase !== "waiting_input") {
      return buildPayload();
    }

    const expectedColor = state.sequence[state.expected_index];
    state.last_input = { color: normalized, source };

    if (normalized !== expectedColor) {
      toGameOver("Voce errou a sequencia");
      return buildPayload();
    }

    state.user_progress.push(normalized);
    state.expected_index += 1;

    if (state.expected_index >= state.sequence.length) {
      state.score += 1;
      state.phase = "round_result";
      state.round_result_end_at = demoNow() + ROUND_RESULT_DELAY_SECONDS * 1000;
      state.deadline_at = null;
      state.message = "Acertou! Proxima rodada...";
      return buildPayload();
    }

    const nextIndex = state.expected_index;
    const nextLimit = inputTimeLimit(nextIndex);
    state.deadline_at = demoNow() + nextLimit * 1000;
    state.message = `Correta. Proximo clique em ate ${nextLimit}s (${nextIndex + 1}/${state.sequence.length}).`;
    return buildPayload();
  }

  return { getState, registerInput };
}

const demoEngine = runtimeMode === "demo" ? createDemoEngine() : null;

async function fetchState() {
  if (runtimeMode === "demo") {
    renderState(demoEngine.getState());
    return;
  }

  try {
    const response = await fetch("/api/state/");
    const data = await response.json();
    renderState(data);
  } catch {
    messageEl.textContent = "Falha ao consultar estado do jogo.";
  }
}

async function sendManual(color) {
  if (runtimeMode === "demo") {
    renderState(demoEngine.registerInput(color));
    return;
  }

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
