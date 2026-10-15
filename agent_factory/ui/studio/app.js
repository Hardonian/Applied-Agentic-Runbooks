(() => {
  'use strict';

  const suites = [
    ['reasoning_frontier', 'Reasoning Frontier'], ['pareto_cascade', 'Pareto Cascade'],
    ['adversarial_security', 'Security & MCPWall'], ['self_healing', 'Self-Healing'],
    ['settler_accounting', 'Settler Accounting'],
  ];
  const state = {
    arenaSocket: null, streamSocket: null, frames: [], filteredFrames: [], ticket: null,
    currentRun: null, pollTimer: null, reconnects: {}, cursors: {},
  };
  const byId = (id) => document.getElementById(id);
  const token = () => localStorage.getItem('agentFactoryToken') || '';
  const headers = () => token() ? { Authorization: `Bearer ${token()}` } : {};

  function addLog(message, tone = '') {
    const line = document.createElement('div'); line.className = tone;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    byId('event-log').prepend(line);
  }

  function renderSuites() {
    suites.forEach(([id, label]) => {
      const row = document.createElement('div'); row.className = 'suite'; row.dataset.suite = id;
      const name = document.createElement('span'); name.textContent = label;
      const track = document.createElement('div'); track.className = 'suite-track'; track.appendChild(document.createElement('i'));
      const status = document.createElement('b'); status.textContent = 'Queued'; row.append(name, track, status);
      byId('suite-list').appendChild(row);
    });
  }

  function updateSuite(id, status, passed) {
    const row = document.querySelector(`[data-suite="${id}"]`); if (!row) return;
    row.classList.toggle('passed', passed === true); row.classList.toggle('failed', passed === false);
    row.querySelector('b').textContent = status;
    row.querySelector('i').classList.toggle('complete', ['Passed', 'Failed'].includes(status));
  }

  function socketUrl(path, topic) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const params = new URLSearchParams();
    if (topic) params.set('topic', topic);
    if (token()) params.set('token', token());
    const cursor = Number(localStorage.getItem(`cursor:${topic || path}`) || 0);
    if (cursor) params.set('cursor', String(cursor));
    return `${protocol}//${location.host}${path}?${params}`;
  }

  function connect(path, topic, handler, key) {
    const socket = new WebSocket(socketUrl(path, topic));
    socket.addEventListener('open', () => { byId('connection-dot').classList.add('online'); byId('connection-label').textContent = 'Streaming online'; state.reconnects[key] = 0; });
    socket.addEventListener('message', (message) => {
      const event = JSON.parse(message.data);
      if (event.sequence) localStorage.setItem(`cursor:${topic || path}`, String(event.sequence));
      handler(event);
    });
    socket.addEventListener('close', () => {
      byId('connection-dot').classList.remove('online'); byId('connection-label').textContent = 'Reconnecting';
      const attempt = (state.reconnects[key] || 0) + 1; state.reconnects[key] = attempt;
      const delay = Math.min(30000, 500 * (2 ** attempt));
      window.setTimeout(() => { state[key] = connect(path, topic, handler, key); }, delay);
    });
    return socket;
  }

  function connectRunTopic(runId) {
    if (state.arenaSocket) state.arenaSocket.close();
    state.arenaSocket = connect('/api/v1/ws/arena', `arena:${runId}`, onArena, 'arenaSocket');
  }

  function onArena(event) {
    const data = event.data || event;
    if (event.type === 'arena.started') { byId('arena-status').textContent = 'Running'; suites.forEach(([id]) => updateSuite(id, 'Queued')); addLog(`Run ${data.run_id} started`); }
    else if (event.type === 'arena.suite.started') { updateSuite(data.suite, 'Running'); addLog(`${data.suite} entered the gauntlet`); }
    else if (event.type === 'arena.suite.completed') { updateSuite(data.result.suite, data.result.passed ? 'Passed' : 'Failed', data.result.passed); addLog(`${data.result.suite}: ${(data.result.pass_rate * 100).toFixed(0)}%`, data.result.passed ? 'success' : 'error'); }
    else if (event.type === 'arena.completed') { renderSummary(data); loadFrames(data.apcap); refreshHistory(); refreshLeaderboard(); }
    else if (event.type === 'arena.failed') { byId('arena-status').textContent = 'Failed'; addLog(data.error, 'error'); }
    else if (event.type === 'arena.cancelled') { byId('arena-status').textContent = 'Cancelled'; addLog('Run cancelled', 'error'); }
    else if (event.type === 'approval.requested') showApproval(data);
  }

  function onStream(event) {
    if (event.type === 'stream.started') byId('token-output').textContent = '';
    if (event.type === 'token.chunk') byId('token-output').textContent += event.token;
    if (event.type === 'approval.requested') showApproval(event.data || event);
  }

  function renderSummary(run) {
    state.currentRun = run.run_id; const metrics = run.metrics;
    byId('arena-status').textContent = run.status; byId('pass-rate').textContent = `${(metrics.pass_rate * 100).toFixed(1)}%`;
    byId('pass-bar').style.width = `${metrics.pass_rate * 100}%`; byId('pareto-score').textContent = metrics.pareto_frontier_score.toFixed(3);
    byId('pareto-dial').style.setProperty('--dial', `${Math.min(100, metrics.pareto_frontier_score * 100) * 3.6}deg`);
    byId('pareto-dial').querySelector('b').textContent = metrics.pareto_frontier_score.toFixed(2);
    byId('p95-latency').textContent = metrics.p95_latency_ms.toFixed(1); byId('token-velocity').textContent = metrics.token_burn_velocity.toFixed(0);
    ['apcap', 'proof', 'manifest'].forEach((kind) => {
      const target = byId(`download-${kind}`); const apiKind = kind === 'proof' ? 'veridag' : kind;
      target.href = `/api/v1/arena/runs/${run.run_id}/artifacts/${apiKind}`; target.classList.remove('disabled');
    });
    addLog(`Merkle root ${run.veridag_proof.final_merkle_root.slice(0, 18)}…`, 'success');
    setRunning(false);
  }

  function setRunning(running) { byId('run-arena').disabled = running; byId('cancel-arena').disabled = !running; }

  async function runArena() {
    setRunning(true); suites.forEach(([id]) => updateSuite(id, 'Queued')); byId('arena-status').textContent = 'Queued';
    try {
      const response = await fetch('/api/v1/arena/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers() }, body: JSON.stringify({ concurrency: 32, trials: Number(byId('run-trials').value), mode: byId('run-mode').value }) });
      if (!response.ok) throw new Error(`Arena returned ${response.status}`);
      const job = await response.json(); state.currentRun = job.run_id; connectRunTopic(job.run_id); addLog(`Queued durable job ${job.run_id}`); pollRun(job.run_id);
    } catch (error) { addLog(error.message, 'error'); byId('arena-status').textContent = 'Error'; setRunning(false); }
  }

  function pollRun(runId) {
    window.clearTimeout(state.pollTimer);
    state.pollTimer = window.setTimeout(async () => {
      const response = await fetch(`/api/v1/arena/runs/${runId}`, { headers: headers() });
      if (!response.ok) return;
      const record = await response.json(); byId('arena-status').textContent = record.status;
      if (record.summary) { renderSummary(record.summary); loadFrames(record.summary.apcap); refreshHistory(); return; }
      if (['failed', 'cancelled'].includes(record.status)) { setRunning(false); addLog(record.error || record.status, 'error'); return; }
      pollRun(runId);
    }, 800);
  }

  async function cancelRun() { if (!state.currentRun) return; await fetch(`/api/v1/arena/runs/${state.currentRun}/cancel`, { method: 'POST', headers: headers() }); addLog('Cancellation requested'); }

  async function refreshLeaderboard() {
    const response = await fetch('/api/v1/arena/leaderboard', { headers: headers() }); if (!response.ok) return;
    const { entries } = await response.json(); const body = byId('leaderboard'); body.replaceChildren();
    entries.forEach((entry) => { const row = document.createElement('tr'); [entry.rank, entry.run_id, `${(entry.pass_rate * 100).toFixed(0)}%`, `${entry.p95_latency_ms.toFixed(1)} ms`, `${entry.merkle_root.slice(0, 10)}…`].forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); }); body.appendChild(row); });
  }

  async function refreshHistory() {
    const status = byId('history-status').value; const query = status ? `?run_status=${encodeURIComponent(status)}` : '';
    const response = await fetch(`/api/v1/arena/runs${query}`, { headers: headers() }); if (!response.ok) return;
    const { entries } = await response.json(); const body = byId('run-history'); body.replaceChildren();
    entries.forEach((entry) => {
      const row = document.createElement('tr'); const checkCell = document.createElement('td'); const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.value = entry.run_id; checkbox.className = 'compare-check'; checkbox.setAttribute('aria-label', `Compare ${entry.run_id}`); checkCell.appendChild(checkbox); row.appendChild(checkCell);
      [entry.run_id, entry.mode, entry.status, entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'].forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); });
      row.addEventListener('dblclick', () => loadHistoricalRun(entry.run_id)); body.appendChild(row);
    });
  }

  async function loadHistoricalRun(runId) { const response = await fetch(`/api/v1/arena/runs/${runId}`, { headers: headers() }); const record = await response.json(); if (record.summary) { renderSummary(record.summary); loadFrames(record.summary.apcap); } }

  async function compareRuns() {
    const ids = [...document.querySelectorAll('.compare-check:checked')].map((item) => item.value);
    if (ids.length < 2) { addLog('Select at least two runs to compare', 'error'); return; }
    const response = await fetch(`/api/v1/arena/compare?ids=${encodeURIComponent(ids.join(','))}`, { headers: headers() }); const { entries } = await response.json(); const chart = byId('comparison-chart'); chart.replaceChildren();
    entries.forEach((entry) => { const group = document.createElement('div'); group.className = 'comparison-row'; const label = document.createElement('b'); label.textContent = entry.run_id; const quality = document.createElement('i'); quality.className = 'comparison-bar'; quality.style.setProperty('--score', `${entry.pass_rate * 100}%`); const detail = document.createElement('span'); detail.textContent = `${(entry.pass_rate * 100).toFixed(0)}% pass · ${entry.p95_latency_ms.toFixed(1)} ms · $${entry.total_cost_usd.toFixed(4)}`; group.append(label, quality, detail); chart.appendChild(group); });
  }

  function loadFrames(apcap) { state.frames = apcap.frames || []; byId('anomaly-count').textContent = `${(apcap.diagnostics || []).length} anomalies`; filterFrames(); }
  function filterFrames() { const type = byId('frame-filter').value; state.filteredFrames = type ? state.frames.filter((frame) => frame.type === type) : [...state.frames]; const scrubber = byId('frame-scrubber'); scrubber.max = Math.max(0, state.filteredFrames.length - 1); scrubber.value = 0; inspectFrame(0); }
  function inspectFrame(index) { const frame = state.filteredFrames[index]; byId('frame-position').textContent = `${frame ? index + 1 : 0} / ${state.filteredFrames.length}`; const inspector = byId('frame-inspector'); if (!frame) { inspector.textContent = 'No capture loaded.'; return; } inspector.textContent = `${frame.id} · ${frame.type.toUpperCase()} · ${frame.src} → ${frame.dst}\n${JSON.stringify(frame.payload, null, 2)}\n${frame.tokens} tokens · ${frame.latency_ms} ms · hash ${frame.hash}`; }
  function moveFrame(delta) { const scrubber = byId('frame-scrubber'); const next = Math.max(0, Math.min(Number(scrubber.max), Number(scrubber.value) + delta)); scrubber.value = next; inspectFrame(next); }

  function showApproval(ticket) { state.ticket = ticket; byId('approval-message').textContent = `${ticket.tool_name || 'Tool operation'} requires a single-use operator decision.`; byId('approval-hash').textContent = ticket.request_hash || ticket.ticket_id; byId('approval-reason').value = ''; byId('approval-modal').showModal(); }
  function resolveApproval(decision) { if (!state.ticket || !state.streamSocket) return; state.streamSocket.send(JSON.stringify({ type: `approval.${decision}`, ticket_id: state.ticket.ticket_id, reason: byId('approval-reason').value })); state.ticket = null; }

  renderSuites(); state.arenaSocket = connect('/api/v1/ws/arena', 'arena', onArena, 'arenaSocket'); state.streamSocket = connect('/api/v1/ws/stream', 'stream', onStream, 'streamSocket');
  byId('run-arena').addEventListener('click', runArena); byId('cancel-arena').addEventListener('click', cancelRun); byId('refresh-board').addEventListener('click', refreshLeaderboard); byId('refresh-history').addEventListener('click', refreshHistory); byId('history-status').addEventListener('change', refreshHistory); byId('compare-runs').addEventListener('click', compareRuns);
  byId('frame-filter').addEventListener('change', filterFrames); byId('frame-scrubber').addEventListener('input', (event) => inspectFrame(Number(event.target.value))); byId('previous-frame').addEventListener('click', () => moveFrame(-1)); byId('next-frame').addEventListener('click', () => moveFrame(1));
  byId('prompt-form').addEventListener('submit', (event) => { event.preventDefault(); if (state.streamSocket.readyState === WebSocket.OPEN) state.streamSocket.send(JSON.stringify({ type: 'stream.prompt', prompt: byId('prompt').value })); });
  byId('approve-operation').addEventListener('click', () => resolveApproval('approve')); byId('deny-operation').addEventListener('click', () => resolveApproval('deny'));
  refreshLeaderboard(); refreshHistory();
})();
