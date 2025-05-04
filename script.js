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

const PROMPT_WRAPPER = `
You are an advanced math assistant.

If the question or your response involves mathematics, always include LaTeX formatting.

- Use inline math with dollar signs: $ ... $
- Use display math with double dollars: $$ ... $$
- Do not include explanations without formatting key expressions in LaTeX
- Prefer clean typeset equations instead of plain text math
`;

/**
 * Append a message bubble with optional timestamp (user)
 * and copy button (AI). Renders Markdown → sanitize → LaTeX.
 */
function appendMessage(text, sender) {
  const wrapper = document.createElement('div');
  wrapper.className = `message-wrapper ${sender}`;

  const bubble = document.createElement('div');
  bubble.className = `message ${sender}`;
  const rawHtml = marked.parse(text);
  bubble.innerHTML = DOMPurify.sanitize(rawHtml);
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
}

/**
 * Send user prompt to Gemini Flash via public API
 */
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(text, 'user');
  userInput.value = '';

  // If there's an uploaded doc, you can inject context here later
  const wrappedPrompt = PROMPT_WRAPPER + "\n\nUser: " + text;

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
