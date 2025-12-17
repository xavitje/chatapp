// Typing Indicator Manager
class TypingIndicator {
    constructor(websocket, username, roomSlug) {
        this.ws = websocket;
        this.username = username;
        this.roomSlug = roomSlug;
        this.typingUsers = new Set();
        this.typingTimeout = null;
        this.isTyping = false;
    }

    // Call this when user starts typing
    startTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.sendTypingStatus(true);
        }

        // Reset timeout
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 3000); // Stop after 3 seconds of inactivity
    }

    // Call this when user stops typing
    stopTyping() {
        if (this.isTyping) {
            this.isTyping = false;
            this.sendTypingStatus(false);
        }
        clearTimeout(this.typingTimeout);
    }

    sendTypingStatus(isTyping) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'typing',
                username: this.username,
                isTyping: isTyping
            }));
        }
    }

    // Call this when receiving typing status from server
    handleTypingStatus(username, isTyping) {
        if (username === this.username) return; // Ignore own typing

        if (isTyping) {
            this.typingUsers.add(username);
        } else {
            this.typingUsers.delete(username);
        }

        this.updateTypingDisplay();
    }

    updateTypingDisplay() {
        const container = document.getElementById('typing-indicator');
        if (!container) return;

        if (this.typingUsers.size === 0) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');
        const users = Array.from(this.typingUsers);

        let text = '';
        if (users.length === 1) {
            text = `${users[0]} is aan het typen...`;
        } else if (users.length === 2) {
            text = `${users[0]} en ${users[1]} zijn aan het typen...`;
        } else {
            text = `${users.length} mensen zijn aan het typen...`;
        }

        container.textContent = text;
    }
}

window.TypingIndicator = TypingIndicator;
