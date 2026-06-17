const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

chatContainer.innerHTML = '';

function appendMessage(sender, text) {
  const messageDiv = document.createElement('div');

  if (sender === 'user') {
    // Apply Tailwind classes for a right-aligned blue user bubble
    messageDiv.className = 'flex justify-end';
    messageDiv.innerHTML = `
        <div class="bg-blue-600 p-3 rounded-lg max-w-md break-words">
            ${text}
        </div>
    `;
  } else {
    // Apply Tailwind classes for a left-aligned zinc agent bubble
    messageDiv.classname = 'flex justify-start items-start gap-3';
    messageDiv.innerHTML = `
      <div class="bg-zinc-900 border border-zinc-800 p-3 rounded-lg max-w-md break-words">
            ${text}
        </div>
    `;
  }

  chatContainer.appendChild(messageDiv);

  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage('user', text);
  userInput.value = '';

  appendMessage('agent', 'Thinking...');
  const bubbles = chatContainer.children;
  const thinkingBubble = bubbles[bubbles, length - 1].querySelector(('div'));

  try {
    const response = await fetc('http://127.0.0.1:5000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: text })
    });

    if (!response.ok) {
      throw new Error('Server error');
    }

    const data = await response.json();

    thinkingBubble.innerText = data.response;
    
  } catch (error) {
    thinkingBubble.innerText = "Error: Could not connect to local Prism AI Engine.";
    thinkingBubble.classList.add('text-red-400');
  }
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendMessage();
  }
});