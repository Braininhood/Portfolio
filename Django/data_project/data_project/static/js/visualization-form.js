document.addEventListener('DOMContentLoaded', function() {
    const vizTypeSelect = document.getElementById('id_viz_type');
    const yColumnDiv = document.getElementById('id_y_column').closest('.mb-3');
    
    function updateYColumnVisibility() {
        const selectedVizType = vizTypeSelect.value;
        
        if (selectedVizType === 'scatter') {
            yColumnDiv.style.display = 'block';
            document.getElementById('id_y_column').required = true;
        } else if (selectedVizType === 'pie' || selectedVizType === 'histogram') {
            yColumnDiv.style.display = 'none';
            document.getElementById('id_y_column').required = false;
            document.getElementById('id_y_column').value = '';
        } else {
            yColumnDiv.style.display = 'block';
            document.getElementById('id_y_column').required = false;
        }
    }
    
    if (vizTypeSelect) {
        vizTypeSelect.addEventListener('change', updateYColumnVisibility);
        
        // Initial check
        updateYColumnVisibility();
    }
}); 