/**
 * Utility functions for handling visualization images
 */

// Save an image to disk
function saveImage(imgElement, filenamePrefix) {
    if (imgElement && imgElement.src) {
        const link = document.createElement('a');
        link.href = imgElement.src;
        link.download = `${filenamePrefix}_${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Copy an image to clipboard
async function copyImageToClipboard(imgElement, buttonElement) {
    if (imgElement && imgElement.src) {
        try {
            // Create a temporary canvas to handle the image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            // Set up a promise to wait for the image to load
            const imageLoaded = new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
                img.crossOrigin = "Anonymous"; // Handle CORS issues
                img.src = imgElement.src;
            });
            
            await imageLoaded;
            
            // Set canvas dimensions to match the image
            canvas.width = img.width;
            canvas.height = img.height;
            
            // Draw the image on the canvas
            ctx.drawImage(img, 0, 0);
            
            // Try modern Clipboard API first
            if (navigator.clipboard && navigator.clipboard.write) {
                // Convert the canvas to a blob
                const blob = await new Promise(resolve => canvas.toBlob(resolve));
                
                // Use the Clipboard API to copy the image
                await navigator.clipboard.write([
                    new ClipboardItem({ 'image/png': blob })
                ]);
            } else {
                // Fallback for browsers that don't support clipboard.write
                // Open the image in a new tab where the user can copy it manually
                const dataUrl = canvas.toDataURL('image/png');
                const newTab = window.open();
                newTab.document.write(`
                    <html>
                    <head>
                        <title>Copy Image</title>
                        <style>
                            body { display: flex; justify-content: center; align-items: center; flex-direction: column; min-height: 100vh; margin: 0; }
                            img { max-width: 90%; max-height: 70vh; }
                            p { font-family: Arial, sans-serif; margin-top: 20px; }
                        </style>
                    </head>
                    <body>
                        <img src="${dataUrl}" alt="Visualization">
                        <p>Right-click on the image and select "Copy Image" to copy it to your clipboard</p>
                    </body>
                    </html>
                `);
                newTab.document.close();
            }
            
            // Provide user feedback
            if (buttonElement) {
                const originalContent = buttonElement.innerHTML;
                buttonElement.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
                setTimeout(() => {
                    buttonElement.innerHTML = originalContent;
                }, 2000);
            }
            
            return true;
        } catch (error) {
            console.error('Failed to copy image: ', error);
            
            if (buttonElement) {
                const originalContent = buttonElement.innerHTML;
                buttonElement.innerHTML = '<i class="fas fa-times me-1"></i>Failed';
                setTimeout(() => {
                    buttonElement.innerHTML = originalContent;
                }, 2000);
            }
            
            return false;
        }
    }
    return false;
} 