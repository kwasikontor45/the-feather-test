// judge's chat interface
const socket = io();

const roundNumEl = document.getElementById('round-num');
const birdStatusDot = document.getElementById('bird-status-dot');
const birdStatusText = document.getElementById('bird-status-text');
const logA = document.getElementById('log-a');
const logB = document.getElementById('log-b');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const guessSection = document.getElementById('guess-section');

let currentRound = 0;
let waitingForReplies = false;
let repliesReceived = 0;   // tracks A and B replies per round

// ── connect ──────────────────────────────────────────────────
socket.on('connect', () => {
  socket.emit('judge_join', { room_code: ROOM_CODE });
  enableInput();
});

socket.on('status', (data) => {
  currentRound = data.round || 0;
  roundNumEl.textContent = currentRound;
  if (data.bird_connected) {
    setBirdStatus(true);
  }
  enableInput();
});

socket.on('bird_arrived', () => {
  setBirdStatus(true);
  enableInput();
  appendSystem('Bird has entered the aviary. Ask your first question.');
});

socket.on('bird_left', () => {
  setBirdStatus(false);
  appendSystem('Bird disconnected.');
});

// ── round flow ────────────────────────────────────────────────
socket.on('round_started', (data) => {
  currentRound = data.round;
  roundNumEl.textContent = currentRound;
  repliesReceived = 0;
  disableInput();

  appendQuestion(logA, data.question);
  appendQuestion(logB, data.question);

  // show typing indicator in both lanes
  showTyping('A');
  showTyping('B');
});

socket.on('bird_response', (data) => {
  removeTyping(data.slot);
  appendReply(data.slot === 'A' ? logA : logB, data.text);
  repliesReceived += 1;

  if (repliesReceived >= 2) {
    if (currentRound >= TOTAL_ROUNDS) {
      guessSection.classList.remove('hidden');
      appendSystem('5 rounds complete. Make your verdict.');
    } else {
      enableInput();
    }
  }
});

// ── guess ─────────────────────────────────────────────────────
document.querySelectorAll('.guess-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const guess = btn.dataset.guess; // 'A' or 'B'
    socket.emit('judge_guess', { room_code: ROOM_CODE, guess });

    // we know the answer via redirect — server handles scoring
    window.location.href = `/reveal/${ROOM_CODE}?guess=${guess}`;
  });
});

// ── sending questions ─────────────────────────────────────────
sendBtn.addEventListener('click', sendQuestion);
questionInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendQuestion();
});

function sendQuestion() {
  const q = questionInput.value.trim();
  if (!q || waitingForReplies) return;
  socket.emit('send_question', { room_code: ROOM_CODE, question: q });
  questionInput.value = '';
}

// ── helpers ───────────────────────────────────────────────────
function enableInput() {
  questionInput.disabled = false;
  sendBtn.disabled = false;
  questionInput.focus();
  waitingForReplies = false;
}

function disableInput() {
  questionInput.disabled = true;
  sendBtn.disabled = true;
  waitingForReplies = true;
}

function setBirdStatus(online) {
  birdStatusDot.className = 'status-dot ' + (online ? 'dot-online' : 'dot-offline');
  birdStatusText.textContent = online ? 'bird connected' : 'waiting for bird…';
}

function appendQuestion(logEl, text) {
  const div = document.createElement('div');
  div.className = 'msg msg-question';
  div.textContent = `🔭 ${text}`;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

function appendReply(logEl, text) {
  const div = document.createElement('div');
  div.className = 'msg msg-reply';
  div.textContent = text;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

function appendSystem(text) {
  [logA, logB].forEach(log => {
    const div = document.createElement('div');
    div.className = 'msg msg-system';
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  });
}

function showTyping(slot) {
  const log = slot === 'A' ? logA : logB;
  const div = document.createElement('div');
  div.className = 'msg msg-typing';
  div.id = `typing-${slot}`;
  div.textContent = '…';
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function removeTyping(slot) {
  const el = document.getElementById(`typing-${slot}`);
  if (el) el.remove();
}
