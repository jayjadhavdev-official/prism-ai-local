document.addEventListener("DOMContentLoaded", () => {
  const chatContainer = document.getElementById("chat-container");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");

  if (!chatContainer || !userInput || !sendBtn) {
    console.error("HTML ID mismatch.");
    return;
  }

  chatContainer.innerHTML = "";

  function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    let innerHTMLString = "";

    if (sender === "user") {
      // Apply Tailwind classes for a right-aligned blue user bubble
      messageDiv.className = "flex justify-end";
      innerHTMLString = `
          <div class="bg-blue-600 p-3 rounded-lg max-w-md break-words">
              ${text}
          </div>
      `;
    } else {
      // Apply Tailwind classes for a left-aligned zinc agent bubble
      messageDiv.classname = "flex justify-start items-start gap-3";
      innerHTMLString = `
        <div class="bg-zinc-900 border border-zinc-800 p-3 rounded-lg max-w-md break-words">
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

    const thinkingBox = appendMessage("agent", "Thinking...");

    try {
      const respons = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) throw new Error("Server error");

      const data = await response.json();
      thkingBox.innerText = data.response;
    } catch (error) {
      thinkingBox.innerText =
        "Error: Could not connect to the local Prism AI Engine.";
      thinkingBox.classList.add("text=red=400");
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});
