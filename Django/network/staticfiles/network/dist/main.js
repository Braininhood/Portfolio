document.addEventListener('DOMContentLoaded', function() {
  // Get the root element
  let rootElement = document.getElementById('root');
  
  // If root element doesn't exist, create it
  if (!rootElement) {
    console.log('Root element not found, creating one...');
    rootElement = document.createElement('div');
    rootElement.id = 'root';
    
    // Find where to append it (either in a specific container or the body)
    const container = document.querySelector('.container.mt-4');
    if (container) {
      // If we have the main container, insert it there
      container.prepend(rootElement);
    } else {
      // Fallback to body
      document.body.prepend(rootElement);
    }
  }
  
  const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
  
  // Base URL for API calls - ensure we always start from site root
  const baseUrl = window.location.origin;
  
  let currentPage = 1;
  let currentView = 'all-posts'; // 'all-posts', 'following', 'profile'
  let currentProfile = null;
  let postsPerPage = 10; // Show 10 posts per page
  
  // Check if user is authenticated
  const userDataElement = document.getElementById('user-data');
  const isAuthenticated = !!userDataElement;
  const currentUsername = userDataElement ? userDataElement.dataset.username : null;
  
  // Utility function to debounce function calls
  function debounce(func, wait) {
    let timeout;
    return function(...args) {
      const context = this;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }
  
  // Utility function to handle window resize
  function handleWindowResize() {
    adjustUI();
  }
  
  // Utility function to handle orientation change
  function handleOrientationChange() {
    // Wait for orientation change to complete
    setTimeout(adjustUI, 300);
  }
  
  // Adjust UI based on screen size
  function adjustUI() {
    const screenWidth = window.innerWidth;
    
    // Adjust emoji picker positions
    const emojiContainers = document.querySelectorAll('.emoji-button-container');
    emojiContainers.forEach(container => {
      const picker = container.querySelector('.emoji-picker');
      if (picker) {
        if (screenWidth < 768) {
          picker.style.left = '0';
          picker.style.right = 'auto';
        } else {
          picker.style.left = 'auto';
          picker.style.right = '0';
        }
      }
    });
    
    // Adjust modal widths
    const modals = document.querySelectorAll('.modal-dialog');
    modals.forEach(modal => {
      if (screenWidth < 576) {
        modal.style.maxWidth = '95%';
        modal.style.margin = '10px auto';
      } else {
        modal.style.maxWidth = '';
        modal.style.margin = '';
      }
    });
  }
  
  // Check URL parameters for login/register modals and messages
  checkUrlParamsForAuth();
  
  // Add validator functions before the DOMContentLoaded
  // Client-side input validation and sanitization
  function validateInput(text, maxLength = 280) {
    if (!text || !text.trim()) {
      return { isValid: false, error: "Content cannot be empty." };
    }
    
    if (text.length > maxLength) {
      return { isValid: false, error: `Content exceeds ${maxLength} characters.` };
    }
    
    // Simplified validation - only check for obvious malicious content
    const obviousScript = /<script>|<\/script>|javascript:/i;
    if (obviousScript.test(text)) {
      return { isValid: false, error: "Content contains potentially unsafe elements." };
    }
    
    return { isValid: true, sanitized: text.trim() };
  }

  // Sanitize HTML content function
  function sanitizeHTML(html) {
    const element = document.createElement('div');
    element.textContent = html;
    return element.innerHTML;
  }
  
  // Main render function
  function renderApp() {
    // Create the basic app structure with two columns
    rootElement.innerHTML = `
      <div class="network-layout">
        <!-- Left Sidebar with User Information -->
        <div class="left-sidebar">
          ${isAuthenticated ? renderUserContainer() : renderLoginPrompt()}
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
          <div id="alert-container"></div>
          <div id="view-container">
            ${currentView === 'profile' ? renderProfileHeader() : renderViewHeader()}
            <div id="posts-container"></div>
            <div id="pagination" class="pagination-container"></div>
          </div>
        </div>
      </div>
    `;
    
    // Load the posts for the current view
    loadPosts();
    
    // Add event listeners after rendering
    if (isAuthenticated) {
      // New Post button in the sidebar
      const newPostBtn = document.getElementById('new-post-btn');
      if (newPostBtn) {
        newPostBtn.addEventListener('click', showNewPostForm);
      }
      
      // Edit Profile button in the sidebar
      const editProfileBtn = document.getElementById('edit-profile-btn');
      if (editProfileBtn) {
        editProfileBtn.addEventListener('click', showEditProfileForm);
      }
    } else {
      // Login and Register buttons in the sidebar for non-authenticated users
      const loginBtn = document.getElementById('login-btn');
      if (loginBtn) {
        loginBtn.addEventListener('click', showLoginModal);
      }
      
      const registerBtn = document.getElementById('register-btn');
      if (registerBtn) {
        registerBtn.addEventListener('click', showRegisterModal);
      }
    }
  }
  
  // Render user container for the sidebar
  function renderUserContainer() {
    // Get user initials for avatar fallback
    const userInitials = currentUsername ? currentUsername.substring(0, 2).toUpperCase() : 'UN';
    
    return `
      <div class="user-container">
        <div class="user-profile">
          <div class="user-avatar">
            <img src="${window.userAvatar || '/static/network/images/default-avatar.svg'}" 
                 alt="${currentUsername}" 
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" 
                 class="avatar-img">
            <div class="avatar-initials" style="display:none;">${userInitials}</div>
          </div>
          <div class="user-name">${currentUsername}</div>
          <div class="user-username">@${currentUsername}</div>
          
          <div class="user-stats">
            <div class="stat-item">
              <div class="stat-count" id="posts-count">-</div>
              <div class="stat-label">Posts</div>
            </div>
            <div class="stat-item">
              <div class="stat-count" id="followers-count">-</div>
              <div class="stat-label">Followers</div>
            </div>
            <div class="stat-item">
              <div class="stat-count" id="following-count">-</div>
              <div class="stat-label">Following</div>
            </div>
          </div>
        </div>
        
        <div class="sidebar-links mt-3 d-grid gap-2">
          <a href="/profile/${currentUsername}" class="btn btn-outline-primary profile-link">
            <i class="fas fa-user-circle me-2"></i>My Posts
          </a>
          <a href="/following" class="btn btn-outline-primary following-link">
            <i class="fas fa-users me-2"></i>Following
          </a>
          <button id="new-post-btn" class="btn btn-primary new-post-btn">
            <i class="fas fa-plus me-2"></i>New Post
          </button>
          <button id="edit-profile-btn" class="btn btn-outline-secondary edit-profile-link">
            <i class="fas fa-edit me-2"></i>Edit Profile
          </button>
        </div>
      </div>
    `;
  }
  
  // Render login prompt for non-authenticated users
  function renderLoginPrompt() {
    return `
      <div class="user-container">
        <h4 class="text-center mb-4">Welcome to Threads</h4>
        <p class="text-center">Sign in to post and interact with other users.</p>
        <div class="d-grid gap-2">
          <button id="login-btn" class="btn btn-primary">Log In</button>
          <button id="register-btn" class="btn btn-outline-secondary">Register</button>
        </div>
      </div>
    `;
  }
  
  // Show new post form as a modal
  function showNewPostForm() {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
    
    // Create modal HTML
    const modalHTML = `
      <div class="modal fade show" style="display: block;">
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Create New Post</h5>
              <button type="button" class="btn-close" id="close-modal"></button>
            </div>
            <div class="modal-body">
              <form id="new-post-form" enctype="multipart/form-data">
                <div class="form-group">
                  <textarea class="form-control mb-2" id="post-content" name="content" rows="5" placeholder="What's on your mind?"></textarea>
                  <small class="text-muted" id="character-count">0/280</small>
                </div>
                <div class="form-group mt-3">
                  <div class="d-flex align-items-center">
                    <label for="post-image" class="form-label mb-0 me-2">Add Image:</label>
                    <div class="input-group">
                      <input type="file" class="form-control" id="post-image" name="image" accept="image/png, image/jpeg, image/jpg">
                      <button class="btn btn-outline-secondary" type="button" id="clear-image">Clear</button>
                    </div>
                  </div>
                  <div class="image-preview-container mt-2" id="image-preview-container" style="display: none;">
                    <div class="position-relative">
                      <img id="image-preview" class="img-fluid rounded" style="max-height: 200px;" alt="Preview">
                      <button type="button" class="btn-close position-absolute top-0 end-0 bg-light rounded-circle m-1" id="remove-preview"></button>
                    </div>
                  </div>
                  <small class="text-muted d-block mt-1">Supported formats: PNG, JPG (max 5MB)</small>
                </div>
                
                <!-- Buttons in form instead of modal footer -->
                <div class="d-flex justify-content-start align-items-center gap-2 mt-3">
                  <div class="emoji-button-container"></div>
                  <button type="button" class="btn btn-secondary" id="cancel-post">Cancel</button>
                  <button type="button" class="btn btn-primary" id="submit-post">Post</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Add modal to DOM
    const modalContainer = document.createElement('div');
    modalContainer.id = 'new-post-modal';
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Add event listeners
    const postTextarea = document.getElementById('post-content');
    const characterCount = document.getElementById('character-count');
    const submitButton = document.getElementById('submit-post');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-post');
    const postImageInput = document.getElementById('post-image');
    const clearImageBtn = document.getElementById('clear-image');
    const removePreviewBtn = document.getElementById('remove-preview');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    
    // Character count
    postTextarea.addEventListener('input', function() {
      const length = this.value.length;
      characterCount.textContent = `${length}/280`;
      
      if (length > 280) {
        characterCount.classList.add('text-danger');
        submitButton.disabled = true;
      } else {
        characterCount.classList.remove('text-danger');
        submitButton.disabled = false;
      }
    });
    
    // Image preview
    postImageInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        const file = this.files[0];
        
        // Check file type
        const fileType = file.type;
        if (fileType !== 'image/png' && fileType !== 'image/jpeg' && fileType !== 'image/jpg') {
          showAlert('Error: Only PNG and JPG images are allowed.', 'danger');
          this.value = ''; // Clear the input
          imagePreviewContainer.style.display = 'none';
          return;
        }
        
        // Check file size (5MB max)
        const maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (file.size > maxSize) {
          showAlert('Error: Image size should be less than 5MB.', 'danger');
          this.value = ''; // Clear the input
          imagePreviewContainer.style.display = 'none';
          return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
          imagePreview.src = e.target.result;
          imagePreviewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
    
    // Clear image input
    clearImageBtn.addEventListener('click', function() {
      postImageInput.value = '';
      imagePreviewContainer.style.display = 'none';
    });
    
    // Remove preview
    removePreviewBtn.addEventListener('click', function() {
      postImageInput.value = '';
      imagePreviewContainer.style.display = 'none';
    });
    
    // Close modal function
    const closeModal = () => {
      document.body.removeChild(modalContainer);
      document.body.removeChild(backdrop);
    };
    
    // Close buttons
    closeModalBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    
    // Submit post
    submitButton.addEventListener('click', function() {
      createPost();
      closeModal();
    });
    
    // Focus textarea
    postTextarea.focus();
  }
  
  // Show edit profile form as a modal
  function showEditProfileForm() {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
    
    // Create modal HTML with enhanced styling
    const modalHTML = `
      <div class="modal fade show" style="display: block;">
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit Profile</h5>
              <button type="button" class="btn-close" id="close-modal"></button>
            </div>
            <div class="modal-body">
              <form id="profile-form" enctype="multipart/form-data">
                <div class="text-center mb-4">
                  <div class="avatar-container position-relative d-inline-block mb-3">
                    <img id="avatar-preview" src="${window.userAvatar || '/static/network/images/default-avatar.svg'}" 
                      alt="${currentUsername}" 
                      class="rounded-circle" style="width: 150px; height: 150px; object-fit: cover; border: 3px solid #e5e5e5;">
                    <div class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center rounded-circle" 
                         style="background-color: rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.3s; cursor: pointer;">
                      <span class="text-white"><i class="fas fa-camera fa-2x"></i></span>
                    </div>
                  </div>
                  <input type="file" id="avatar-upload" name="avatar" accept="image/png, image/jpeg, image/jpg" class="d-none">
                  <button type="button" id="avatar-upload-btn" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-camera me-1"></i> Change Profile Picture
                  </button>
                  <button type="button" id="remove-avatar-btn" class="btn btn-outline-danger btn-sm ms-2" style="${!window.userAvatar || window.userAvatar.includes('default-avatar') ? 'display: none;' : ''}">
                    <i class="fas fa-times me-1"></i> Remove
                  </button>
                  <div class="text-muted small mt-1">Supported formats: PNG, JPG (max 5MB)</div>
                </div>

                <div class="mb-3">
                  <label for="username" class="form-label">Username</label>
                  <input type="text" class="form-control" id="username" value="${currentUsername}" disabled>
                  <div class="form-text text-muted">Username cannot be changed</div>
                </div>

                <div class="mb-3">
                  <label for="bio" class="form-label">Bio <span class="text-muted small" id="bio-count">0/500</span></label>
                  <textarea class="form-control" id="bio" name="bio" rows="4" placeholder="Tell us about yourself" maxlength="500"></textarea>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" id="cancel-edit">Cancel</button>
              <button type="button" class="btn btn-primary" id="save-profile">Save Changes</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Add modal to DOM
    const modalContainer = document.createElement('div');
    modalContainer.id = 'edit-profile-modal';
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Load current user bio
    fetch(`/api/users/${currentUsername}`)
      .then(response => response.json())
      .then(data => {
        if (data && data.bio) {
          const bioElement = document.getElementById('bio');
          bioElement.value = data.bio;
          
          // Update character count
          const bioCount = document.getElementById('bio-count');
          bioCount.textContent = `${bioElement.value.length}/500`;
        }
      })
      .catch(error => {
        console.error('Error loading user data:', error);
      });
    
    // Add event listeners
    const avatarUpload = document.getElementById('avatar-upload');
    const avatarPreview = document.getElementById('avatar-preview');
    const avatarUploadBtn = document.getElementById('avatar-upload-btn');
    const removeAvatarBtn = document.getElementById('remove-avatar-btn');
    const avatarContainer = document.querySelector('.avatar-container');
    const bioTextarea = document.getElementById('bio');
    const bioCount = document.getElementById('bio-count');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-edit');
    const saveBtn = document.getElementById('save-profile');
    
    // Bio character count update
    bioTextarea.addEventListener('input', function() {
      bioCount.textContent = `${this.value.length}/500`;
    });
    
    // Make avatar container hover effect work
    if (avatarContainer) {
      const overlay = avatarContainer.querySelector('.position-absolute');
      avatarContainer.addEventListener('mouseover', function() {
        overlay.style.opacity = '1';
      });
      
      avatarContainer.addEventListener('mouseout', function() {
        overlay.style.opacity = '0';
      });
      
      avatarContainer.addEventListener('click', function() {
        avatarUpload.click();
      });
    }
    
    // Close modal function
    const closeModal = () => {
      document.body.removeChild(modalContainer);
      document.body.removeChild(backdrop);
    };
    
    // Close button event
    closeModalBtn.addEventListener('click', closeModal);
    
    // Cancel button event
    cancelBtn.addEventListener('click', closeModal);
    
    // Escape key closes modal
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        closeModal();
      }
    });
    
    // Trigger file upload when button is clicked
    avatarUploadBtn.addEventListener('click', function() {
      avatarUpload.click();
    });
    
    // Remove avatar
    if (removeAvatarBtn) {
      removeAvatarBtn.addEventListener('click', function() {
        avatarPreview.src = '/static/network/images/default-avatar.svg';
        avatarUpload.value = ''; // Clear the file input
        // Set a flag to indicate the avatar should be removed
        avatarPreview.dataset.removeAvatar = 'true';
        removeAvatarBtn.style.display = 'none';
      });
    }
    
    // Preview the uploaded image
    avatarUpload.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        const file = this.files[0];
        
        // Check file type
        const fileType = file.type;
        if (fileType !== 'image/png' && fileType !== 'image/jpeg' && fileType !== 'image/jpg') {
          showAlert('Error: Only PNG and JPG images are allowed.', 'danger');
          this.value = ''; // Clear the input
          return;
        }
        
        // Check file size (5MB max)
        const maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (file.size > maxSize) {
          showAlert('Error: Image size should be less than 5MB.', 'danger');
          this.value = ''; // Clear the input
          return;
        }
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
          avatarPreview.src = e.target.result;
          // Remove the flag if set previously
          delete avatarPreview.dataset.removeAvatar;
          // Show the remove button
          removeAvatarBtn.style.display = 'inline-block';
        }
        
        reader.readAsDataURL(file);
      }
    });
    
    // Handle form submission
    saveBtn.addEventListener('click', function() {
      // Show loading state
      const originalBtnText = saveBtn.innerHTML;
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
      
      const formData = new FormData();
      
      // Add bio to form data
      const bio = document.getElementById('bio').value;
      formData.append('bio', bio);
      
      // Add avatar to form data if a file was selected
      if (avatarUpload.files.length > 0) {
        formData.append('avatar', avatarUpload.files[0]);
      } else if (avatarPreview.dataset.removeAvatar === 'true') {
        // If the user clicked the remove button
        formData.append('remove_avatar', 'true');
      }
      
      // Submit the form
      fetch('/api/profile/update', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => {
        // Parse the JSON first
        return response.json().then(data => {
          // Add the status to the data for error handling
          return { ...data, ok: response.ok, status: response.status };
        });
      })
      .then(data => {
        // Reset button state
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalBtnText;
        
        if (!data.ok) {
          // Show error message from the server
          showAlert(data.error || 'Error updating profile. Please try again.', 'danger');
          return;
        }
        
        // Show success message
        showAlert('Profile updated successfully!', 'success');
        
        // Update avatar in sidebar if provided
        if (data.avatar_url) {
          window.userAvatar = data.avatar_url;
          const avatarImg = document.querySelector('.user-avatar img');
          if (avatarImg) {
            avatarImg.src = data.avatar_url;
          }
        } else if (avatarPreview.dataset.removeAvatar === 'true') {
          // If avatar was removed
          window.userAvatar = '/static/network/images/default-avatar.svg';
          const avatarImg = document.querySelector('.user-avatar img');
          if (avatarImg) {
            avatarImg.src = '/static/network/images/default-avatar.svg';
          }
        }
        
        // Close the modal
        closeModal();
        
        // Reload the page if we're viewing the profile
        if (currentView === 'profile' && currentProfile && currentProfile.username === currentUsername) {
          setTimeout(() => {
            loadPosts();
          }, 1000);
        }
      })
      .catch(error => {
        // Reset button state
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalBtnText;
        
        // Show error message
        showAlert('Error updating profile. Please try again.', 'danger');
        console.error('Error:', error);
      });
    });
  }
  
  // View header based on current view
  function renderViewHeader() {
    if (currentView === 'all-posts') {
      return '<h2 class="mb-4">All Posts</h2>';
    } else if (currentView === 'following') {
      return '<h2 class="mb-4">Posts from Users You Follow</h2>';
    }
    return '<h2 class="mb-4">Posts</h2>'; // Default fallback
  }
  
  // Render profile header for the current profile
  function renderProfileHeader() {
    if (!currentProfile) return '';
    
    const isOwnProfile = currentProfile.username === currentUsername;
    const followButton = !isOwnProfile
      ? `<button id="follow-button" class="btn ${currentProfile.is_following ? 'btn-outline-primary' : 'btn-primary'} follow-button">
          ${currentProfile.is_following ? 'Unfollow' : 'Follow'}
        </button>`
      : `<button id="profile-edit-button" class="btn btn-outline-secondary edit-profile-btn">
          <i class="fas fa-edit me-2"></i>Edit Profile
        </button>`;
    
    return `
      <div class="profile-header mb-4">
        <div class="card">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <div class="profile-avatar me-3">
                <img src="${currentProfile.avatar || '/static/network/images/default-avatar.svg'}" 
                     alt="${currentProfile.username}" 
                     class="rounded-circle" 
                     width="100" height="100"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" 
                     class="avatar-img">
                <div class="avatar-initials" style="display:none;">
                  ${currentProfile.username ? currentProfile.username.substring(0, 2).toUpperCase() : 'UN'}
                </div>
              </div>
              <div>
                <h1 class="profile-username">${currentProfile.username}</h1>
                <div class="profile-stats d-flex gap-4">
                  <div><strong>${currentProfile.posts_count || 0}</strong> ${currentProfile.posts_count === 1 ? 'post' : 'posts'}</div>
                  <div><strong>${currentProfile.followers_count || 0}</strong> ${currentProfile.followers_count === 1 ? 'follower' : 'followers'}</div>
                  <div><strong>${currentProfile.following_count || 0}</strong> following</div>
                </div>
                ${currentProfile.bio ? `<div class="profile-bio mt-2">${currentProfile.bio}</div>` : ''}
                <div class="profile-actions">
                  ${followButton}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  // Load posts based on the current view
  function loadPosts() {
    let url;
    
    try {
      if (currentView === 'all-posts') {
        url = `${baseUrl}/api/posts?page=${currentPage}&per_page=${postsPerPage}`;
      } else if (currentView === 'following') {
        url = `${baseUrl}/api/posts/following?page=${currentPage}&per_page=${postsPerPage}`;
      } else if (currentView === 'profile') {
        // Ensure we have a username to load profile
        if (!currentProfile || !currentProfile.username) {
          console.error('No username provided for profile view');
          showAlert('Error: No username provided for profile view', 'danger');
          currentView = 'all-posts';
          url = `${baseUrl}/api/posts?page=${currentPage}&per_page=${postsPerPage}`;
        } else {
          url = `${baseUrl}/api/users/${currentProfile.username}?page=${currentPage}&per_page=${postsPerPage}`;
        }
      } else {
        // Default to all posts if view type is unknown
        url = `${baseUrl}/api/posts?page=${currentPage}&per_page=${postsPerPage}`;
        currentView = 'all-posts';
      }
      
      // Add timestamp to prevent caching issues
      const timestamp = new Date().getTime();
      url = `${url}${url.includes('?') ? '&' : '?'}_=${timestamp}`;
      
      // Show loading state
      const postsContainer = document.getElementById('posts-container');
      if (postsContainer) {
        postsContainer.innerHTML = '<div class="text-center my-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading posts...</p></div>';
      }
      
      console.log(`Attempting to fetch posts from: ${url}`);
      
      // For debugging - try using XMLHttpRequest instead of fetch
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.setRequestHeader('Accept', 'application/json');
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      xhr.withCredentials = true;
      
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            console.log('Successfully fetched posts:', data);
            
            if (currentView === 'profile') {
              // Update profile data
              currentProfile = {
                username: data.username,
                followers_count: data.followers_count || 0,
                following_count: data.following_count || 0,
                posts_count: data.posts_count || 0,
                is_following: data.is_following || false,
                avatar: data.avatar || null,
                bio: data.bio || '',
                is_self: data.is_self || (currentUsername && data.username === currentUsername)
              };
              
              // Render updated profile header
              const viewContainer = document.querySelector('#view-container');
              if (viewContainer) {
                viewContainer.innerHTML = 
                  renderProfileHeader() + 
                  '<h3 class="mb-3">Posts</h3>' +
                  '<div id="posts-container"></div>' +
                  '<div id="pagination" class="pagination-container"></div>';
                
                // Add event listeners for profile actions
                const followButton = document.getElementById('follow-button');
                if (followButton) {
                  followButton.addEventListener('click', toggleFollow);
                }
                
                // Add edit profile button event listener
                const profileEditButton = document.getElementById('profile-edit-button');
                if (profileEditButton) {
                  profileEditButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    showEditProfileForm();
                  });
                }
              }
              
              // Render posts
              renderPosts(data.posts || [], data.page || {current: 1, total_pages: 1});
            } else {
              renderPosts(data.posts || [], data.page || {current: 1, total_pages: 1});
            }
            
            // Update user stats in sidebar if authenticated
            if (isAuthenticated) {
              // Try to update user stats if available
              updateUserStats(data, currentView, currentProfile);
            }
          } catch (e) {
            console.error('Error parsing JSON response:', e);
            showError(postsContainer, 'Invalid response format from server');
          }
        } else {
          console.error('Server returned error:', xhr.status, xhr.statusText, xhr.responseText);
          showError(postsContainer, `Server returned ${xhr.status}: ${xhr.statusText}`);
        }
      };
      
      xhr.onerror = function() {
        console.error('Network error occurred');
        showError(postsContainer, 'Network connection error. Please check your internet connection.');
      };
      
      xhr.send();

      function showError(container, message) {
        if (!container) return;
        
        container.innerHTML = `
          <div class="alert alert-danger text-center my-5" role="alert">
            <h5>Error Loading Posts</h5>
            <p>${message}</p>
            <div class="mt-3">
              <button class="btn btn-outline-danger me-2" onclick="location.reload()">Refresh Page</button>
              <button class="btn btn-primary" onclick="window.loadPosts()">Try Again</button>
            </div>
            <div class="mt-3 text-start bg-light p-3 rounded small">
              <p class="mb-1">Technical details:</p>
              <p class="mt-2 mb-1">Current view: ${currentView}</p>
              <p class="mb-1">Current page: ${currentPage}</p>
              <p class="mb-1">URL attempted: ${url}</p>
            </div>
          </div>
        `;
        
        // Also show alert
        showAlert('Failed to load posts. Please refresh the page or try again.', 'danger');
      }
    } catch (error) {
      // Handle any synchronous errors in the try block
      console.error('Error in loadPosts function:', error);
      showAlert('An unexpected error occurred. Please refresh the page.', 'danger');
    }
  }
  
  // Function to update user stats
  function updateUserStats(data, view, profile) {
    try {
      const postsCountEl = document.getElementById('posts-count');
      const followersCountEl = document.getElementById('followers-count');
      const followingCountEl = document.getElementById('following-count');
      
      // If we have the user profile data
      if (view === 'profile' && profile && profile.username === currentUsername) {
        if (postsCountEl) postsCountEl.textContent = data.posts_count || '-';
        if (followersCountEl) followersCountEl.textContent = data.followers_count || '-';
        if (followingCountEl) followingCountEl.textContent = data.following_count || '-';
      } else {
        // Fetch user stats if we're not on profile page
        fetch(`${baseUrl}/api/users/${currentUsername}/stats`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          credentials: 'same-origin'
        })
          .then(response => {
            if (!response.ok) throw new Error('Failed to load user stats');
            return response.json();
          })
          .then(stats => {
            if (postsCountEl) postsCountEl.textContent = stats.posts_count || '-';
            if (followersCountEl) followersCountEl.textContent = stats.followers_count || '-';
            if (followingCountEl) followingCountEl.textContent = stats.following_count || '-';
          })
          .catch(error => {
            console.error('Error loading user stats:', error);
            // Silently fail - stats aren't critical
          });
      }
    } catch (error) {
      console.error('Error updating user stats:', error);
      // Silently fail - stats aren't critical
    }
  }
  
  // Render pagination controls - enhanced version
  function renderPagination(pageInfo) {
    const paginationContainer = document.getElementById('pagination');
    
    if (!pageInfo || pageInfo.total_pages <= 1) {
      paginationContainer.innerHTML = '';
      return;
    }
    
    paginationContainer.innerHTML = `
      <button id="prev-page" class="pagination-button" ${!pageInfo.has_previous ? 'disabled' : ''}>
        <i class="fas fa-chevron-left"></i> Previous
      </button>
      <div class="pagination-info">
        Page ${pageInfo.current} of ${pageInfo.total_pages}
      </div>
      <button id="next-page" class="pagination-button" ${!pageInfo.has_next ? 'disabled' : ''}>
        Next <i class="fas fa-chevron-right"></i>
      </button>
    `;
    
    // Add event listeners for pagination
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    
    if (prevPageButton && pageInfo.has_previous) {
      prevPageButton.addEventListener('click', function() {
        currentPage--;
        // Smooth scroll to top
        window.scrollTo({top: 0, behavior: 'smooth'});
        loadPosts();
      });
    }
    
    if (nextPageButton && pageInfo.has_next) {
      nextPageButton.addEventListener('click', function() {
        currentPage++;
        // Smooth scroll to top
        window.scrollTo({top: 0, behavior: 'smooth'});
        loadPosts();
      });
    }
  }
  
  // Render list of posts
  function renderPosts(posts, pageInfo) {
    const postsContainer = document.getElementById('posts-container');
    const paginationContainer = document.getElementById('pagination');
    
    if (!posts || posts.length === 0) {
      postsContainer.innerHTML = '<div class="text-center my-5">No posts to show.</div>';
      paginationContainer.innerHTML = '';
      return;
    }
    
    // Render posts
    postsContainer.innerHTML = posts.map(post => {
      // Check if the post is by the current user
      const isOwnPost = post.is_owner || post.user === currentUsername;
      
      const likeButton = isAuthenticated
        ? `<button class="like-button ${post.liked_by_user ? 'active' : ''}" data-post-id="${post.id}">
            <i class="fa${post.liked_by_user ? 's' : 'r'} fa-heart"></i> ${post.likes_count}
          </button>`
        : `<span class="like-count"><i class="far fa-heart"></i> ${post.likes_count}</span>`;
      
      // Show edit and delete buttons only if the user is the post owner
      const editButton = isOwnPost
        ? `<button class="edit-button ms-3" data-post-id="${post.id}">
            <i class="fas fa-edit"></i> Edit
          </button>`
        : '';
        
      const deleteButton = isOwnPost
        ? `<button class="delete-button ms-3 text-danger" data-post-id="${post.id}">
            <i class="fas fa-trash-alt"></i> Delete
          </button>`
        : '';
      
      const commentButton = `
        <button class="comment-button ms-3" data-post-id="${post.id}">
          <i class="far fa-comment"></i> ${post.comments_count || 0}
        </button>
      `;
      
      // Build the post action buttons
      let actionButtons = '';
      if (isOwnPost) {
        // User's own post - show comment, edit, delete buttons
        actionButtons = `
          ${likeButton}
          ${commentButton}
          ${editButton}
          ${deleteButton}
        `;
      } else {
        // Other user's post - just show like and comment
        actionButtons = `
          ${likeButton}
          ${commentButton}
        `;
      }
      
      // Create post user header with avatar and username properly linked
      return `
        <div class="card post-card mb-3" id="post-${post.id}">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center">
                <a href="/profile/${post.user}" class="post-username" data-username="${post.user}">@${post.user}</a>
              </div>
              <small class="text-muted">${post.timestamp}</small>
            </div>
            <div class="post-content mt-2">${post.content}</div>
            ${post.image ? `<div class="post-image mt-2"><img src="${post.image}" alt="Post image" class="img-fluid rounded"></div>` : ''}
            <div class="mt-2 d-flex">
              ${actionButtons}
            </div>
            <div class="comments-section mt-3" id="comments-section-${post.id}" style="display: none;">
              <hr>
              <h6 class="mb-3">Comments</h6>
              <div class="comments-container" id="comments-container-${post.id}"></div>
              ${isAuthenticated ? `
                <div class="mt-3">
                  <textarea class="form-control comment-textarea" id="comment-textarea-${post.id}" rows="2" placeholder="Write a comment..."></textarea>
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 5px; width: 100%; margin-top: 8px;">
                    <div class="emoji-button-container"></div>
                    <button class="btn btn-secondary btn-sm cancel-comment-btn" data-post-id="${post.id}">Cancel</button>
                    <button class="btn btn-primary btn-sm add-comment-btn" data-post-id="${post.id}">Comment</button>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
    
    // Add event listeners to like and edit buttons
    document.querySelectorAll('.like-button').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        toggleLike(postId);
      });
    });
    
    document.querySelectorAll('.edit-button').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const postCard = document.getElementById(`post-${postId}`);
        const postContent = postCard.querySelector('.post-content').textContent;
        showEditForm(postId, postContent);
      });
    });
    
    // Add event listeners for delete buttons
    document.querySelectorAll('.delete-button').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        if (confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
          deletePost(postId);
        }
      });
    });
    
    // Add event listeners for comment buttons
    document.querySelectorAll('.comment-button').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        toggleCommentSection(postId);
      });
    });
    
    // Add event listeners for adding comments
    document.querySelectorAll('.add-comment-btn').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const commentTextarea = document.getElementById(`comment-textarea-${postId}`);
        addComment(postId, commentTextarea.value);
      });
    });
    
    // Add event listeners for canceling comments
    document.querySelectorAll('.cancel-comment-btn').forEach(button => {
      button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const commentTextarea = document.getElementById(`comment-textarea-${postId}`);
        commentTextarea.value = ''; // Clear the textarea
        
        // Hide comment section
        const commentsSection = document.getElementById(`comments-section-${postId}`);
        commentsSection.style.display = 'none';
      });
    });
    
    // Render pagination
    renderPagination(pageInfo);
  }
  
  // Show edit form for a post
  function showEditForm(postId, content) {
    const postCard = document.getElementById(`post-${postId}`);
    const postContentElement = postCard.querySelector('.post-content');
    
    postContentElement.innerHTML = `
      <textarea class="form-control mb-2 edit-textarea" rows="3">${content}</textarea>
      <div style="display: flex; justify-content: flex-start; align-items: center; gap: 5px; width: 100%;">
        <div class="emoji-button-container"></div>
        <button class="btn btn-secondary btn-sm cancel-edit">Cancel</button>
        <button class="btn btn-primary btn-sm save-edit" data-post-id="${postId}">Save</button>
      </div>
    `;
    
    // Add event listeners to edit form buttons
    postCard.querySelector('.cancel-edit').addEventListener('click', function() {
      postContentElement.innerHTML = content;
      
      // Re-enable the edit button
      const editButton = postCard.querySelector('.edit-button');
      if (editButton) {
        editButton.disabled = false;
      }
    });
    
    postCard.querySelector('.save-edit').addEventListener('click', function() {
      const newContent = postCard.querySelector('.edit-textarea').value;
      saveEditedPost(postId, newContent);
    });
    
    // Initialize emoji picker for the edit form with longer timeout
    setTimeout(() => {
      const textarea = postCard.querySelector('.edit-textarea');
      if (textarea && typeof addEmojiButtonsToForms === 'function') {
        try {
          addEmojiButtonsToForms();
          console.log('Initialized emoji picker for post edit');
          
          // Apply button spacing
          adjustButtonSpacing();
        } catch (error) {
          console.error('Error initializing emoji picker:', error);
        }
      }
    }, 500);
    
    // Focus on textarea
    postCard.querySelector('.edit-textarea').focus();
  }
  
  // Create a new post
  function createPost() {
    // Find the form and its elements
    const form = document.getElementById('new-post-form');
    const contentTextarea = document.getElementById('post-content');
    const imageInput = document.getElementById('post-image');
    
    // Return early if form elements not found
    if (!form || !contentTextarea) {
      console.error('Post form elements not found');
      showAlert('An error occurred. Please try again.', 'danger');
      return;
    }
    
    const content = contentTextarea.value;
    
    // Validate content
    const validation = validateInput(content);
    if (!validation.isValid) {
      showAlert(validation.error, 'danger');
      return;
    }
    
    // Check if we have an image to upload
    const hasImage = imageInput && imageInput.files && imageInput.files.length > 0;
    
    if (hasImage) {
      // Validate image
      const file = imageInput.files[0];
      const validFileTypes = ['image/jpeg', 'image/jpg', 'image/png'];
      
      if (!validFileTypes.includes(file.type)) {
        showAlert('Error: Only PNG and JPG images are allowed.', 'danger');
        return;
      }
      
      // Check file size (5MB max)
      const maxSize = 5 * 1024 * 1024; // 5MB in bytes
      if (file.size > maxSize) {
        showAlert('Error: Image size should be less than 5MB.', 'danger');
        return;
      }
      
      // Use FormData for file uploads
      const formData = new FormData(form);
      
      fetch(`${baseUrl}/api/posts/create`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin',
        body: formData
      })
        .then(response => {
          if (!response.ok) throw new Error('Failed to create post');
          return response.json();
        })
        .then(data => {
          // Clear the form
          contentTextarea.value = '';
          if (imageInput) imageInput.value = '';
          
          // Update character count if element exists
          const characterCountEl = document.getElementById('character-count');
          if (characterCountEl) {
            characterCountEl.textContent = '0/280';
          }
          
          // Reload posts to show the new one
          currentPage = 1;
          loadPosts();
          
          showAlert('Post created successfully!', 'success');
        })
        .catch(error => {
          console.error('Error creating post:', error);
          showAlert('Failed to create post. Please try again.', 'danger');
        });
    } else {
      // No image, use JSON for just the content
      fetch(`${baseUrl}/api/posts/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin',
        body: JSON.stringify({ content: validation.sanitized })
      })
        .then(response => {
          if (!response.ok) throw new Error('Failed to create post');
          return response.json();
        })
        .then(data => {
          // Clear the textarea
          contentTextarea.value = '';
          
          // Update character count if element exists
          const characterCountEl = document.getElementById('character-count');
          if (characterCountEl) {
            characterCountEl.textContent = '0/280';
          }
          
          // Reload posts to show the new one
          currentPage = 1;
          loadPosts();
          
          showAlert('Post created successfully!', 'success');
        })
        .catch(error => {
          console.error('Error creating post:', error);
          showAlert('Failed to create post. Please try again.', 'danger');
        });
    }
  }
  
  // Save edited post
  function saveEditedPost(postId, content) {
    // Validate content
    const validation = validateInput(content);
    if (!validation.isValid) {
      showAlert(validation.error, 'danger');
      return;
    }
    
    fetch(`${baseUrl}/api/posts/${postId}/edit`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin',
      body: JSON.stringify({ content: validation.sanitized })
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to update post');
        return response.json();
      })
      .then(data => {
        // Update post content in the DOM
        const postCard = document.getElementById(`post-${postId}`);
        postCard.querySelector('.post-content').innerHTML = content;
        
        // Re-enable the edit button
        const editButton = postCard.querySelector('.edit-button');
        if (editButton) {
          editButton.disabled = false;
        }
        
        showAlert('Post updated successfully!', 'success');
      })
      .catch(error => {
        console.error('Error updating post:', error);
        showAlert('Failed to update post. Please try again.', 'danger');
        
        // Re-enable the edit button even if there's an error
        const postCard = document.getElementById(`post-${postId}`);
        const editButton = postCard.querySelector('.edit-button');
        if (editButton) {
          editButton.disabled = false;
        }
      });
  }
  
  // Toggle like on a post
  function toggleLike(postId) {
    fetch(`${baseUrl}/api/posts/${postId}/like`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin'
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to toggle like');
        return response.json();
      })
      .then(data => {
        // Update like button
        const likeButton = document.querySelector(`.like-button[data-post-id="${postId}"]`);
        const likeIcon = likeButton.querySelector('i');
        
        likeButton.classList.toggle('active', data.liked);
        likeIcon.className = data.liked ? 'fas fa-heart' : 'far fa-heart';
        likeButton.innerHTML = `${likeIcon.outerHTML} ${data.likes_count}`;
      })
      .catch(error => {
        console.error('Error toggling like:', error);
        showAlert('Failed to like post. Please try again.', 'danger');
      });
  }
  
  // Toggle follow for a user
  function toggleFollow() {
    if (!currentProfile) return;
    
    fetch(`${baseUrl}/api/users/${currentProfile.username}/follow`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin'
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to toggle follow');
        return response.json();
      })
      .then(data => {
        // Update follow button and follower count
        currentProfile.is_following = data.following;
        currentProfile.followers_count = data.followers_count;
        
        const followButton = document.getElementById('follow-button');
        followButton.textContent = data.following ? 'Unfollow' : 'Follow';
        followButton.className = `btn ${data.following ? 'btn-outline-primary' : 'btn-primary'} follow-button`;
        
        // Update follower count in the DOM
        const followerCountElement = document.querySelector('.profile-stats div:first-child strong');
        followerCountElement.textContent = data.followers_count;
        
        // Update followers text (follower/followers)
        const followerTextElement = document.querySelector('.profile-stats div:first-child');
        followerTextElement.innerHTML = `<strong>${data.followers_count}</strong> ${data.followers_count === 1 ? 'follower' : 'followers'}`;
      })
      .catch(error => {
        console.error('Error toggling follow:', error);
        showAlert('Failed to follow user. Please try again.', 'danger');
      });
  }
  
  // Toggle comment section for a post
  function toggleCommentSection(postId) {
    const commentsSection = document.getElementById(`comments-section-${postId}`);
    const isHidden = commentsSection.style.display === 'none';
    
    if (isHidden) {
      commentsSection.style.display = 'block';
      loadComments(postId);
      
      // Setup a function to repeatedly try initializing emoji pickers
      let attempts = 0;
      const maxAttempts = 5;
      
      function initializeEmojiPicker() {
        attempts++;
        console.log(`Attempting to initialize emoji pickers (attempt ${attempts})`);
        
        try {
          // Main comment textarea
          const commentTextarea = document.getElementById(`comment-textarea-${postId}`);
          if (commentTextarea) {
            const container = commentTextarea.closest('.mt-3');
            if (container) {
              const emojiContainer = container.querySelector('.emoji-button-container');
              if (emojiContainer) {
                console.log('Found emoji container for comment textarea');
                
                // Ensure emoji container has proper styles
                emojiContainer.style.display = 'block';
                emojiContainer.style.position = 'relative';
                
                // Initialize emoji buttons 
                if (typeof addEmojiButtonsToForms === 'function') {
                  addEmojiButtonsToForms();
                } else {
                  console.warn('Emoji button function not found');
                  
                  // Try again if we haven't reached max attempts
                  if (attempts < maxAttempts) {
                    setTimeout(initializeEmojiPicker, 300);
                  }
                  return;
                }
              }
            }
          }
          
          // After initializing, do another check for any missing emoji pickers
          setTimeout(() => {
            // Check for reply forms too
            document.querySelectorAll('.reply-form-container:visible').forEach(container => {
              const textarea = container.querySelector('.reply-textarea');
              const emojiContainer = container.querySelector('.emoji-button-container');
              
              if (textarea && emojiContainer && !emojiContainer.querySelector('.emoji-picker-container')) {
                console.log('Found reply form without emoji picker, initializing');
                if (typeof addEmojiButtonsToForms === 'function') {
                  addEmojiButtonsToForms();
                }
              }
            });
          }, 100);
          
        } catch (error) {
          console.error('Error initializing emoji pickers:', error);
          
          // Try again if we haven't reached max attempts
          if (attempts < maxAttempts) {
            setTimeout(initializeEmojiPicker, 300);
          }
        }
      }
      
      // Start the initialization process with a delay to allow comments to load
      setTimeout(initializeEmojiPicker, 500);
      
    } else {
      commentsSection.style.display = 'none';
    }
  }
  
  // Load comments for a post
  function loadComments(postId) {
    const commentsContainer = document.getElementById(`comments-container-${postId}`);
    commentsContainer.innerHTML = '<div class="text-center my-2">Loading comments...</div>';
    
    fetch(`${baseUrl}/api/posts/${postId}/comments`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to load comments');
        return response.json();
      })
      .then(data => {
        if (data.comments.length === 0) {
          commentsContainer.innerHTML = '<div class="text-center my-2">No comments yet. Be the first to comment!</div>';
          return;
        }
        
        // Helper function to recursively render comments and their replies
        function renderCommentTree(comment, isTopLevel) {
          const commentHtml = renderComment(comment, isTopLevel);
          
          // If the comment has replies, render them recursively
          let repliesHtml = '';
          if (comment.replies && comment.replies.length > 0) {
            repliesHtml = `
              <div class="replies ms-4 mt-2">
                ${comment.replies.map(reply => renderCommentTree(reply, false)).join('')}
              </div>
            `;
          }
          
          return commentHtml + repliesHtml;
        }
        
        // Render all top-level comments with their nested replies
        commentsContainer.innerHTML = data.comments.map(comment => renderCommentTree(comment, true)).join('');
        
        // Set up all comment-related event listeners
        setupCommentEventListeners(postId);
        
        // Initialize emoji pickers for the comment section
        initializeEmojiPickersForComments(postId);
      })
      .catch(error => {
        console.error('Error loading comments:', error);
        commentsContainer.innerHTML = '<div class="text-center my-2 text-danger">Failed to load comments. Please try again.</div>';
      });
  }
  
  // Helper function to initialize emoji pickers for comments
  function initializeEmojiPickersForComments(postId) {
    // Check if the emoji picker initialization function exists
    if (typeof addEmojiButtonsToForms === 'function') {
      setTimeout(() => {
        addEmojiButtonsToForms();
      }, 200);
    } else {
      console.warn('Emoji picker initialization function not found.');
    }
  }
  
  // Helper function to set up all comment event listeners
  function setupCommentEventListeners(postId) {
    // Add event listeners for reply buttons
    document.querySelectorAll('.reply-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        showReplyForm(postId, commentId);
      });
    });
    
    // Add event listeners for submit reply buttons
    document.querySelectorAll('.submit-reply-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        const replyTextarea = document.getElementById(`reply-textarea-${commentId}`);
        addReply(postId, commentId, replyTextarea.value);
      });
    });
    
    // Add event listeners for cancel reply buttons
    document.querySelectorAll('.cancel-reply-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        hideReplyForm(commentId);
      });
    });
    
    // Add event listeners for edit comment buttons
    document.querySelectorAll('.edit-comment-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        showCommentEditForm(commentId);
      });
    });
    
    // Add event listeners for save comment edit buttons
    document.querySelectorAll('.save-comment-edit-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        const editTextarea = document.getElementById(`comment-edit-textarea-${commentId}`);
        saveEditedComment(commentId, editTextarea.value);
      });
    });
    
    // Add event listeners for cancel comment edit buttons
    document.querySelectorAll('.cancel-comment-edit-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        hideCommentEditForm(commentId);
      });
    });
    
    // Add event listeners for delete comment buttons
    document.querySelectorAll('.delete-comment-btn').forEach(button => {
      button.addEventListener('click', function() {
        const commentId = this.dataset.commentId;
        if (confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
          deleteComment(postId, commentId);
        }
      });
    });
  }
  
  // Render a single comment or reply
  function renderComment(comment, isTopLevel) {
    const replyButton = isAuthenticated
      ? `<button class="btn btn-sm text-primary reply-btn" data-comment-id="${comment.id}">Reply</button>`
      : '';
    
    const editButton = comment.is_owner
      ? `<button class="btn btn-sm text-secondary edit-comment-btn ms-2" data-comment-id="${comment.id}">Edit</button>`
      : '';

    const deleteButton = comment.is_owner
      ? `<button class="btn btn-sm text-danger delete-comment-btn ms-2" data-comment-id="${comment.id}">Delete</button>`
      : '';

    const editedLabel = comment.is_edited
      ? `<span class="text-muted small ms-1">(edited)</span>`
      : '';
    
    return `
      <div class="comment mb-2" id="comment-${comment.id}">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <a href="/profile/${comment.user}" class="fw-bold" data-username="${comment.user}">${comment.user}</a>
            <span class="ms-2 small text-muted">${comment.timestamp}</span>
            ${editedLabel}
          </div>
          <div>
            ${replyButton}
            ${editButton}
            ${deleteButton}
          </div>
        </div>
        <div class="comment-content" id="comment-content-${comment.id}">${comment.content}</div>
        <div class="comment-edit-form mt-2" id="comment-edit-form-${comment.id}" style="display: none;">
          <textarea class="form-control comment-edit-textarea" id="comment-edit-textarea-${comment.id}" rows="2">${comment.content}</textarea>
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 5px; width: 100%; margin-top: 8px;">
            <div class="emoji-button-container"></div>
            <button class="btn btn-secondary btn-sm cancel-comment-edit-btn" data-comment-id="${comment.id}">Cancel</button>
            <button class="btn btn-primary btn-sm save-comment-edit-btn" data-comment-id="${comment.id}">Save</button>
          </div>
        </div>
        <div class="reply-form-container mt-2" id="reply-form-container-${comment.id}" style="display: none;">
          <textarea class="form-control reply-textarea" id="reply-textarea-${comment.id}" rows="2" placeholder="Write a reply..."></textarea>
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 5px; width: 100%; margin-top: 8px;">
            <div class="emoji-button-container"></div>
            <button class="btn btn-secondary btn-sm cancel-reply-btn" data-comment-id="${comment.id}">Cancel</button>
            <button class="btn btn-primary btn-sm submit-reply-btn" data-comment-id="${comment.id}">Reply</button>
          </div>
        </div>
      </div>
    `;
  }
  
  // Show the reply form for a comment
  function showReplyForm(postId, commentId) {
    const replyFormContainer = document.getElementById(`reply-form-container-${commentId}`);
    replyFormContainer.style.display = 'block';
    
    // Ensure the emoji button container has the proper styling
    const emojiContainer = replyFormContainer.querySelector('.emoji-button-container');
    if (emojiContainer) {
      emojiContainer.style.display = 'block';
      emojiContainer.style.position = 'relative';
    }
    
    // Focus the textarea 
    const textarea = document.getElementById(`reply-textarea-${commentId}`);
    if (textarea) {
      textarea.focus();
    }
    
    // Initialize emoji picker for the reply form with a longer delay
    setTimeout(() => {
      if (typeof addEmojiButtonsToForms === 'function') {
        try {
          addEmojiButtonsToForms();
          console.log('Initialized emoji picker for comment reply');
          
          // Additional style fixes after initialization
          const buttonContainer = replyFormContainer.querySelector('div[style*="display: flex"]');
          if (buttonContainer) {
            buttonContainer.style.justifyContent = 'flex-start';
            buttonContainer.style.width = '100%';
            buttonContainer.style.gap = '5px';
          }
          
          // Apply button spacing
          adjustButtonSpacing();
        } catch (error) {
          console.error('Error initializing emoji picker:', error);
        }
      }
    }, 750); // Increased timeout for stability
  }
  
  // Hide the reply form for a comment
  function hideReplyForm(commentId) {
    const replyFormContainer = document.getElementById(`reply-form-container-${commentId}`);
    replyFormContainer.style.display = 'none';
    document.getElementById(`reply-textarea-${commentId}`).value = '';
  }
  
  // Show alert message
  function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    // Auto-close alert after 5 seconds
    setTimeout(() => {
      const alert = document.querySelector('.alert');
      if (alert) {
        alert.classList.remove('show');
        setTimeout(() => alertContainer.innerHTML = '', 150);
      }
    }, 5000);
  }
  
  // Navigation functionality
  function setupNavigation() {
    // Handle "All Posts" link - use querySelectorAll and check if element exists
    const allPostsLinks = document.querySelectorAll('a[href="/"]');
    if (allPostsLinks.length > 0) {
      allPostsLinks.forEach(link => {
        link.addEventListener('click', function(e) {
          e.preventDefault();
          currentView = 'all-posts';
          currentPage = 1;
          renderApp();
        });
      });
    }
    
    // Handle "Following" link if authenticated
    if (isAuthenticated) {
      const followingLinks = document.querySelectorAll('a[href="/following"]');
      if (followingLinks.length > 0) {
        followingLinks.forEach(link => {
          link.addEventListener('click', function(e) {
            e.preventDefault();
            currentView = 'following';
            currentPage = 1;
            renderApp();
          });
        });
      }
      
      // Also check for the sidebar following link with class 'following-link'
      const sidebarFollowingLink = document.querySelector('.following-link');
      if (sidebarFollowingLink) {
        sidebarFollowingLink.addEventListener('click', function(e) {
          e.preventDefault();
          console.log("Clicked Following link from sidebar");
          currentView = 'following';
          currentPage = 1;
          renderApp();
        });
      }
    }
    
    // Add listener for profile link in sidebar
    const profileLink = document.querySelector('.profile-link');
    if (profileLink) {
      profileLink.addEventListener('click', function(e) {
        e.preventDefault();
        console.log("Clicked My Posts link for current user:", currentUsername);
        currentView = 'profile';
        currentProfile = { username: currentUsername };
        currentPage = 1;
        renderApp();
      });
    }
  }
  
  // Add global event delegation for profile links and following link
  document.addEventListener('click', function(e) {
    // Handle profile links
    const profileLink = e.target.closest('a[href^="/profile/"]');
    if (profileLink) {
      e.preventDefault();
      const username = profileLink.getAttribute('href').split('/profile/')[1];
      console.log("Clicked profile link for user:", username);
      currentView = 'profile';
      currentProfile = { username };
      currentPage = 1;
      renderApp();
      return;
    }
    
    // Handle following link in navbar
    const followingNavLink = e.target.closest('.nav-link[href="/following"]');
    if (followingNavLink) {
      e.preventDefault();
      console.log("Clicked Following link in navbar");
      currentView = 'following';
      currentPage = 1;
      renderApp();
      return;
    }
    
    // Handle the sidebar profile link (My Posts)
    const sidebarProfileLink = e.target.closest('.profile-link');
    if (sidebarProfileLink) {
      e.preventDefault();
      console.log("Clicked My Posts link in sidebar for current user:", currentUsername);
      currentView = 'profile';
      currentProfile = { username: currentUsername };
      currentPage = 1;
      renderApp();
      return;
    }
    
    // Handle the sidebar following link
    const sidebarFollowingLink = e.target.closest('.following-link');
    if (sidebarFollowingLink) {
      e.preventDefault();
      console.log("Clicked Following link in sidebar");
      currentView = 'following';
      currentPage = 1;
      renderApp();
      return;
    }
  });
  
  // Initialize the app
  function init() {
    // Set up navigation event listeners
    setupNavigation();
    
    // Render the app
    renderApp();
    
    // Window resize event listeners
    window.addEventListener('resize', debounce(handleWindowResize, 250));
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Initial UI adjustment
    adjustUI();
    
    // Add event listeners for navigation login/register buttons
    const navLoginBtn = document.getElementById('nav-login-btn');
    if (navLoginBtn) {
      navLoginBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showLoginModal();
      });
    }
    
    const navRegisterBtn = document.getElementById('nav-register-btn');
    if (navRegisterBtn) {
      navRegisterBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showRegisterModal();
      });
    }
  }
  
  // Start the app
  init();

  // Add a new comment to a post
  function addComment(postId, content) {
    // Validate content
    const validation = validateInput(content);
    if (!validation.isValid) {
      showAlert(validation.error, 'danger');
      return;
    }
    
    fetch(`${baseUrl}/api/posts/${postId}/comments/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin',
      body: JSON.stringify({ content: validation.sanitized })
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to add comment');
        return response.json();
      })
      .then(data => {
        // Clear the textarea
        document.getElementById(`comment-textarea-${postId}`).value = '';
        
        // Reload comments
        loadComments(postId);
        
        // Update comment count in the button
        const commentButton = document.querySelector(`.comment-button[data-post-id="${postId}"]`);
        const currentCount = parseInt(commentButton.innerText.trim().split(' ')[1] || '0');
        commentButton.innerHTML = `<i class="far fa-comment"></i> ${currentCount + 1}`;
        
        showAlert('Comment added successfully!', 'success');
      })
      .catch(error => {
        console.error('Error adding comment:', error);
        showAlert('Failed to add comment. Please try again.', 'danger');
      });
  }
  
  // Add a reply to a comment
  function addReply(postId, commentId, content) {
    // Validate content
    const validation = validateInput(content);
    if (!validation.isValid) {
      showAlert(validation.error, 'danger');
      return;
    }
    
    fetch(`${baseUrl}/api/posts/${postId}/comments/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin',
      body: JSON.stringify({ 
        content: validation.sanitized,
        parent_id: commentId
      })
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to add reply');
        return response.json();
      })
      .then(data => {
        // Hide reply form
        hideReplyForm(commentId);
        
        // Reload comments
        loadComments(postId);
        
        showAlert('Reply added successfully!', 'success');
      })
      .catch(error => {
        console.error('Error adding reply:', error);
        showAlert('Failed to add reply. Please try again.', 'danger');
      });
  }
  
  // Show login form as a modal
  function showLoginModal() {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
    
    // Create modal HTML
    const modalHTML = `
      <div class="modal fade show" style="display: block;">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Log In</h5>
              <button type="button" class="btn-close" id="close-modal"></button>
            </div>
            <div class="modal-body">
              <div id="login-alert" class="alert alert-danger" style="display: none;"></div>
              <form id="login-form" method="post" action="/login">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <div class="form-group mb-3">
                  <input class="form-control" type="text" name="username" placeholder="Username" required autofocus>
                </div>
                <div class="form-group mb-3">
                  <input class="form-control" type="password" name="password" placeholder="Password" required>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary" id="switch-to-register">Register</button>
              <button type="button" class="btn btn-primary" id="submit-login">Log In</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Add modal to DOM
    const modalContainer = document.createElement('div');
    modalContainer.id = 'login-modal';
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Add event listeners
    const closeModalBtn = document.getElementById('close-modal');
    const switchToRegisterBtn = document.getElementById('switch-to-register');
    const submitLoginBtn = document.getElementById('submit-login');
    
    // Close modal function
    const closeModal = () => {
      document.body.removeChild(modalContainer);
      document.body.removeChild(backdrop);
    };
    
    // Close button event
    closeModalBtn.addEventListener('click', closeModal);
    
    // Switch to register modal
    switchToRegisterBtn.addEventListener('click', () => {
      closeModal();
      showRegisterModal();
    });
    
    // Submit login form
    submitLoginBtn.addEventListener('click', () => {
      document.getElementById('login-form').submit();
    });
    
    // Escape key closes modal
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        closeModal();
      }
    });
    
    // Enter key submits form
    document.querySelector('#login-form input[name="password"]').addEventListener('keydown', function(event) {
      if (event.key === 'Enter') {
        document.getElementById('login-form').submit();
      }
    });
  }

  // Show register form as a modal
  function showRegisterModal() {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
    
    // Create modal HTML
    const modalHTML = `
      <div class="modal fade show" style="display: block;">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Register</h5>
              <button type="button" class="btn-close" id="close-modal"></button>
            </div>
            <div class="modal-body">
              <div id="register-alert" class="alert alert-danger" style="display: none;"></div>
              <form id="register-form" method="post" action="/register">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <div class="form-group mb-3">
                  <input class="form-control" type="text" name="username" placeholder="Username" required autofocus>
                </div>
                <div class="form-group mb-3">
                  <input class="form-control" type="email" name="email" placeholder="Email Address" required>
                </div>
                <div class="form-group mb-3">
                  <input class="form-control" type="password" name="password1" placeholder="Password" required>
                </div>
                <div class="form-group mb-3">
                  <input class="form-control" type="password" name="password2" placeholder="Confirm Password" required>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary" id="switch-to-login">Log In</button>
              <button type="button" class="btn btn-primary" id="submit-register">Register</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Add modal to DOM
    const modalContainer = document.createElement('div');
    modalContainer.id = 'register-modal';
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Add event listeners
    const closeModalBtn = document.getElementById('close-modal');
    const switchToLoginBtn = document.getElementById('switch-to-login');
    const submitRegisterBtn = document.getElementById('submit-register');
    
    // Close modal function
    const closeModal = () => {
      document.body.removeChild(modalContainer);
      document.body.removeChild(backdrop);
    };
    
    // Close button event
    closeModalBtn.addEventListener('click', closeModal);
    
    // Switch to login modal
    switchToLoginBtn.addEventListener('click', () => {
      closeModal();
      showLoginModal();
    });
    
    // Submit register form
    submitRegisterBtn.addEventListener('click', () => {
      document.getElementById('register-form').submit();
    });
    
    // Escape key closes modal
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        closeModal();
      }
    });
    
    // Enter key submits form
    document.querySelector('#register-form input[name="password2"]').addEventListener('keydown', function(event) {
      if (event.key === 'Enter') {
        document.getElementById('register-form').submit();
      }
    });
  }

  // Function to check URL parameters for auth-related actions
  function checkUrlParamsForAuth() {
    if (isAuthenticated) return; // Skip if user is already logged in
    
    const urlParams = new URLSearchParams(window.location.search);
    
    // Show login modal if requested
    if (urlParams.has('show_login')) {
      setTimeout(() => showLoginModal(), 500);
    }
    
    // Show register modal if requested
    if (urlParams.has('show_register')) {
      setTimeout(() => showRegisterModal(), 500);
    }
    
    // Handle login errors
    if (urlParams.has('login_error')) {
      const error = urlParams.get('login_error');
      const username = urlParams.get('username') || '';
      
      setTimeout(() => {
        showLoginModal();
        const loginAlert = document.getElementById('login-alert');
        if (loginAlert) {
          if (error === 'invalid_credentials') {
            loginAlert.textContent = 'Invalid username and/or password.';
          } else {
            loginAlert.textContent = 'An error occurred during login. Please try again.';
          }
          loginAlert.style.display = 'block';
          
          // Pre-fill username if provided
          const usernameInput = document.querySelector('#login-form input[name="username"]');
          if (usernameInput && username) {
            usernameInput.value = username;
            // Focus on password field instead
            setTimeout(() => {
              document.querySelector('#login-form input[name="password"]').focus();
            }, 100);
          }
        }
      }, 500);
    }
    
    // Handle login messages (like "Username exists, please log in")
    if (urlParams.has('login_message')) {
      const message = urlParams.get('login_message');
      const username = urlParams.get('username') || '';
      
      setTimeout(() => {
        showLoginModal();
        const loginAlert = document.getElementById('login-alert');
        if (loginAlert) {
          if (message === 'username_exists') {
            loginAlert.textContent = `Username '${username}' already exists. Please log in below.`;
            loginAlert.className = 'alert alert-info';
          } else {
            loginAlert.textContent = 'Please log in to continue.';
            loginAlert.className = 'alert alert-info';
          }
          loginAlert.style.display = 'block';
          
          // Pre-fill username if provided
          const usernameInput = document.querySelector('#login-form input[name="username"]');
          if (usernameInput && username) {
            usernameInput.value = username;
            // Focus on password field
            setTimeout(() => {
              document.querySelector('#login-form input[name="password"]').focus();
            }, 100);
          }
        }
      }, 500);
    }
    
    // Handle register messages
    if (urlParams.has('register_message')) {
      const message = urlParams.get('register_message');
      const username = urlParams.get('username') || '';
      
      setTimeout(() => {
        showRegisterModal();
        const registerAlert = document.getElementById('register-alert');
        if (registerAlert) {
          if (message === 'username_not_found') {
            registerAlert.textContent = `Username '${username}' is not registered. Please sign up below.`;
            registerAlert.className = 'alert alert-info';
          } else {
            registerAlert.textContent = 'Please create an account to continue.';
            registerAlert.className = 'alert alert-info';
          }
          registerAlert.style.display = 'block';
          
          // Pre-fill username if provided
          const usernameInput = document.querySelector('#register-form input[name="username"]');
          if (usernameInput && username) {
            usernameInput.value = username;
            // Focus on email field
            setTimeout(() => {
              document.querySelector('#register-form input[name="email"]').focus();
            }, 100);
          }
        }
      }, 500);
    }
    
    // Handle register errors
    if (urlParams.has('register_error')) {
      setTimeout(() => {
        showRegisterModal();
        const registerAlert = document.getElementById('register-alert');
        if (registerAlert) {
          registerAlert.textContent = 'There were errors in your registration form. Please try again.';
          registerAlert.style.display = 'block';
        }
      }, 500);
    }
    
    // Clean URL after processing params
    if (urlParams.has('login_error') || urlParams.has('login_message') || 
        urlParams.has('register_error') || urlParams.has('register_message') ||
        urlParams.has('show_login') || urlParams.has('show_register')) {
      // Remove auth params from URL without reloading page
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }

  // Delete a post
  function deletePost(postId) {
    fetch(`${baseUrl}/api/posts/${postId}/delete`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin'
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to delete post');
        return response.json();
      })
      .then(data => {
        // Remove the post from the DOM
        const postCard = document.getElementById(`post-${postId}`);
        if (postCard) {
          postCard.remove();
        }
        
        // Show success message
        showAlert('Post deleted successfully!', 'success');
        
        // If we're in profile view, we may need to update the posts count
        if (currentView === 'profile' && currentProfile) {
          currentProfile.posts_count = Math.max(0, (currentProfile.posts_count || 1) - 1);
          const postsCountEl = document.querySelector('.profile-stats div:first-child strong');
          if (postsCountEl) {
            postsCountEl.textContent = currentProfile.posts_count;
          }
          
          // If all posts are deleted, show "No posts" message
          const postsContainer = document.getElementById('posts-container');
          if (postsContainer && !postsContainer.querySelector('.post-card')) {
            postsContainer.innerHTML = '<div class="text-center my-5">No posts to show.</div>';
          }
        }
      })
      .catch(error => {
        console.error('Error deleting post:', error);
        showAlert('Failed to delete post. Please try again.', 'danger');
      });
  }
  
  // Delete a comment
  function deleteComment(postId, commentId) {
    fetch(`${baseUrl}/api/comments/${commentId}/delete`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin'
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to delete comment');
        return response.json();
      })
      .then(data => {
        // Reload comments
        loadComments(postId);
        
        // Update comment count in the button
        const commentButton = document.querySelector(`.comment-button[data-post-id="${postId}"]`);
        if (commentButton) {
          const currentCount = parseInt(commentButton.innerText.trim().split(' ')[1] || '1');
          commentButton.innerHTML = `<i class="far fa-comment"></i> ${Math.max(0, currentCount - 1)}`;
        }
        
        showAlert('Comment deleted successfully!', 'success');
      })
      .catch(error => {
        console.error('Error deleting comment:', error);
        showAlert('Failed to delete comment. Please try again.', 'danger');
      });
  }
  
  // Show comment edit form
  function showCommentEditForm(commentId) {
    const commentContent = document.getElementById(`comment-content-${commentId}`);
    const editForm = document.getElementById(`comment-edit-form-${commentId}`);
    
    if (commentContent && editForm) {
      commentContent.style.display = 'none';
      editForm.style.display = 'block';
      
      // Initialize emoji picker for edit form
      setTimeout(() => {
        if (typeof addEmojiButtonsToForms === 'function') {
          addEmojiButtonsToForms();
        }
      }, 100);
      
      // Focus on textarea
      document.getElementById(`comment-edit-textarea-${commentId}`).focus();
    }
  }
  
  // Hide comment edit form
  function hideCommentEditForm(commentId) {
    const commentContent = document.getElementById(`comment-content-${commentId}`);
    const editForm = document.getElementById(`comment-edit-form-${commentId}`);
    
    if (commentContent && editForm) {
      commentContent.style.display = 'block';
      editForm.style.display = 'none';
    }
  }
  
  // Save edited comment
  function saveEditedComment(commentId, content) {
    // Validate content
    const validation = validateInput(content, 500); // Allow longer comments
    if (!validation.isValid) {
      showAlert(validation.error, 'danger');
      return;
    }
    
    fetch(`${baseUrl}/api/comments/${commentId}/edit`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      },
      credentials: 'same-origin',
      body: JSON.stringify({ content: validation.sanitized })
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to update comment');
        return response.json();
      })
      .then(data => {
        // Update comment content in the DOM
        const commentContent = document.getElementById(`comment-content-${commentId}`);
        if (commentContent) {
          commentContent.innerHTML = content;
        }
        
        // Hide edit form
        hideCommentEditForm(commentId);
        
        // Add edited marker if not already present
        const commentHeader = document.getElementById(`comment-${commentId}`).querySelector('.d-flex.justify-content-between.align-items-center div:first-child');
        if (commentHeader && !commentHeader.querySelector('.text-muted.small')) {
          commentHeader.innerHTML += '<span class="text-muted small ms-1">(edited)</span>';
        }
        
        showAlert('Comment updated successfully!', 'success');
      })
      .catch(error => {
        console.error('Error updating comment:', error);
        showAlert('Failed to update comment. Please try again.', 'danger');
      });
  }

  // Function to adjust button spacing for all forms
  function adjustButtonSpacing() {
    // Find all button containers
    document.querySelectorAll('div[style*="display: flex"], div.d-flex').forEach(container => {
      // Skip containers that don't have buttons
      if (!container.querySelector('button')) return;
      
      // Skip containers that don't have emoji container
      if (!container.querySelector('.emoji-button-container')) return;
      
      // Special handling for new post form
      if (container.closest('#new-post-form')) {
        container.style.justifyContent = 'flex-start';
        container.style.alignItems = 'center';
        container.style.gap = '5px';
        
        // Ensure emoji button container has proper margin
        const emojiContainer = container.querySelector('.emoji-button-container');
        if (emojiContainer) {
          emojiContainer.style.marginRight = '10px';
          emojiContainer.style.flexShrink = '0';
        }
        
        // Add margin between buttons
        const buttons = container.querySelectorAll('button:not(.emoji-button)');
        if (buttons.length > 1) {
          for (let i = 0; i < buttons.length - 1; i++) {
            buttons[i].style.marginRight = '5px';
          }
        }
        return;
      }
      
      // Apply flex-start alignment for other containers
      container.style.justifyContent = 'flex-start';
      container.style.alignItems = 'center';
      container.style.gap = '5px';
      
      // Ensure emoji button container has proper margin
      const emojiContainer = container.querySelector('.emoji-button-container');
      if (emojiContainer) {
        emojiContainer.style.marginRight = '10px';
      }
      
      // Add margin between buttons
      const buttons = container.querySelectorAll('button:not(.emoji-button)');
      if (buttons.length > 1) {
        for (let i = 0; i < buttons.length - 1; i++) {
          buttons[i].style.marginRight = '5px';
        }
      }
    });
  }
  
  // Make adjustButtonSpacing available globally
  window.adjustButtonSpacing = adjustButtonSpacing;
  
  // Wait for window to load, then call adjustButtonSpacing
  window.addEventListener('load', function() {
    setTimeout(adjustButtonSpacing, 1000);
  });
}); 