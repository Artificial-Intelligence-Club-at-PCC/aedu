// — In‑memory & persisted chat memory —
let chatMemory = [];

/**
 * Load saved memory from localStorage into chatMemory.
 */
function loadMemory() {
  try {
    const stored = localStorage.getItem('chatMemory');
    const parsed = JSON.parse(stored);
    chatMemory = Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.warn('⚠️ Failed to parse chatMemory:', e);
    chatMemory = [];
  }
}


/**
 * Persist chatMemory to localStorage.
 */
function saveMemory() {
  localStorage.setItem('chatMemory', JSON.stringify(chatMemory));
}

/**
 * Completely reset conversation memory.
 */
function resetMemory() {
  chatMemory = [];
  localStorage.removeItem('chatMemory');
  console.log('Chat memory reset.');
}

// load any existing memory on startup
loadMemory();

/**
 * Build a context injection string from chatMemory.
 */
function getContextInjection() {
  let injection = '--- Conversation Context Injection ---\n';
  for (const msg of chatMemory) {
    const speaker = msg.role === 'user' ? 'User' : 'Assistant';
    injection += `${speaker}: "${msg.content}"\n`;
  }
  injection += '--- End of Context ---';
  return injection;
}

/**
 * Escape every single backslash in a LaTeX string
 * so that "\" → "\\"
 */
function escapeBackslashes(str) 
{
  if (str.includes('$$')) {
    // Inline LaTeX: escape backslashes with double backslashes
    return str.replace(/\\/g, '\\\\');
  } else if (str.includes('$')) {
    // Centered LaTeX: keep single backslashes
    return str.replace(/\\/g, '\\');
  }
  return str;
}


// — Load API key from config.json (unchanged) —
let API_KEY = null;
fetch('config.json')
  .then(r => r.json())
  .then(cfg => { API_KEY = cfg.API_KEY; })
  .catch(err => {
    console.error('Could not load config.json', err);
    appendMessage('⚠️ Failed to load API key.', 'ai');
  });

// — Track active document for RAG —
let latestDocId = null;

// — DOM refs —
const chatWindow = document.getElementById('chat-window');
const userInput  = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const uploadForm = document.getElementById('upload-form');
const pdfInput   = document.getElementById('pdf-input');
const docStatus  = document.getElementById('doc-status');

/**
 * Our wrapper now includes a {{CONTEXT}} placeholder
 */
const PROMPT_WRAPPER = `
You are an advanced math assistant.

If the question or your response involves mathematics, always include LaTeX formatting.

- Use inline math with dollar signs: $ ... $
- Use display math with double dollars: $$ ... $$
- Do not include explanations without formatting key expressions in LaTeX
- Prefer clean typeset equations instead of plain text math

{{CONTEXT}}

Continue using this context to maintain mathematical precision and rigor...
`;

/**
 * Append a message bubble, plus record it in chatMemory.
 */
function appendMessage(text, sender) {
  // 0) Deal with backslash errors
  text = escapeBackslashes(text);
  
  // 1) UI
  const wrapper = document.createElement('div');
  wrapper.className = `message-wrapper ${sender}`;
  const bubble = document.createElement('div');
  bubble.className = `message ${sender}`;
  bubble.innerHTML = DOMPurify.sanitize(marked.parse(text));
  wrapper.appendChild(bubble);

  if (sender === 'user') {
    const ts = document.createElement('div');
    ts.className = 'timestamp';
    ts.innerText = new Date().toLocaleTimeString();
    wrapper.appendChild(ts);
  }

  if (sender === 'ai') {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.innerText = 'Copy';
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(text)
        .then(() => {
          btn.innerText = 'Copied!';
          setTimeout(() => btn.innerText = 'Copy', 1500);
        })
        .catch(err => console.error('Copy failed', err));
    });
    wrapper.appendChild(btn);
  }

  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  if (window.MathJax?.typesetPromise) {
    MathJax.typesetPromise([bubble]).catch(console.error);
  }

  // 2) Memory
  if (!Array.isArray(chatMemory)) chatMemory = [];
  chatMemory.push({ role: sender, content: text });
  saveMemory();
}

/**
 * Send user prompt to Gemini Flash via public API,
 * injecting full convo context each time.
 */
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;
  appendMessage(text, 'user');
  userInput.value = '';

  // inject full context
  const contextBlock = getContextInjection();
  const wrappedPrompt = PROMPT_WRAPPER.replace(
    '{{CONTEXT}}',
    contextBlock
  ) + `\n\nUser: ${text}`;

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`;
  const body = {
    contents: [{ parts: [{ text: wrappedPrompt }], role: 'user' }]
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const reply = data?.candidates?.[0]?.content?.parts?.[0]?.text
                || '⚠️ No response.';
    appendMessage(reply, 'ai');
  } catch (e) {
    console.error('Fetch error:', e);
    appendMessage('⚠️ Could not fetch AI response.', 'ai');
  }
}

/**
 * Handle PDF upload to your FastAPI backend
 */
uploadForm.addEventListener('submit', async e => {
  e.preventDefault();
  const file = pdfInput.files[0];
  if (!file) {
    appendMessage('⚠️ No file selected.', 'ai');
    return;
  }
  const formData = new FormData();
  formData.append('pdf', file);
  try {
    const res = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    const { doc_id } = await res.json();
    latestDocId = doc_id;
    docStatus.innerText = `📄 Active Document: ${doc_id}`;
    appendMessage(`✅ PDF uploaded. Document ID: ${doc_id}`, 'ai');
  } catch (err) {
    console.error(err);
    appendMessage(`❌ Upload failed: ${err.message}`, 'ai');
  }
});

// — Event listeners —
// Send on Enter, newline on Shift+Enter
userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
sendBtn.addEventListener('click', sendMessage);

// — Initial welcome message —
window.addEventListener('DOMContentLoaded', () => {
  const welcome = `
I'm a **generative AI model** specialized in mathematical conversation, reasoning, and education.

_Think of me as the **future of math education and computation** — ready when you are._
  `;
  appendMessage(welcome, 'ai');
});

window.addEventListener('beforeunload', () => {
  localStorage.removeItem('chatMemory');
});

