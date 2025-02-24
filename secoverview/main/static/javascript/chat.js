document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user_input");
    const sendBtn = document.getElementById("send-btn");

    function getCSRFToken() {
        return document.querySelector("[name=csrfmiddlewaretoken]").value;
    }

    async function sendMessage() {
        let userInputValue = userInput.value.trim();
        if (userInputValue === "") return;

        // Ensure chatBox is found before using it
        if (!chatBox) {
            console.error("Chat box not found!");
            return;
        }

        chatBox.innerHTML += `<p><b>You:</b> ${userInputValue}</p>`;

        const response = await fetch("/chat/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken()
            },
            body: new URLSearchParams({ "user_input": userInputValue })
        });

        const data = await response.json();
        chatBox.innerHTML += `<p><b>${data.response.model}:</b> {'model': '${data.response.model}', 'message': '${data.response.message}', 'tokens_used': ${data.response.token_used}}</p>`;

        userInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
});

function toggleChat() {
    let chatContainer = document.getElementById("chat-container");
    let expandBtn = document.getElementById("expand-btn");

    if (chatContainer.style.display === "none") {
        chatContainer.style.display = "block"; // Show chat box
        expandBtn.style.display = "block"; // Hide button
    } else {
        chatContainer.style.display = "none"; // Hide chat box
        expandBtn.style.display = "block"; // Show button
    }
}

function sendMessage() {
    let userInput = document.getElementById("user_input").value;
    let chatBox = document.getElementById("chat-box");

    if (userInput.trim() === "") return;

    chatBox.innerHTML += `<p><b>You:</b> ${userInput}</p>`;
    chatBox.innerHTML += `<p><b>Ollama:</b> Processing...</p>`; // Placeholder for response

    document.getElementById("user_input").value = "";
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
}