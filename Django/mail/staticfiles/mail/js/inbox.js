document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#drafts').addEventListener('click', () => load_mailbox('drafts'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', () => compose_email());

  // Add event listeners for compose view buttons
  document.querySelector('#save-draft').addEventListener('click', save_draft);
  document.querySelector('#cancel-compose').addEventListener('click', cancel_compose);

  // Add event listeners for batch action buttons
  document.querySelector('#batch-archive').addEventListener('click', batchArchive);
  document.querySelector('#batch-mark-read').addEventListener('click', () => batchMarkReadStatus(true));
  document.querySelector('#batch-mark-unread').addEventListener('click', () => batchMarkReadStatus(false));
  document.querySelector('#batch-delete').addEventListener('click', batchDelete);

  // By default, load the inbox
  load_mailbox('inbox');

  // Add event listener for the compose form submission
  document.querySelector('#compose-form').addEventListener('submit', function(event) {
    // Prevent default form submission
    event.preventDefault();
    
    // Validate form using our FormValidator
    const form = document.querySelector('#compose-form');
    const isValid = FormValidator.validateForm(form);
    
    if (isValid) {
      // Form is valid, send the email
      const recipients = document.querySelector('#compose-recipients').value.trim();
      const subject = document.querySelector('#compose-subject').value.trim();
      const body = document.querySelector('#compose-body').value.trim();
      const draftId = document.querySelector('#draft-id').value;
      
      // Delete the draft if this was a draft being sent
      if (draftId) {
        fetch(`/emails/${draftId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          }
        }).catch(error => {
          console.error('Error deleting draft:', error);
        });
      }
      
      // Send the email
      const data = {
        recipients: recipients,
        subject: subject,
        body: body,
        is_draft: false
      };
      console.log('Sending data:', data);
      
      fetch('/emails', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        }
      })
      .then(response => response.json())
      .then(result => {
        console.log(result);
        if (!result.error) {
          load_mailbox('sent');
        } else {
          alert(result.error);
        }
      })
      .catch(error => {
        console.error('Error sending email:', error);
        alert('Failed to send email. Please try again.');
      });
    }
  });

  // Function to save a draft email
  function save_draft() {
    const recipients = document.querySelector('#compose-recipients').value.trim();
    const subject = document.querySelector('#compose-subject').value.trim();
    const body = document.querySelector('#compose-body').value.trim();
    const draftId = document.querySelector('#draft-id').value;
    
    // Only save if there's some content
    if (!recipients && !subject && !body) {
      alert('Cannot save an empty draft');
      return;
    }
    
    const method = draftId ? 'PUT' : 'POST';
    const url = draftId ? `/emails/${draftId}` : '/emails';
    
    fetch(url, {
      method: method,
      body: JSON.stringify({
        recipients: recipients,
        subject: subject,
        body: body,
        is_draft: true
      }),
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      }
    })
    .then(response => response.json())
    .then(result => {
      console.log(result);
      // If this is a new draft, update the draft-id field
      if (!draftId && result.id) {
        document.querySelector('#draft-id').value = result.id;
      }
      alert('Draft saved successfully');
    })
    .catch(error => {
      console.error('Error saving draft:', error);
      alert('Failed to save draft. Please try again.');
    });
  }

  // Function to cancel compose and return to previous view
  function cancel_compose() {
    // Check if there are unsaved changes
    const recipients = document.querySelector('#compose-recipients').value.trim();
    const subject = document.querySelector('#compose-subject').value.trim();
    const body = document.querySelector('#compose-body').value.trim();
    
    if (recipients || subject || body) {
      if (confirm('You have unsaved changes. Do you want to save this draft?')) {
        save_draft();
      }
    }
    
    // Return to inbox
    load_mailbox('inbox');
  }

  // Function to get the CSRF token from the cookies
  function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
  }

  // Function to toggle archive status
  function toggleArchive(email_id, currentStatus, currentMailbox) {
    fetch(`/emails/${email_id}`, {
      method: 'PUT',
      body: JSON.stringify({ archived: !currentStatus }),
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      }
    })
    .then(response => {
      if (response.ok) {
        // If we're in the sent mailbox and we're archiving, load the archive
        // If we're in the archive mailbox and we're unarchiving, load the inbox
        // Otherwise, stay in the current mailbox or go to inbox for detail view
        if (currentMailbox === 'sent' && !currentStatus) {
          load_mailbox('archive');
        } else if (currentMailbox === 'archive' && currentStatus) {
          load_mailbox('inbox');
        } else if (currentMailbox) {
          load_mailbox(currentMailbox);
        } else {
          load_mailbox('inbox');
        }
      } else {
        console.error('Failed to update archive status');
      }
    });
  }

  // Example of adding event listener for archive button
  document.querySelector('#emails-view').addEventListener('click', event => {
    if (event.target.id === 'archive') {
      const email_id = event.target.dataset.emailId;
      const currentStatus = event.target.dataset.archived === 'true';
      const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
      toggleArchive(email_id, currentStatus, currentMailbox);
    }
  });

  function compose_email(email = null) {
    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Update the heading to match the button text
    document.querySelector('#compose-view h3').textContent = 'New Email';

    // Clear out composition fields and draft ID
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
    document.querySelector('#draft-id').value = '';

    // If an email object is provided, fill the form with it
    if (email) {
      document.querySelector('#compose-recipients').value = email.recipients.join(', ');
      document.querySelector('#compose-subject').value = email.subject;
      document.querySelector('#compose-body').value = email.body;
      
      // If this is a draft, store its ID
      if (email.is_draft) {
        document.querySelector('#draft-id').value = email.id;
        document.querySelector('#compose-view h3').textContent = 'Edit Draft';
      }
    }

    // Hide batch actions when composing
    document.querySelector('#batch-actions').style.display = 'none';
  }

  function load_mailbox(mailbox) {
    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#compose-view').style.display = 'none';
    
    // Hide email view if it exists
    const emailView = document.querySelector('#email-view');
    if (emailView) {
      emailView.style.display = 'none';
    }

    // Set data attribute for current mailbox
    document.querySelector('#emails-view').dataset.mailbox = mailbox;

    // Show the mailbox name and add select all checkbox
    document.querySelector('#emails-view').innerHTML = `
      <div class="mailbox-header">
        <h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>
        <div class="select-all-container">
          <input type="checkbox" id="select-all" class="email-checkbox">
          <label for="select-all">Select All</label>
        </div>
      </div>
    `;

    // Add event listener for select all checkbox
    const selectAllCheckbox = document.querySelector('#select-all');
    selectAllCheckbox.addEventListener('change', function() {
      const checkboxes = document.querySelectorAll('.email-checkbox:not(#select-all)');
      checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
      });
      
      // Show or hide batch actions based on selection
      updateBatchActionsVisibility();
    });

    // Fetch emails for the selected mailbox
    fetch(`/emails/${mailbox}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(emails => {
      // Display each email
      emails.forEach(email => {
        const emailDiv = document.createElement('div');
        emailDiv.className = 'email';
        
        // Add checkbox for selection
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'email-checkbox';
        checkbox.dataset.emailId = email.id;
        checkbox.addEventListener('change', updateBatchActionsVisibility);
        
        emailDiv.appendChild(checkbox);
        
        // Create inner content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'email-content';
        contentDiv.innerHTML = `<strong>${email.sender}</strong> ${email.subject} <span class="timestamp">${email.timestamp}</span>`;
        
        emailDiv.appendChild(contentDiv);
        emailDiv.style.backgroundColor = email.read ? 'lightgray' : 'white';

        // For drafts, clicking should open the compose view with the draft
        if (mailbox === 'drafts') {
          contentDiv.addEventListener('click', () => {
            fetch(`/emails/${email.id}`)
              .then(response => response.json())
              .then(draft => compose_email(draft));
          });
        } else {
          // Make content area clickable for viewing email for non-drafts
          contentDiv.addEventListener('click', () => view_email(email.id));
        }

        // Create action buttons based on mailbox
        if (mailbox !== 'drafts') {
          // Create archive button for non-draft emails
          const archiveButton = document.createElement('button');
          archiveButton.innerHTML = email.archived ? 'Unarchive' : 'Archive';
          archiveButton.className = 'btn btn-sm btn-outline-primary archive-btn';
          archiveButton.id = 'archive';
          archiveButton.dataset.emailId = email.id;
          archiveButton.dataset.archived = email.archived;
          
          // Ensure click event doesn't propagate
          archiveButton.addEventListener('click', function(event) {
              event.stopPropagation();
              toggleArchive(email.id, email.archived, mailbox);
          });
          
          emailDiv.appendChild(archiveButton);
        } else {
          // For drafts, add edit and delete buttons
          const editButton = document.createElement('button');
          editButton.innerHTML = 'Edit';
          editButton.className = 'btn btn-sm btn-outline-primary';
          editButton.addEventListener('click', function(event) {
            event.stopPropagation();
            fetch(`/emails/${email.id}`)
              .then(response => response.json())
              .then(draft => compose_email(draft));
          });
          
          const deleteButton = document.createElement('button');
          deleteButton.innerHTML = 'Delete';
          deleteButton.className = 'btn btn-sm btn-outline-danger';
          deleteButton.addEventListener('click', function(event) {
            event.stopPropagation();
            if (confirm('Are you sure you want to delete this draft?')) {
              fetch(`/emails/${email.id}`, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCSRFToken()
                }
              })
              .then(() => load_mailbox('drafts'))
              .catch(error => {
                console.error('Error deleting draft:', error);
                alert('Failed to delete draft. Please try again.');
              });
            }
          });
          
          emailDiv.appendChild(editButton);
          emailDiv.appendChild(deleteButton);
        }
        
        document.querySelector('#emails-view').appendChild(emailDiv);
      });
    })
    .catch(error => {
        console.error('Error loading mailbox:', error);
        document.querySelector('#emails-view').innerHTML = `
            <h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>
            <div class="alert alert-danger">Failed to load emails. Please check your connection and try again.</div>
        `;
    });
  }

  function view_email(email_id) {
    // First, make sure we have the email-view element in the DOM
    // Show email view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';
    
    // Check if email-view exists, if not create it
    let emailView = document.querySelector('#email-view');
    if (!emailView) {
      emailView = document.createElement('div');
      emailView.id = 'email-view';
      document.querySelector('.container').appendChild(emailView);
    }
    
    // Make sure the email view is displayed
    emailView.style.display = 'block';
    
    // Fetch the email content
    fetch(`/emails/${email_id}`)
      .then(response => response.json())
      .then(email => {
        // Clear previous content
        emailView.innerHTML = '';
        
        // Create header elements with sender, recipients, subject, timestamp
        const header = document.createElement('div');
        header.className = 'email-header';
        header.innerHTML = `
          <p><strong>From:</strong> ${email.sender}</p>
          <p><strong>To:</strong> ${email.recipients.join(', ')}</p>
          <p><strong>Subject:</strong> ${email.subject}</p>
          <p><strong>Timestamp:</strong> ${email.timestamp}</p>
        `;
        emailView.appendChild(header);
        
        // Create buttons for reply, etc.
        const actions = document.createElement('div');
        actions.className = 'email-actions';
        actions.innerHTML = `
          <button class="btn btn-primary" id="reply-button" data-email-id="${email.id}">Reply</button>
          <button class="btn btn-primary" id="archive-button">${email.archived ? 'Unarchive' : 'Archive'}</button>
        `;
        emailView.appendChild(actions);
        
        // Add event listener for reply button after creating it
        document.querySelector('#reply-button').addEventListener('click', function() {
          compose_reply(email);
        });
        
        // Add event listener for archive button
        document.querySelector('#archive-button').addEventListener('click', function() {
          const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
          toggleArchive(email.id, email.archived, currentMailbox);
        });
        
        // Create the body content with properly formatted replies
        const bodyContent = document.createElement('div');
        bodyContent.className = 'email-body';
        
        // Process the email body for display
        let formattedHtml = '';
        
        // First, ensure proper line breaks in the original content
        let formattedBody = email.body;
        
        // Replace the regex pattern to better detect reply headers
        const sections = formattedBody.split(/(\s*On\s+.*?wrote:\s*)/g);
        
        // Process each section with proper spacing
        for (let i = 0; i < sections.length; i++) {
          const section = sections[i];
          
          if (section.match(/\s*On\s+.*?wrote:\s*/)) {
            // This is a header for a quoted section
            formattedHtml += `<div class="quote-header">${section.replace(/\n/g, '<br>')}</div>`;
          } else if (i > 0) {
            // This is quoted content - ensure proper spacing
            formattedHtml += `<div class="email-quote">${section.replace(/\n/g, '<br>')}</div>`;
          } else {
            // This is the new message content
            formattedHtml += `<div>${section.replace(/\n/g, '<br>')}</div>`;
          }
        }
        
        bodyContent.innerHTML = formattedHtml;
        emailView.appendChild(bodyContent);
        
        // Mark as read if needed
        if (!email.read) {
          fetch(`/emails/${email.id}`, {
            method: 'PUT',
            body: JSON.stringify({ read: true }),
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCSRFToken()
            }
          });
        }
        
        // Hide batch actions when viewing a single email
        if (document.querySelector('#batch-actions')) {
          document.querySelector('#batch-actions').style.display = 'none';
        }
      });
  }

  function reply_email(email) {
    // Show compose view and hide other views
    compose_reply(email);
  }

  function compose_reply(email) {
    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';
    document.querySelector('#email-view').style.display = 'none';

    // Format the recipients field (to the sender of the email being replied to)
    document.querySelector('#compose-recipients').value = email.sender;
    
    // Format the subject line with "Re: " prefix if it doesn't already have one
    let subject = email.subject;
    if (!subject.startsWith('Re: ')) {
      subject = 'Re: ' + subject;
    }
    document.querySelector('#compose-subject').value = subject;
    
    // Format the reply message with proper spacing
    const timestamp = new Date(email.timestamp).toLocaleString();
    
    // Clean up and format the existing body content for better readability
    let originalBody = email.body.trim();
    
    // Format any existing quotes properly
    originalBody = originalBody.replace(/On\s+(.*?)wrote:\s*/g, '\nOn $1wrote:\n');
    
    // Ensure double line breaks before each quote header
    originalBody = originalBody.replace(/([^\n])\s*(On\s+.*?wrote:)/g, '$1\n\n$2');
    
    // Create the final template with proper spacing
    const replyTemplate = `\n\nOn ${timestamp}, ${email.sender} wrote:\n${originalBody}`;
    
    document.querySelector('#compose-body').value = replyTemplate;
    
    // Set focus to the beginning of the body field
    const bodyField = document.querySelector('#compose-body');
    bodyField.focus();
    bodyField.setSelectionRange(0, 0);
  }

  // New functions for batch operations
  function getSelectedEmailIds() {
    const selectedCheckboxes = document.querySelectorAll('.email-checkbox:checked:not(#select-all)');
    return Array.from(selectedCheckboxes).map(checkbox => checkbox.dataset.emailId);
  }
  
  function updateBatchActionsVisibility() {
    const selectedEmails = getSelectedEmailIds();
    document.querySelector('#batch-actions').style.display = selectedEmails.length > 0 ? 'block' : 'none';
    
    // Update button text based on the current mailbox
    const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
    const batchArchiveButton = document.querySelector('#batch-archive');
    
    if (currentMailbox === 'archive') {
      batchArchiveButton.textContent = 'Unarchive Selected';
    } else {
      batchArchiveButton.textContent = 'Archive Selected';
    }
  }
  
  function batchArchive() {
    const selectedIds = getSelectedEmailIds();
    const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
    const toArchive = currentMailbox !== 'archive';
    
    // Create a promise for each email to archive/unarchive
    const promises = selectedIds.map(id => {
      return fetch(`/emails/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ archived: toArchive }),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        }
      });
    });
    
    // Wait for all operations to complete
    Promise.all(promises)
      .then(() => {
        // Reload current mailbox
        load_mailbox(currentMailbox);
      })
      .catch(error => {
        console.error('Error performing batch archive:', error);
        alert('Failed to archive/unarchive some emails. Please try again.');
      });
  }
  
  function batchMarkReadStatus(isRead) {
    const selectedIds = getSelectedEmailIds();
    const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
    
    // Create a promise for each email to mark read/unread
    const promises = selectedIds.map(id => {
      return fetch(`/emails/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ read: isRead }),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        }
      });
    });
    
    // Wait for all operations to complete
    Promise.all(promises)
      .then(() => {
        // Reload current mailbox
        load_mailbox(currentMailbox);
      })
      .catch(error => {
        console.error('Error marking emails as read/unread:', error);
        alert('Failed to update some emails. Please try again.');
      });
  }
  
  function batchDelete() {
    // Confirm before deleting
    if (!confirm('Are you sure you want to delete the selected emails?')) {
      return;
    }
    
    const selectedIds = getSelectedEmailIds();
    const currentMailbox = document.querySelector('#emails-view').dataset.mailbox;
    
    // You'll need to add a delete endpoint on the server
    // For now, I'll just archive them as a placeholder
    const promises = selectedIds.map(id => {
      return fetch(`/emails/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ archived: true }),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        }
      });
    });
    
    // Wait for all operations to complete
    Promise.all(promises)
      .then(() => {
        // Reload current mailbox
        load_mailbox(currentMailbox);
      })
      .catch(error => {
        console.error('Error deleting emails:', error);
        alert('Failed to delete some emails. Please try again.');
      });
  }

  // Example of responsive JavaScript
  window.addEventListener('resize', function() {
    // Determine current viewport width
    const viewportWidth = window.innerWidth;
    
    // Adjust behavior based on screen size
    if (viewportWidth < 768) {
      // Mobile behavior
      enableMobileNavigation();
    } else {
      // Desktop behavior
      enableDesktopNavigation();
    }
  });

  // Run once on page load
  document.addEventListener('DOMContentLoaded', function() {
    const viewportWidth = window.innerWidth;
    if (viewportWidth < 768) {
      enableMobileNavigation();
    } else {
      enableDesktopNavigation();
    }
  });
});