(() => {
  'use strict';

  const suites = [
    ['reasoning_frontier', 'Reasoning Frontier'],
    ['pareto_cascade', 'Pareto Cascade'],
    ['adversarial_security', 'Security & MCPWall'],
    ['self_healing', 'Self-Healing'],
    ['settler_accounting', 'Settler Accounting'],
  ];
  const state = { arenaSocket: null, streamSocket: null, frames: [], ticket: null };
  const byId = (id) => document.getElementById(id);

  function addLog(message, tone = '') {
    const line = document.createElement('div');
    line.className = tone;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    byId('event-log').prepend(line);
  }

  function renderSuites() {
    const list = byId('suite-list');
    suites.forEach(([id, label]) => {
      const row = document.createElement('div');
      row.className = 'suite';
      row.dataset.suite = id;
      const name = document.createElement('span');
      name.textContent = label;
      const track = document.createElement('div');
      track.className = 'suite-track';
      track.appendChild(document.createElement('i'));
      const status = document.createElement('b');
      status.textContent = 'Queued';
      row.append(name, track, status);
      list.appendChild(row);
    });
  }

  function updateSuite(id, status, passed) {
    const row = document.querySelector(`[data-suite="${id}"]`);
    if (!row) return;
    row.classList.toggle('passed', passed === true);
    row.classList.toggle('failed', passed === false);
    row.querySelector('b').textContent = status;
    row.querySelector('i').classList.toggle('complete', status === 'Passed' || status === 'Failed');
  }

  function socketUrl(path) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${location.host}${path}`;
  }

  function connect(path, handler) {
    const socket = new WebSocket(socketUrl(path));
    socket.addEventListener('open', () => {
      byId('connection-dot').classList.add('online');
      byId('connection-label').textContent = 'Streaming online';
    });
    socket.addEventListener('message', (event) => handler(JSON.parse(event.data)));
    socket.addEventListener('close', () => {
      byId('connection-dot').classList.remove('online');
      byId('connection-label').textContent = 'Reconnecting';
      window.setTimeout(() => {
        const replacement = connect(path, handler);
        if (path.endsWith('/arena')) state.arenaSocket = replacement;
        else state.streamSocket = replacement;
      }, 1500);
    });
    return socket;
  }

  function onArena(event) {
    const data = event.data || event;
    if (event.type === 'arena.started') {
      byId('arena-status').textContent = 'Running';
      suites.forEach(([id]) => updateSuite(id, 'Queued'));
      addLog(`Run ${data.run_id} started`);
    } else if (event.type === 'arena.suite.started') {
      updateSuite(data.suite, 'Running');
      addLog(`${data.suite} entered the gauntlet`);
    } else if (event.type === 'arena.suite.completed') {
      updateSuite(data.result.suite, data.result.passed ? 'Passed' : 'Failed', data.result.passed);
      addLog(`${data.result.suite}: ${(data.result.pass_rate * 100).toFixed(0)}%`, data.result.passed ? 'success' : 'error');
    } else if (event.type === 'arena.completed') {
      renderSummary(data);
      loadFrames(data.apcap);
      refreshLeaderboard();
    } else if (event.type === 'approval.requested') {
      showApproval(data);
    }
  }

  function onStream(event) {
    if (event.type === 'stream.started') byId('token-output').textContent = '';
    if (event.type === 'token.chunk') byId('token-output').textContent += event.token;
    if (event.type === 'approval.requested') showApproval(event.data || event);
  }

  function renderSummary(run) {
    const metrics = run.metrics;
    byId('arena-status').textContent = run.status;
    byId('pass-rate').textContent = `${(metrics.pass_rate * 100).toFixed(1)}%`;
    byId('pass-bar').style.width = `${metrics.pass_rate * 100}%`;
    byId('pareto-score').textContent = metrics.pareto_frontier_score.toFixed(3);
    byId('pareto-dial').style.setProperty('--dial', `${Math.min(100, metrics.pareto_frontier_score * 100) * 3.6}deg`);
    byId('pareto-dial').querySelector('b').textContent = metrics.pareto_frontier_score.toFixed(2);
    byId('p95-latency').textContent = metrics.p95_latency_ms.toFixed(1);
    byId('token-velocity').textContent = metrics.token_burn_velocity.toFixed(0);
    addLog(`Merkle root ${run.veridag_proof.final_merkle_root.slice(0, 18)}…`, 'success');
  }

  async function runArena() {
    byId('run-arena').disabled = true;
    try {
      const response = await fetch('/api/v1/arena/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ concurrency: 32 }) });
      if (!response.ok) throw new Error(`Arena returned ${response.status}`);
      const run = await response.json();
      renderSummary(run);
      loadFrames(run.apcap);
      await refreshLeaderboard();
    } catch (error) {
      addLog(error.message, 'error');
      byId('arena-status').textContent = 'Error';
    } finally {
      byId('run-arena').disabled = false;
    }
  }

  async function refreshLeaderboard() {
    const response = await fetch('/api/v1/arena/leaderboard');
    if (!response.ok) return;
    const { entries } = await response.json();
    const body = byId('leaderboard');
    body.replaceChildren();
    entries.forEach((entry) => {
      const row = document.createElement('tr');
      [entry.rank, entry.run_id, `${(entry.pass_rate * 100).toFixed(0)}%`, `${entry.p95_latency_ms.toFixed(1)} ms`, `${entry.merkle_root.slice(0, 10)}…`].forEach((value) => {
        const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell);
      });
      body.appendChild(row);
    });
  }

  function loadFrames(apcap) {
    state.frames = apcap.frames || [];
    const scrubber = byId('frame-scrubber');
    scrubber.max = Math.max(0, state.frames.length - 1);
    scrubber.value = 0;
    byId('anomaly-count').textContent = `${(apcap.diagnostics || []).length} anomalies`;
    inspectFrame(0);
  }

  function inspectFrame(index) {
    const frame = state.frames[index];
    const inspector = byId('frame-inspector');
    if (!frame) { inspector.textContent = 'No capture loaded.'; return; }
    inspector.textContent = `${frame.id} · ${frame.type.toUpperCase()} · ${frame.src} → ${frame.dst}\n${JSON.stringify(frame.payload, null, 2)}\n${frame.tokens} tokens · ${frame.latency_ms} ms · hash ${frame.hash}`;
  }

  function showApproval(ticket) {
    state.ticket = ticket;
    byId('approval-message').textContent = `${ticket.tool_name || 'Tool operation'} requires a single-use operator decision.`;
    byId('approval-hash').textContent = ticket.request_hash || ticket.ticket_id;
    byId('approval-modal').showModal();
  }

  function resolveApproval(decision) {
    if (!state.ticket || !state.streamSocket) return;
    state.streamSocket.send(JSON.stringify({ type: `approval.${decision}`, ticket_id: state.ticket.ticket_id, approver: 'studio-operator' }));
    state.ticket = null;
  }

  renderSuites();
  state.arenaSocket = connect('/api/v1/ws/arena', onArena);
  state.streamSocket = connect('/api/v1/ws/stream', onStream);
  byId('run-arena').addEventListener('click', runArena);
  byId('refresh-board').addEventListener('click', refreshLeaderboard);
  byId('frame-scrubber').addEventListener('input', (event) => inspectFrame(Number(event.target.value)));
  byId('prompt-form').addEventListener('submit', (event) => {
    event.preventDefault();
    if (state.streamSocket.readyState === WebSocket.OPEN) state.streamSocket.send(JSON.stringify({ type: 'stream.prompt', prompt: byId('prompt').value }));
  });
  byId('approve-operation').addEventListener('click', () => resolveApproval('approve'));
  byId('deny-operation').addEventListener('click', () => resolveApproval('deny'));
  refreshLeaderboard();
})();
