document.addEventListener("DOMContentLoaded", () => {
    const messageInput = document.getElementById("message");
    const wordCountMessage = document.getElementById("wordCountMessage");

    messageInput.addEventListener("input", () => {
        const words = messageInput.value.trim().split(/\s+/).filter(word => word.length > 0);
        if (words.length > 1000) {
            wordCountMessage.textContent = "You can only enter a maximum of 1000 words.";
        } else {
            wordCountMessage.textContent = ""; // Clear the message if within limit
        }
    });
});
