// Main JavaScript for Secure File Storage System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize file upload area
    initFileUpload();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize file share functionality
    initFileSharing();
    
    // Initialize blockchain explorer
    initBlockchainExplorer();
});

// File Upload Functionality
function initFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                const fileSize = formatFileSize(fileInput.files[0].size);
                
                document.getElementById('selected-file-name').textContent = fileName;
                document.getElementById('selected-file-size').textContent = fileSize;
                document.getElementById('file-preview').classList.remove('d-none');
            }
        });
        
        // Drag and drop support
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('border-primary');
        });
        
        uploadArea.addEventListener('dragleave', function() {
            uploadArea.classList.remove('border-primary');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('border-primary');
            
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                const fileName = e.dataTransfer.files[0].name;
                const fileSize = formatFileSize(e.dataTransfer.files[0].size);
                
                document.getElementById('selected-file-name').textContent = fileName;
                document.getElementById('selected-file-size').textContent = fileSize;
                document.getElementById('file-preview').classList.remove('d-none');
            }
        });
    }
}

// Initialize Bootstrap tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// File sharing functionality
function initFileSharing() {
    const shareButtons = document.querySelectorAll('.share-file-btn');
    
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-file-id');
            document.getElementById('file-id-input').value = fileId;
        });
    });
}

// Blockchain explorer functionality
function initBlockchainExplorer() {
    const blockDetails = document.querySelectorAll('.block-details-toggle');
    
    blockDetails.forEach(detail => {
        detail.addEventListener('click', function() {
            const blockId = this.getAttribute('data-block-id');
            const detailsElement = document.getElementById('block-details-' + blockId);
            
            if (detailsElement) {
                if (detailsElement.classList.contains('d-none')) {
                    detailsElement.classList.remove('d-none');
                    this.textContent = 'Hide Details';
                } else {
                    detailsElement.classList.add('d-none');
                    this.textContent = 'Show Details';
                }
            }
        });
    });
}

// Format file size (bytes to KB, MB, etc.)
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Password strength checker
function checkPasswordStrength(password) {
    let strength = 0;
    const feedback = document.getElementById('password-feedback');
    
    if (password.length >= 12) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    const strengthBar = document.getElementById('password-strength');
    if (strengthBar) {
        strengthBar.style.width = (strength * 20) + '%';
        
        switch(strength) {
            case 0:
            case 1:
                strengthBar.className = 'progress-bar bg-danger';
                if (feedback) feedback.textContent = 'Very weak password';
                break;
            case 2:
                strengthBar.className = 'progress-bar bg-warning';
                if (feedback) feedback.textContent = 'Weak password';
                break;
            case 3:
                strengthBar.className = 'progress-bar bg-info';
                if (feedback) feedback.textContent = 'Moderate password';
                break;
            case 4:
                strengthBar.className = 'progress-bar bg-primary';
                if (feedback) feedback.textContent = 'Strong password';
                break;
            case 5:
                strengthBar.className = 'progress-bar bg-success';
                if (feedback) feedback.textContent = 'Very strong password';
                break;
        }
    }
    
    return strength;
} 