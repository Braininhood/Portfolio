// Modified navigation setup function that doesn't rely on Django template tags
document.addEventListener('DOMContentLoaded', function() {
  console.log("Initializing custom navigation...");
  
  // First prevent the original setupNavigation from causing errors
  if (window.setupNavigation) {
    console.log("Completely disabling original setupNavigation function");
    window.originalSetupNavigation = window.setupNavigation;
    window.setupNavigation = function() {
      console.log("Original setupNavigation prevented from running");
      return; // Do nothing
    };
  } else {
    // setupNavigation isn't available yet, so we'll override it when it becomes available
    Object.defineProperty(window, 'setupNavigation', {
      configurable: true,
      enumerable: true,
      get: function() { return window._setupNavigation; },
      set: function(val) {
        // Store the original function
        window.originalSetupNavigation = val;
        // Replace with our safe version
        window._setupNavigation = function() {
          console.log("Original setupNavigation prevented from running");
          return; // Do nothing
        };
      }
    });
  }
  
  // Fix the navigation setup with our own implementation
  function fixNavigation() {
    // Handle "All Posts" link
    const allPostsLinks = document.querySelectorAll('a[href="/"]');
    allPostsLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        if (window.location.pathname === '/') {
          e.preventDefault();
          // If the app has React Router functionality
          if (typeof currentView !== 'undefined') {
            currentView = 'all-posts';
            currentPage = 1;
            if (typeof renderApp === 'function') renderApp();
          } else {
            // Fallback
            window.location.href = '/';
          }
        }
      });
    });
    
    // Handle "Following" link if authenticated
    if (typeof window.isAuthenticated !== 'undefined' && window.isAuthenticated) {
      const followingLinks = document.querySelectorAll('a[href="/following"]');
      followingLinks.forEach(link => {
        link.addEventListener('click', function(e) {
          e.preventDefault();
          // If the app has React Router functionality
          if (typeof currentView !== 'undefined') {
            currentView = 'following';
            currentPage = 1;
            if (typeof renderApp === 'function') renderApp();
          } else {
            // Fallback
            window.location.href = '/following';
          }
        });
      });
    }
    
    // Handle profile links
    document.querySelectorAll('a[href^="/profile/"]').forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        const username = this.getAttribute('href').split('/profile/')[1];
        
        // If the app has React Router functionality
        if (typeof currentView !== 'undefined') {
          currentView = 'profile';
          currentProfile = { username };
          currentPage = 1;
          if (typeof renderApp === 'function') renderApp();
        } else {
          // Fallback
          window.location.href = `/profile/${username}`;
        }
      });
    });
  }
  
  // Try to fix the navigation setup
  try {
    fixNavigation();
    console.log("Navigation fixed successfully");
  } catch (error) {
    console.error('Error fixing navigation:', error);
  }
});

