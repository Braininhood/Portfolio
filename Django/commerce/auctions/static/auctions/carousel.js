document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.carousel').forEach(carousel => {
        const images = carousel.querySelectorAll('.carousel-image');
        if (images.length > 0) {
            images[0].style.display = 'block'; // Show the first image
        }
    });
});

function nextImage(carouselId) {
    const carousel = document.getElementById(carouselId);
    const images = carousel.querySelectorAll('.carousel-image');
    let currentIndex = Array.from(images).findIndex(img => img.style.display === 'block');
    images[currentIndex].style.display = 'none'; // Hide current image
    currentIndex = (currentIndex + 1) % images.length; // Move to next image
    images[currentIndex].style.display = 'block'; // Show next image
}

function prevImage(carouselId) {
    const carousel = document.getElementById(carouselId);
    const images = carousel.querySelectorAll('.carousel-image');
    let currentIndex = Array.from(images).findIndex(img => img.style.display === 'block');
    images[currentIndex].style.display = 'none'; // Hide current image
    currentIndex = (currentIndex - 1 + images.length) % images.length; // Move to previous image
    images[currentIndex].style.display = 'block'; // Show previous image
} 