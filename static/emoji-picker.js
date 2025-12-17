// Simple Emoji Picker
class EmojiPicker {
    constructor(inputElement, buttonElement) {
        this.input = inputElement;
        this.button = buttonElement;
        this.isOpen = false;

        // Common emojis
        this.emojis = [
            '😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊',
            '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘',
            '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪',
            '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒',
            '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖',
            '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡',
            '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰',
            '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶',
            '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙',
            '👏', '🙌', '👐', '🤲', '🤝', '🙏', '✍️', '💪',
            '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍',
            '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘',
            '🔥', '✨', '💫', '⭐', '🌟', '💯', '🎉', '🎊'
        ];

        this.createPicker();
        this.attachEvents();
    }

    createPicker() {
        this.picker = document.createElement('div');
        this.picker.className = 'absolute bottom-full mb-2 bg-gray-800 rounded-lg shadow-xl p-3 hidden z-50 max-w-xs';
        this.picker.style.maxHeight = '200px';
        this.picker.style.overflowY = 'auto';

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-8 gap-2';

        this.emojis.forEach(emoji => {
            const btn = document.createElement('button');
            btn.textContent = emoji;
            btn.type = 'button';
            btn.className = 'text-2xl hover:bg-gray-700 rounded p-1 transition-colors';
            btn.onclick = () => this.selectEmoji(emoji);
            grid.appendChild(btn);
        });

        this.picker.appendChild(grid);
        this.button.parentElement.style.position = 'relative';
        this.button.parentElement.appendChild(this.picker);
    }

    attachEvents() {
        this.button.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggle();
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.picker.contains(e.target) && e.target !== this.button) {
                this.close();
            }
        });
    }

    toggle() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.picker.classList.remove('hidden');
        } else {
            this.picker.classList.add('hidden');
        }
    }

    close() {
        this.isOpen = false;
        this.picker.classList.add('hidden');
    }

    selectEmoji(emoji) {
        const start = this.input.selectionStart;
        const end = this.input.selectionEnd;
        const text = this.input.value;

        this.input.value = text.substring(0, start) + emoji + text.substring(end);
        this.input.selectionStart = this.input.selectionEnd = start + emoji.length;
        this.input.focus();
        this.close();
    }
}

window.EmojiPicker = EmojiPicker;
