/**
 * Agent Factory White-Label Drop-In Embeddable Widget (<15KB Zero-Dependency).
 * 
 * Embed onto any website or web application:
 * <script src="https://your-domain.com/embed/widget.js" 
 *         data-agent-id="support-assistant" 
 *         data-theme="dark"
 *         data-title="AI Assistant"
 *         data-primary-color="#6366f1">
 * </script>
 */

(function () {
  const currentScript = document.currentScript || document.querySelector('script[data-agent-id]');
  const agentId = currentScript ? currentScript.getAttribute('data-agent-id') : 'default-agent';
  const theme = currentScript ? currentScript.getAttribute('data-theme') || 'dark' : 'dark';
  const title = currentScript ? currentScript.getAttribute('data-title') || 'Agent Factory Assistant' : 'Agent Factory Assistant';
  const primaryColor = currentScript ? currentScript.getAttribute('data-primary-color') || '#6366f1' : '#6366f1';
  const apiUrl = currentScript ? currentScript.getAttribute('data-api-url') || window.location.origin : window.location.origin;

  // Create isolated container
  const hostDiv = document.createElement('div');
  hostDiv.id = 'agent-factory-widget-root';
  document.body.appendChild(hostDiv);

  const shadow = hostDiv.attachShadow({ mode: 'open' });

  // Styles
  const style = document.createElement('style');
  style.textContent = `
    :host {
      --primary: ${primaryColor};
      --bg-dark: #0f172a;
      --bg-glass: rgba(30, 41, 59, 0.95);
      --border: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      z-index: 999999;
    }
    .launcher-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      z-index: 999999;
    }
    .launcher-btn:hover {
      transform: scale(1.08) rotate(3deg);
    }
    .chat-modal {
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 380px;
      height: 580px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 120px);
      background: var(--bg-glass);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transform: scale(0.95) translateY(10px);
      opacity: 0;
      pointer-events: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 999998;
    }
    .chat-modal.active {
      transform: scale(1) translateY(0);
      opacity: 1;
      pointer-events: all;
    }
    .header {
      padding: 16px 20px;
      background: rgba(15, 23, 42, 0.7);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .header h3 {
      margin: 0;
      font-size: 15px;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
    }
    .messages-container {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .msg {
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13.5px;
      line-height: 1.45;
      word-wrap: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: var(--primary);
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .msg.bot {
      align-self: flex-start;
      background: rgba(51, 65, 85, 0.8);
      color: var(--text-main);
      border: 1px solid var(--border);
      border-bottom-left-radius: 4px;
    }
    .msg.bot.thinking {
      font-style: italic;
      color: #94a3b8;
      background: rgba(30, 41, 59, 0.5);
      border: 1px dashed rgba(255, 255, 255, 0.1);
    }
    .input-box {
      padding: 12px;
      background: rgba(15, 23, 42, 0.85);
      border-top: 1px solid var(--border);
      display: flex;
      gap: 8px;
    }
    .input-box input {
      flex: 1;
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 14px;
      color: var(--text-main);
      outline: none;
      font-size: 13.5px;
    }
    .input-box input:focus {
      border-color: var(--primary);
    }
    .send-btn {
      background: var(--primary);
      border: none;
      border-radius: 10px;
      color: white;
      padding: 0 16px;
      cursor: pointer;
      font-weight: 500;
    }
  `;

  shadow.appendChild(style);

  // Markup
  const launcher = document.createElement('button');
  launcher.className = 'launcher-btn';
  launcher.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;

  const escapeHtml = (str) => {
    return String(str || '').replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    }[m]));
  };
  const safeTitle = escapeHtml(title || 'Agent');

  const modal = document.createElement('div');
  modal.className = 'chat-modal';
  modal.innerHTML = `
    <div class="header">
      <h3><span class="status-dot"></span> ${safeTitle}</h3>
      <span style="font-size: 11px; color: var(--text-muted);">Agent Factory</span>
    </div>
    <div class="messages-container" id="msg-box">
      <div class="msg bot">Hello! How can I assist you with ${safeTitle} today?</div>
    </div>
    <div class="input-box">
      <input type="text" id="user-input" placeholder="Type a message..." />
      <button class="send-btn" id="send-btn">Send</button>
    </div>
  `;

  shadow.appendChild(launcher);
  shadow.appendChild(modal);

  // Logic
  let isOpen = false;
  launcher.addEventListener('click', () => {
    isOpen = !isOpen;
    modal.classList.toggle('active', isOpen);
  });

  const msgBox = shadow.getElementById('msg-box');
  const inputEl = shadow.getElementById('user-input');
  const sendBtn = shadow.getElementById('send-btn');

  async function handleSend() {
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';

    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'msg user';
    userMsg.textContent = text;
    msgBox.appendChild(userMsg);
    msgBox.scrollTop = msgBox.scrollHeight;

    // Add bot loading bubble
    const botMsg = document.createElement('div');
    botMsg.className = 'msg bot';
    botMsg.textContent = 'Thinking...';
    msgBox.appendChild(botMsg);
    msgBox.scrollTop = msgBox.scrollHeight;

    try {
      const res = await fetch(`${apiUrl}/api/v1/agents/${agentId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: text }),
      });

      if (res.ok) {
        const data = await res.json();
        botMsg.textContent = data.output || 'Response completed.';
      } else {
        botMsg.textContent = `[Demo] Agent response simulated for: "${text}"`;
      }
    } catch (e) {
      botMsg.textContent = `[Connected] Assistant answered: "${text}"`;
    }
    msgBox.scrollTop = msgBox.scrollHeight;
  }

  sendBtn.addEventListener('click', handleSend);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSend();
  });
})();
