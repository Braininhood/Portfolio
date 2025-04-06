// Simple Emoji Picker Implementation
class SimpleEmojiPicker extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.render();
    this._setupEvents();
  }

  static get observedAttributes() {
    return ['data-use-cache'];
  }

  connectedCallback() {
    // Set some default styles when added to the DOM
    this.style.display = 'none';
    this.classList.add('emoji-picker');
  }

  render() {
    // Common emojis that work well across platforms
    const commonEmojis = [
      '😀', '😁', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😊', 
      '😋', '😎', '😍', '😘', '🥰', '😗', '😙', '😚', '🙂', '🤗',
      '🤔', '🤨', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮',
      '🤐', '😯', '😪', '😫', '🥱', '😴', '😌', '😛', '😜', '😝',
      '🤤', '😒', '😓', '😔', '😕', '🙃', '🤑', '😲', '☹️', '🙁',
      '😖', '😞', '😟', '😤', '😢', '😭', '😦', '😧', '😨', '😩',
      '🤯', '😬', '😰', '😱', '🥵', '🥶', '😳', '🤪', '😵', '🥴',
      '😠', '😡', '🤬', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '😇',
      '🥳', '🥺', '🤠', '🤡', '🤥', '🤫', '🤭', '🧐', '🤓', '😈',
      '👋', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👍',
      '👎', '👊', '✊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝',
      '🙏', '✍️', '💪', '🦾', '🖕', '🦿', '🦵', '🦶', '👂', '🦻',
      '👃', '🧠', '🦷', '🦴', '👀', '👁️', '👅', '👄', '💋', '🩸',
      '❤️', '🧡', '💛', '💚', '💙', '💜', '🤎', '🖤', '🤍', '💔',
      '💯', '💢', '💥', '💫', '💦', '💨', '🕳️', '💣', '💬', '👁️‍🗨️',
      '🗨️', '🗯️', '💭', '💤', '👶', '🧒', '👦', '👧', '🧑', '👱',
    ];

    // Create CSS
    const style = document.createElement('style');
    style.textContent = `
      :host {
        display: block;
        width: 300px;
        height: 300px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        font-family: sans-serif;
        overflow-y: auto;
      }
      .emoji-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
      }
      .emoji {
        cursor: pointer;
        font-size: 24px;
        padding: 5px;
        border-radius: 5px;
        width: 24px;
        height: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: background-color 0.2s;
      }
      .emoji:hover {
        background-color: #f0f0f0;
      }
      .search {
        margin-bottom: 10px;
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 5px;
        box-sizing: border-box;
      }
    `;

    // Create HTML structure
    const search = document.createElement('input');
    search.type = 'text';
    search.placeholder = 'Search emojis';
    search.classList.add('search');

    const emojiGrid = document.createElement('div');
    emojiGrid.classList.add('emoji-grid');

    // Add emojis to the grid
    commonEmojis.forEach(emoji => {
      const emojiElement = document.createElement('div');
      emojiElement.classList.add('emoji');
      emojiElement.textContent = emoji;
      emojiElement.addEventListener('click', () => {
        this.dispatchEvent(new CustomEvent('emoji-click', { 
          detail: { unicode: emoji }
        }));
      });
      emojiGrid.appendChild(emojiElement);
    });

    // Add everything to the shadow DOM
    this.shadowRoot.appendChild(style);
    this.shadowRoot.appendChild(search);
    this.shadowRoot.appendChild(emojiGrid);

    // Set up search functionality
    search.addEventListener('input', (e) => {
      const searchText = e.target.value.toLowerCase();
      // Simple filtering for demo purposes
      Array.from(emojiGrid.children).forEach(emojiElement => {
        if (searchText === '') {
          emojiElement.style.display = 'flex';
          return;
        }
        // This is not a real search, just for demonstration
        // In a real implementation, you'd need emoji descriptions to search properly
        emojiElement.style.display = Math.random() > 0.5 ? 'flex' : 'none';
      });
    });
  }

  _setupEvents() {
    // Add any event handlers needed
    document.addEventListener('click', (e) => {
      // Close picker when clicking outside
      if (!this.contains(e.target) && this.style.display === 'block') {
        this.style.display = 'none';
      }
    });
  }
}

// Register the custom element
customElements.define('emoji-picker', SimpleEmojiPicker);

console.log('Simple emoji picker loaded!'); 