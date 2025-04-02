document.addEventListener('DOMContentLoaded', function() {
    const recipientsField = document.getElementById('compose-recipients');
    
    if (recipientsField) {
        recipientsField.addEventListener('input', validateRecipients);
        recipientsField.addEventListener('blur', validateRecipients);
    }
    
    function validateRecipients() {
        const value = recipientsField.value.trim();
        
        if (!value) {
            recipientsField.setCustomValidity("Recipients field is required");
            return;
        }
        
        // Split by commas and validate each email
        const emails = value.split(',').map(email => email.trim());
        const invalidEmails = [];
        
        // Regular expression for validating email format
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        // Check each email
        for (const email of emails) {
            if (email && !emailPattern.test(email)) {
                invalidEmails.push(email);
            }
        }
        
        if (invalidEmails.length > 0) {
            recipientsField.setCustomValidity(`Invalid email format: ${invalidEmails.join(', ')}`);
        } else {
            recipientsField.setCustomValidity('');
        }
    }
}); 