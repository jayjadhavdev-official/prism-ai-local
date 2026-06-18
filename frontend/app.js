document.addEventListener("DOMContentLoaded", () => {
  const chatContainer = document.getElementById("chat-container");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");

  if (!chatContainer || !userInput || !sendBtn) return;

  chatContainer.innerHTML = "";

  function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    let innerHTMLString = "";

    if (sender === "user") {
      messageDiv.className = "flex justify-end";
      innerHTMLString = `<div class="bg-blue-600 p-3 rounded-lg max-w-xl break-words">${text}</div>`;
    } else {
      messageDiv.className = "flex justify-start items-start gap-3";
      innerHTMLString = `
          <div class="bg-black border border-black p-3 rounded-lg max-w-full break-words prose prose-invert">
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
          "Content-Type": "applications/json",
        },
        body: JSON.stringify({ message: text }),
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
