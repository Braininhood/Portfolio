document.addEventListener('DOMContentLoaded', function() {
    const actionSelect = document.getElementById('id_action');
    const fillValueDiv = document.getElementById('fillValueDiv');
    const fillValueInput = document.getElementById('id_value');
    
    if (actionSelect && fillValueDiv && fillValueInput) {
        // Initialize based on current selection
        if (actionSelect.value === 'fill_na') {
            fillValueDiv.style.display = 'block';
            fillValueInput.required = true;
        } else {
            fillValueDiv.style.display = 'none';
            fillValueInput.required = false;
        }
        
        // Handle changes to the selection
        actionSelect.addEventListener('change', function() {
            if (this.value === 'fill_na') {
                fillValueDiv.style.display = 'block';
                fillValueInput.required = true;
            } else {
                fillValueDiv.style.display = 'none';
                fillValueInput.required = false;
                fillValueInput.value = '';
            }
        });
    }
}); 