// Custom JavaScript enhancements
document.addEventListener('DOMContentLoaded', function() {
  console.log("Loading custom enhancements...");

  // Fix edit functionality to ensure buttons don't freeze
  function fixEditButtons() {
    // Add custom event handlers for edit and cancel buttons
    document.addEventListener('click', function(e) {
      // Edit button handling for posts
      if (e.target.closest('.edit-button')) {
        const editButton = e.target.closest('.edit-button');
        const postId = editButton.dataset.postId;
        const postCard = document.getElementById(`post-${postId}`);
        if (!postCard) return;
        
        const postContent = postCard.querySelector('.post-content');
        if (!postContent) return;
        
        // Store the original content for cancel functionality
        const originalContent = postContent.innerHTML;
        postCard.setAttribute('data-original-content', originalContent);
        
        // Define what happens when cancel is clicked
        const handleCancel = function(evt) {
          evt.preventDefault();
          // Restore the original content
          postContent.innerHTML = postCard.getAttribute('data-original-content');
          
          // Restore the edit button functionality
          editButton.disabled = false;
        };
        
        // Set up our own edit form if needed
        if (!postContent.querySelector('.edit-textarea')) {
          const content = postContent.textContent.trim();
          
          postContent.innerHTML = `
            <textarea class="form-control mb-2 edit-textarea" rows="3">${content}</textarea>
            <div class="d-flex justify-content-end gap-2">
              <button class="btn btn-secondary btn-sm cancel-edit">Cancel</button>
              <button class="btn btn-primary btn-sm save-edit" data-post-id="${postId}">Save</button>
            </div>
          `;
          
          // Add event listener to cancel button
          const cancelButton = postContent.querySelector('.cancel-edit');
          if (cancelButton) {
            cancelButton.addEventListener('click', handleCancel);
          }
          
          // Add event listener to save button
          const saveButton = postContent.querySelector('.save-edit');
          if (saveButton) {
            saveButton.addEventListener('click', function(evt) {
              const newContent = postContent.querySelector('.edit-textarea').value;
              // Call the original saveEditedPost function if it exists
              if (typeof saveEditedPost === 'function') {
                saveEditedPost(postId, newContent);
                // Re-enable the edit button after a short delay to ensure the API call completes
                setTimeout(() => {
                  editButton.disabled = false;
                }, 100);
              } else {
                // Fallback if the original function doesn't exist
                fetch(`/api/posts/${postId}/edit`, {
                  method: 'PUT',
                  headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || ''
                  },
                  body: JSON.stringify({ content: newContent })
                })
                .then(response => {
                  if (!response.ok) throw new Error('Failed to update post');
                  return response.json();
                })
                .then(data => {
                  postContent.innerHTML = newContent;
                  editButton.disabled = false;
                  console.log('Post updated successfully');
                })
                .catch(error => {
                  console.error('Error updating post:', error);
                  handleCancel(evt);
                });
              }
            });
          }
          
          // Focus the textarea
          const textarea = postContent.querySelector('.edit-textarea');
          if (textarea) {
            textarea.focus();
          }
        }
        
        // Disable the edit button to prevent multiple edits
        editButton.disabled = true;
      }
      
      // Edit button handling for comments
      if (e.target.closest('.edit-comment-btn')) {
        const editButton = e.target.closest('.edit-comment-btn');
        const commentId = editButton.dataset.commentId;
        if (!commentId) return;
        
        // Show the comment edit form
        const comment = document.getElementById(`comment-${commentId}`);
        if (!comment) return;
        
        const commentContent = document.getElementById(`comment-content-${commentId}`);
        const editForm = document.getElementById(`comment-edit-form-${commentId}`);
        
        if (commentContent && editForm) {
          // Show edit form, hide content
          commentContent.style.display = 'none';
          editForm.style.display = 'block';
          
          // Focus the textarea
          const editTextarea = document.getElementById(`comment-edit-textarea-${commentId}`);
          if (editTextarea) {
            editTextarea.focus();
          }
          
          // Disable the edit button temporarily
          editButton.disabled = true;
          
          // Add event handler for cancel button if needed
          const cancelButton = editForm.querySelector('.cancel-comment-edit-btn');
          if (cancelButton && !cancelButton.getAttribute('data-event-added')) {
            cancelButton.setAttribute('data-event-added', 'true');
            cancelButton.addEventListener('click', function() {
              // Hide edit form, show content
              commentContent.style.display = 'block';
              editForm.style.display = 'none';
              
              // Re-enable the edit button
              editButton.disabled = false;
            });
          }
          
          // Add event handler for save button if needed
          const saveButton = editForm.querySelector('.save-comment-edit-btn');
          if (saveButton && !saveButton.getAttribute('data-event-added')) {
            saveButton.setAttribute('data-event-added', 'true');
            saveButton.addEventListener('click', function() {
              // Re-enable the edit button after save attempt
              setTimeout(() => {
                editButton.disabled = false;
              }, 100);
            });
          }
        }
      }

      // Reply button handling for all comment levels
      if (e.target.closest('.reply-btn')) {
        const replyButton = e.target.closest('.reply-btn');
        const commentId = replyButton.dataset.commentId;
        if (!commentId) return;
        
        // Show reply form
        const replyFormContainer = document.getElementById(`reply-form-container-${commentId}`);
        if (replyFormContainer) {
          replyFormContainer.style.display = 'block';
          
          // Focus the textarea
          const textarea = document.getElementById(`reply-textarea-${commentId}`);
          if (textarea) {
            textarea.focus();
          }
          
          // Initialize emoji picker if available
          setTimeout(() => {
            if (typeof addEmojiButtonsToForms === 'function') {
              try {
                addEmojiButtonsToForms();
              } catch (error) {
                console.error('Error initializing emoji picker for reply:', error);
              }
            }
          }, 300);
        }
      }
    });
  }

  // Function to set up double-click to edit posts
  function setupDoubleClickToEdit() {
    // Double-click to edit posts
    document.addEventListener('dblclick', function(e) {
      // Check if the clicked element is a post content
      const postContent = e.target.closest('.post-content');
      if (postContent) {
        const postCard = postContent.closest('.post-card');
        if (!postCard) return;

        const postId = postCard.id.split('-')[1];
        if (!postId) return;

        // Check if this post is editable (has an edit button)
        const editButton = postCard.querySelector('.edit-button');
        if (editButton && !editButton.disabled) {
          // Simulate click on the edit button
          editButton.click();
        }
      }
      
      // Check if the clicked element is a comment content
      const commentContent = e.target.closest('.comment-content');
      if (commentContent) {
        const comment = commentContent.closest('.comment');
        if (!comment) return;

        const commentId = comment.id.split('-')[1];
        if (!commentId) return;

        // Check if this comment is editable (has an edit button)
        const editButton = comment.querySelector('.edit-comment-btn');
        if (editButton && !editButton.disabled) {
          // Simulate click on the edit button
          editButton.click();
        }
      }
    });
  }

  // Initialize functionality
  fixEditButtons();
  setupDoubleClickToEdit();
}); 