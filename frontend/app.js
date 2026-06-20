document.addEventListener("DOMContentLoaded", () => {
  const chatContainer = document.getElementById("chat-container");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");

  // 1. Grab the Toggle UI elements
  const searchToggle = document.getElementById("searchToggle");
  const indicator = searchToggle
    ? searchToggle.querySelector(".id-indicator")
    : null;
  let isSearchEnabled = false;

  if (!chatContainer || !userInput || !sendBtn) return;

  chatContainer.innerHTML = "";

  // 2. Toggle button listener & structural class swapping
  if (searchToggle && indicator) {
    searchToggle.addEventListener("click", () => {
      isSearchEnabled = !isSearchEnabled;

      if (isSearchEnabled) {
        searchToggle.classList.remove("border-zinc-800", "text-zinc-500");
        searchToggle.classList.add("border-blue-500/30", "text-blue-400");
        indicator.classList.remove("bg-zinc-700");
        indicator.classList.add("bg-blue-500", "shadow-[0_0_8px_#3b82f6]");
        searchToggle.childNodes[2].textContent = " Web Search: ON";
      } else {
        searchToggle.classList.remove("border-blue-500/30", "text-blue-400");
        searchToggle.classList.add("border-zinc-800", "text-zinc-500");
        indicator.classList.remove("bg-blue-500", "shadow-[0_0_8px_#3b82f6]");
        indicator.classList.add("bg-zinc-700");
        searchToggle.childNodes[2].textContent = " Web Search: OFF";
      }
    });
  }

  function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    let innerHTMLString = "";

    if (sender === "user") {
      messageDiv.className = "flex justify-end";
      innerHTMLString = `<div class="bg-blue-600 p-3 rounded-lg max-w-xl break-words">${text}</div>`;
    } else {
      messageDiv.className = "flex justify-start items-start gap-3";
      innerHTMLString = `
          <div class="bg-black border border-black p-3 rounded-lg max-w-full break-words prose prose-invert font-mono">
              ${text}
          </div>
      `;
    }

    messageDiv.innerHTML = innerHTMLString;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return messageDiv.querySelector("div");
  }

  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    userInput.value = "";

    const thinkingBox = appendMessage("agent", "");

    try {
      const response = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json", // FIXED: typo fixed from applications/json
        },
        // 3. Sent the switch context flag payload directly to Python
        body: JSON.stringify({
          message: text,
          webSearchActive: isSearchEnabled,
        }),
      });

      if (!response.ok) throw new Error("Server returned error status");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let accumulatedMarkdown = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });

        accumulatedMarkdown += chunkText;
        thinkingBox.innerHTML = marked.parse(accumulatedMarkdown);

        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    } catch (error) {
      console.error("Streaming error:", error);
      thinkingBox.innerText = "Error streaming from local engine.";
      thinkingBox.classList.add("text-red-400");
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});
