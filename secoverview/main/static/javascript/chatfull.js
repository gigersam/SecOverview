document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box-full");
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

        const response = await fetch("", {
            method: "POST",
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken()
            },
            body: new URLSearchParams({ "user_input": userInputValue })
        });

        const data = await response.json();
        const accordionid = makeid(8)
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


// Dropdown Menu JS
function toggleDropdown() {
    document.getElementById("dropdownList").classList.toggle("show");
  }

  function filterFunction() {
    const input = document.getElementById("dropdownSearch");
    const filter = input.value.toUpperCase();
    const div = document.getElementById("dropdownList");
    const items = div.getElementsByTagName("li");

    // Start from index 1 to skip the search input element
    for (let i = 0; i < items.length; i++) {
      const txtValue = items[i].textContent || items[i].innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        items[i].style.display = "";
      } else {
        items[i].style.display = "none";
      }
    }
  }

  function selectItem(element) {
    const button = document.querySelector('.dropdown button');
    button.textContent = element.textContent;
    // Optionally close the dropdown after selection
    toggleDropdown();
  }

  // Close the dropdown if the user clicks outside of it
  window.onclick = function(event) {
    if (!event.target.matches('.dropdown button')) {
      const dropdowns = document.getElementsByClassName("dropdown-content");
      for (let i = 0; i < dropdowns.length; i++) {
        const openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }