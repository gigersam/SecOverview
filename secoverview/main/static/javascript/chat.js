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
        userInput.value = "";

        const response = await fetch("/chat/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken()
            },
            body: new URLSearchParams({ "user_input": userInputValue, "context": context })
        });

        const data = await response.json();
        const accordionid = makeid(8)
        let htmlstarttag = 0
        let htmlendtag = -1
        chatBox.innerHTML += `
        <p>
            <b>${data.response.model}:</b> 
            <div class="accordion" id="accordionchatthinking">
                <div class="accordion-item">
                  <h2 class="accordion-header" id="heading${accordionid}">
                          <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${accordionid}" aria-expanded="false" aria-controls="collapse${accordionid}">
                      Thinking
                    </button>
                  </h2>
                  <div id="collapse${accordionid}" class="accordion-collapse collapse" aria-labelledby="heading${accordionid}" data-bs-parent="#accordionchatthinking">
                    <div class="accordion-body">
                      ${data.response.message.substring(data.response.message.indexOf("<think>") + 7, data.response.message.lastIndexOf("</think>"))}
                    </div>
                  </div>
                </div>
            </div>
            <br> 
            ${(data.response.message.split("</think>\n\n")[1]).replaceAll("\n", "<br>").replaceAll(/\*\*(.*?)\*\*/g, '<b>$1</b>').replaceAll(/\`\`\`(.*?)\`\`\`/g, '<pre>$1</pre>')}
        </p>`;

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

function makeid(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
      counter += 1;
    }
    return result;
}