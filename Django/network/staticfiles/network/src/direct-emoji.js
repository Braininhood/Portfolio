// Emoji support for posts and comments
document.addEventListener('DOMContentLoaded', function() {
  console.log("Initializing emoji support for posts and comments...");
  
  // Keep track of click-away handler
  let clickAwayHandlerAdded = false;
  
  // Function to add emoji buttons directly to the DOM
  function addEmojiButtonsToForms() {
    if (!ensureEmojiPickerLoaded()) {
      return; // Will try again later
    }
    
    console.log("Running addEmojiButtonsToForms");
    
    // Check for new post form - now looking within the form
    const newPostForm = document.getElementById('new-post-form');
    if (newPostForm) {
      const textarea = newPostForm.querySelector('#post-content');
      if (textarea) {
        const emojiContainer = newPostForm.querySelector('.emoji-button-container');
        if (emojiContainer && !emojiContainer.querySelector('.emoji-picker-container')) {
          addEmojiPickerToContainer(textarea, emojiContainer, true);
        }
      }
    }
    
    // Check for new post form in modal (fallback for older structure)
    const newPostModal = document.getElementById('new-post-modal');
    if (newPostModal && !newPostForm) {
      const textarea = newPostModal.querySelector('#post-content');
      if (textarea) {
        const emojiContainer = newPostModal.querySelector('.emoji-button-container');
        if (emojiContainer && !emojiContainer.querySelector('.emoji-picker-container')) {
          addEmojiPickerToContainer(textarea, emojiContainer, true);
        }
      }
    }
    
    // Check for comment textareas
    document.querySelectorAll('[id^="comment-textarea-"]').forEach(textarea => {
      const formSection = textarea.closest('.mt-3');
      if (formSection) {
        // Get the button container that follows the textarea
        const btnContainer = formSection.querySelector('.emoji-button-container');
        if (btnContainer && !btnContainer.querySelector('.emoji-picker-container')) {
          // Add emoji picker before the first button
          addEmojiPickerToContainer(textarea, btnContainer, false, true);
        }
      }
    });
    
    // Check for reply forms - using a broader selector to capture reply textareas
    document.querySelectorAll('.reply-textarea, [id^="reply-textarea-"]').forEach(textarea => {
      // Find the closest container with emoji-button-container
      const container = textarea.closest('.reply-form-container');
      if (container) {
        const btnContainer = container.querySelector('.emoji-button-container');
        if (btnContainer && !btnContainer.querySelector('.emoji-picker-container')) {
          addEmojiPickerToContainer(textarea, btnContainer, false, true);
        }
      }
    });
    
    // Check for post edit forms - using a broader selector
    document.querySelectorAll('.edit-textarea').forEach(textarea => {
      // Find the closest container with emoji-button-container
      const parentDiv = textarea.nextElementSibling;
      if (parentDiv && parentDiv.querySelector) {
        const btnContainer = parentDiv.querySelector('.emoji-button-container');
        if (btnContainer && !btnContainer.querySelector('.emoji-picker-container')) {
          addEmojiPickerToContainer(textarea, btnContainer, false, true);
        }
      }
    });
    
    // Check for comment edit forms
    document.querySelectorAll('.comment-edit-textarea').forEach(textarea => {
      const form = textarea.closest('.comment-edit-form');
      if (form) {
        const btnContainer = form.querySelector('.emoji-button-container');
        if (btnContainer && !btnContainer.querySelector('.emoji-picker-container')) {
          addEmojiPickerToContainer(textarea, btnContainer, false, true);
        }
      }
    });
    
    // Add global click-away handler (only once)
    if (!clickAwayHandlerAdded) {
      // Add the actual handler
      document.addEventListener('click', function(e) {
        // Close any open emoji pickers when clicking outside
        if (!e.target.closest('.emoji-picker-container') && !e.target.classList.contains('emoji-button')) {
          document.querySelectorAll('emoji-picker').forEach(picker => {
            picker.style.display = 'none';
          });
        }
      });
      
      clickAwayHandlerAdded = true;
    }
  }
  
  // Make addEmojiButtonsToForms available globally
  window.addEmojiButtonsToForms = addEmojiButtonsToForms;
  
  // Ensures emoji-picker-element is loaded
  function ensureEmojiPickerLoaded() {
    if (typeof customElements === 'undefined' || typeof customElements.get !== 'function') {
      console.warn("Custom elements not supported or not ready yet.");
      setTimeout(addEmojiButtonsToForms, 500);
      return false;
    }
    
    if (typeof customElements.get('emoji-picker') === 'undefined') {
      console.warn("Emoji picker custom element not found! Loading fallback...");
      
      // Load emoji picker element dynamically
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/emoji-picker-element@1.16.0/index.js';
      script.type = 'module';
      document.head.appendChild(script);
      
      // Try again after a delay
      setTimeout(addEmojiButtonsToForms, 1000);
      return false;
    }
    return true;
  }
  
  // Helper function to add emoji picker to a container
  function addEmojiPickerToContainer(textarea, container, isModal = false, openUpward = false) {
    // Create a unique ID for this emoji picker to help with debugging
    const uniqueId = Math.random().toString(36).substring(2, 8);
    console.log(`Adding emoji picker ${uniqueId} to container`, container);
    
    // Ensure container has appropriate styles
    if (!container.classList.contains('d-flex')) {
      container.classList.add('d-flex');
    }
    
    // Always make sure we have proper styles for button alignment
    container.style.justifyContent = 'flex-start';
    container.style.alignItems = 'center';
    container.style.gap = '5px';
    container.style.width = '100%';
    
    // Set up different position for modal vs regular form
    if (isModal) {
      // Create emoji container
      const emojiContainer = document.createElement('div');
      emojiContainer.className = 'emoji-picker-container';
      emojiContainer.dataset.pickerId = uniqueId;
      emojiContainer.style.display = 'inline-block';
      emojiContainer.style.marginRight = '10px';
      emojiContainer.style.marginLeft = '0';
      emojiContainer.style.position = 'relative';
      emojiContainer.style.flexShrink = '0';
      
      // Create emoji button
      const emojiButton = document.createElement('button');
      emojiButton.className = 'emoji-button';
      emojiButton.type = 'button';
      emojiButton.setAttribute('aria-label', 'Add emoji');
      emojiButton.innerHTML = '😀';
      emojiButton.style.background = 'none';
      emojiButton.style.border = 'none';
      emojiButton.style.fontSize = '1.5rem';
      emojiButton.style.cursor = 'pointer';
      emojiButton.style.padding = '0 5px';
      emojiContainer.appendChild(emojiButton);
      
      // Create emoji picker
      const emojiPicker = document.createElement('emoji-picker');
      // Add custom settings to avoid database errors
      emojiPicker.setAttribute('data-use-cache', 'false');
      emojiPicker.classList.add('light');
      
      emojiPicker.style.display = 'none';
      emojiPicker.style.position = 'absolute';
      emojiPicker.style.zIndex = '1050'; // Higher than modal backdrop
      emojiPicker.style.bottom = '60px';
      emojiPicker.style.left = '20px';
      emojiContainer.appendChild(emojiPicker);
      
      // Add to DOM at the beginning of the container
      container.insertBefore(emojiContainer, container.firstChild);
    } else {
      // Regular form (not modal)
      // Create emoji container
      const emojiContainer = document.createElement('div');
      emojiContainer.className = 'emoji-picker-container';
      emojiContainer.dataset.pickerId = uniqueId;
      emojiContainer.style.display = 'inline-block';
      emojiContainer.style.marginRight = '10px';
      emojiContainer.style.position = 'relative';
      
      // Create emoji button
      const emojiButton = document.createElement('button');
      emojiButton.className = 'emoji-button';
      emojiButton.type = 'button';
      emojiButton.setAttribute('aria-label', 'Add emoji');
      emojiButton.innerHTML = '😀';
      emojiButton.style.background = 'none';
      emojiButton.style.border = 'none';
      emojiButton.style.fontSize = '1.2rem';
      emojiButton.style.cursor = 'pointer';
      emojiButton.style.padding = '0 5px';
      emojiContainer.appendChild(emojiButton);
      
      // Create emoji picker
      const emojiPicker = document.createElement('emoji-picker');
      // Add custom settings to avoid database errors
      emojiPicker.setAttribute('data-use-cache', 'false');
      emojiPicker.classList.add('light');
      
      emojiPicker.style.display = 'none';
      emojiPicker.style.position = 'absolute';
      emojiPicker.style.zIndex = '1000';
      
      // If openUpward is true, position the picker above the button
      if (openUpward) {
        emojiPicker.style.bottom = '40px';
        emojiPicker.style.left = '0';
      } else {
        // Position below the button
        emojiPicker.style.top = '40px';
        emojiPicker.style.left = '0';
      }
      
      emojiContainer.appendChild(emojiPicker);
      
      // Add to DOM at the beginning of the container
      container.insertBefore(emojiContainer, container.firstChild);
    }
    
    // Find the emoji container we just created
    const emojiContainer = container.querySelector(`.emoji-picker-container[data-picker-id="${uniqueId}"]`);
    const emojiButton = emojiContainer.querySelector('.emoji-button');
    const emojiPicker = emojiContainer.querySelector('emoji-picker');
    
    // Initialize button with toggle functionality
    emojiButton.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log(`Toggling emoji picker ${uniqueId}`);
      
      // Close all other pickers first
      document.querySelectorAll('emoji-picker').forEach(picker => {
        if (picker !== emojiPicker) {
          picker.style.display = 'none';
        }
      });
      
      // Toggle this picker
      emojiPicker.style.display = emojiPicker.style.display === 'none' ? 'block' : 'none';
    });
    
    // Initialize picker - allow multiple emojis
    emojiPicker.addEventListener('emoji-click', function(event) {
      const emoji = event.detail.unicode;
      
      // Insert at cursor position or append
      if (textarea.selectionStart || textarea.selectionStart === 0) {
        const startPos = textarea.selectionStart;
        const endPos = textarea.selectionEnd;
        textarea.value = textarea.value.substring(0, startPos) + 
                        emoji + 
                        textarea.value.substring(endPos);
        
        // Update cursor position
        textarea.selectionStart = textarea.selectionEnd = startPos + emoji.length;
      } else {
        textarea.value += emoji;
      }
      
      // Focus back on textarea
      textarea.focus();
      
      // Don't hide after selection - allow multiple emojis
    });
  }
  
  // Watch for dynamically added forms with MutationObserver
  const observer = new MutationObserver(function(mutations) {
    let shouldAddButtons = false;
    
    mutations.forEach(function(mutation) {
      if (mutation.addedNodes.length) {
        // Check if any of the added nodes are relevant to our forms
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if this is the new post modal
            if (node.id === 'new-post-modal' || node.querySelector('#new-post-modal')) {
              shouldAddButtons = true;
            }
            
            // Check if this contains any textareas or forms
            if (node.querySelector('textarea') || 
                node.querySelector('.comment-textarea') || 
                node.querySelector('[id^="reply-textarea-"]') ||
                node.classList.contains('comment-textarea') ||
                node.id && node.id.startsWith('reply-textarea-')) {
              shouldAddButtons = true;
            }
          }
        });
      }
    });
    
    if (shouldAddButtons) {
      setTimeout(addEmojiButtonsToForms, 100);
    }
  });
  
  // Configure observer to watch the entire document for changes
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['style', 'class']
  });

  // Intercept the original setupNavigation to prevent it from causing errors
  // This is placed at DOMContentLoaded to ensure it runs before the original
  if (typeof window.setupNavigation === 'function') {
    window.originalSetupNavigation = window.setupNavigation;
    window.setupNavigation = function() {
      console.log("Original setupNavigation prevented from running to avoid errors");
      return;
    };
  }
  
  // Override showNewPostForm to add emoji picker to modal
  if (typeof window.showNewPostForm === 'function') {
    const originalShowNewPostForm = window.showNewPostForm;
    window.showNewPostForm = function() {
      // Call original function
      originalShowNewPostForm.apply(this, arguments);
      
      // Wait for modal to be created
      setTimeout(() => {
        // First try the new structure
        const newPostForm = document.getElementById('new-post-form');
        if (newPostForm) {
          const textarea = newPostForm.querySelector('#post-content');
          const emojiContainer = newPostForm.querySelector('.emoji-button-container');
          if (textarea && emojiContainer && !emojiContainer.querySelector('.emoji-picker-container')) {
            addEmojiPickerToContainer(textarea, emojiContainer, true);
            
            // Apply button spacing
            if (typeof window.adjustButtonSpacing === 'function') {
              window.adjustButtonSpacing();
            }
          }
          return;
        }
        
        // Fallback to old structure
        const modal = document.getElementById('new-post-modal');
        if (modal) {
          const textarea = modal.querySelector('#post-content');
          const emojiContainer = modal.querySelector('.emoji-button-container');
          if (textarea && emojiContainer && !emojiContainer.querySelector('.emoji-picker-container')) {
            addEmojiPickerToContainer(textarea, emojiContainer, true);
            
            // Apply button spacing
            if (typeof window.adjustButtonSpacing === 'function') {
              window.adjustButtonSpacing();
            }
          }
        }
      }, 100);
    };
  }
  
  // Wait for everything to be loaded, then add emoji buttons
  setTimeout(addEmojiButtonsToForms, 500);
  
  // Add a recurring check to catch forms that might be added later
  setInterval(addEmojiButtonsToForms, 2000);
}); 