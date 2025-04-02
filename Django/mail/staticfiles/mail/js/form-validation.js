'use strict';

/**
 * Form validation utility
 * Handles validation of form inputs and enables/disables submit buttons
 */
const FormValidator = {
    /**
     * Initialize validation on a form
     * @param {HTMLFormElement} form - The form to validate
     */
    init: function(form) {
        if (!form || form.tagName !== 'FORM') return;
        
        // Store all inputs that should be validated
        const inputs = Array.from(form.querySelectorAll('input:not([type="submit"]):not([type="button"]), select, textarea'))
            .filter(input => !input.disabled && !input.readOnly);
        
        // Find submit buttons
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        
        // Set initial state of submit buttons
        this.updateSubmitButtons(form, submitButtons);
        
        // Add validation to each input
        inputs.forEach(input => {
            // Set initial validation state
            this.validateInput(input);
            
            // Add event listeners for real-time validation
            input.addEventListener('input', () => {
                this.validateInput(input);
                this.updateSubmitButtons(form, submitButtons);
            });
            
            input.addEventListener('blur', () => {
                this.validateInput(input, true);
                this.updateSubmitButtons(form, submitButtons);
            });
        });
        
        // Update validation on form submission attempt
        form.addEventListener('submit', (event) => {
            const isValid = this.validateForm(form);
            if (!isValid) {
                event.preventDefault();
            }
        });
    },
    
    /**
     * Validate all inputs in a form
     * @param {HTMLFormElement} form - The form to validate
     * @returns {boolean} Whether the form is valid
     */
    validateForm: function(form) {
        const inputs = Array.from(form.querySelectorAll('input:not([type="submit"]):not([type="button"]), select, textarea'))
            .filter(input => !input.disabled && !input.readOnly);
        
        // Validate each input with showError=true to display all error messages
        inputs.forEach(input => this.validateInput(input, true));
        
        // Focus the first invalid input
        const firstInvalid = inputs.find(input => !input.validity.valid);
        if (firstInvalid) {
            firstInvalid.focus();
        }
        
        return form.checkValidity();
    },
    
    /**
     * Validate a single input field and show/hide error message
     * @param {HTMLElement} input - The input to validate
     * @param {boolean} showError - Whether to show error message
     * @returns {boolean} Whether the input is valid
     */
    validateInput: function(input, showError = false) {
        // Skip validation for disabled or readonly inputs
        if (input.disabled || input.readOnly) return true;
        
        let isValid = input.validity.valid;
        
        // Additional validation for email fields
        if (input.type === 'email' && input.value) {
            const emailValid = this.validateEmail(input.value);
            if (!emailValid) {
                input.setCustomValidity("Please enter a valid email address (e.g., user@example.com)");
                isValid = false;
            } else {
                input.setCustomValidity("");
            }
        }
        
        // Add appropriate class based on validation state
        if (isValid) {
            input.classList.remove('invalid');
            input.classList.add('valid');
        } else {
            input.classList.remove('valid');
            input.classList.add('invalid');
        }
        
        // Handle error message display
        this.updateErrorMessage(input, showError);
        
        return isValid;
    },
    
    /**
     * Create or update error message for an input
     * @param {HTMLElement} input - The input element
     * @param {boolean} showError - Whether to show the error
     */
    updateErrorMessage: function(input, showError) {
        // Find existing error message or create a new one
        let errorElement = input.nextElementSibling;
        if (!errorElement || !errorElement.classList.contains('error-message')) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            input.parentNode.insertBefore(errorElement, input.nextSibling);
        }
        
        if (!input.validity.valid && showError) {
            // Show appropriate error message based on validation error
            errorElement.textContent = this.getErrorMessage(input);
            errorElement.style.display = 'block';
        } else {
            // Hide error message
            errorElement.style.display = 'none';
        }
    },
    
    /**
     * Generate appropriate error message based on validation state
     * @param {HTMLElement} input - The input element
     * @returns {string} Error message
     */
    getErrorMessage: function(input) {
        const validity = input.validity;
        
        if (validity.valueMissing) {
            return 'This field is required';
        } else if (validity.typeMismatch) {
            if (input.type === 'email') {
                return 'Please enter a valid email address';
            } else if (input.type === 'url') {
                return 'Please enter a valid URL';
            }
        } else if (validity.tooShort) {
            return `Please lengthen this text to ${input.minLength} characters or more`;
        } else if (validity.tooLong) {
            return `Please shorten this text to ${input.maxLength} characters or less`;
        } else if (validity.rangeUnderflow) {
            return `Value must be greater than or equal to ${input.min}`;
        } else if (validity.rangeOverflow) {
            return `Value must be less than or equal to ${input.max}`;
        } else if (validity.patternMismatch) {
            return input.title || 'Please match the requested format';
        }
        
        return 'Please enter a valid value';
    },
    
    /**
     * Update submit buttons based on form validity
     * @param {HTMLFormElement} form - The form containing the buttons
     * @param {NodeList} submitButtons - The submit buttons to update
     */
    updateSubmitButtons: function(form, submitButtons) {
        const isValid = form.checkValidity();
        
        // Enable/disable submit buttons based on form validity
        submitButtons.forEach(button => {
            button.disabled = !isValid;
            
            if (isValid) {
                button.classList.remove('disabled');
                button.classList.add('enabled');
            } else {
                button.classList.remove('enabled');
                button.classList.add('disabled');
            }
        });
    },
    
    /**
     * Validate email format
     * @param {string} email - The email to validate
     * @returns {boolean} Whether the email is valid
     */
    validateEmail: function(email) {
        // Regular expression for validating email format
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(email);
    }
};

// Initialize validation on all forms when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => FormValidator.init(form));
}); 