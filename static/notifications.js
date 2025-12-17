// Notification Manager
class NotificationManager {
    constructor() {
        this.permission = Notification.permission;
        this.isPageVisible = !document.hidden;

        // Request permission on init
        if (this.permission === 'default') {
            this.requestPermission();
        }

        // Track page visibility
        document.addEventListener('visibilitychange', () => {
            this.isPageVisible = !document.hidden;
        });
    }

    async requestPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        }
        return false;
    }

    show(title, options = {}) {
        // Only show notifications if:
        // 1. Permission is granted
        // 2. Page is not visible (user is on another tab/window)
        if (this.permission === 'granted' && !this.isPageVisible) {
            const notification = new Notification(title, {
                icon: '/static/chat-icon.png',
                badge: '/static/chat-icon.png',
                ...options
            });

            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000);

            // Focus window when clicked
            notification.onclick = () => {
                window.focus();
                notification.close();
            };

            return notification;
        }
        return null;
    }
}

// Export for use in other scripts
window.NotificationManager = NotificationManager;
