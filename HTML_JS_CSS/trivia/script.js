// Multiple choice question logic
document.querySelectorAll('.choice').forEach(button => {
    button.addEventListener('click', function() {
        const feedback = document.getElementById('feedback1');
        if (this.dataset.answer === 'correct') {
            this.style.backgroundColor = 'green';
            feedback.textContent = "Correct!";
            feedback.style.color = 'green';
        } else {
            this.style.backgroundColor = 'red';
            feedback.textContent = "Incorrect";
            feedback.style.color = 'red';
        }
    });
});

// Free response question logic
document.getElementById('submit-answer').addEventListener('click', function() {
    const answer = document.getElementById('free-response').value.toLowerCase();
    const feedback = document.getElementById('feedback2');
    if (answer === 'paris') {
        document.getElementById('free-response').style.backgroundColor = 'green';
        feedback.textContent = "Correct!";
        feedback.style.color = 'green';
    } else {
        document.getElementById('free-response').style.backgroundColor = 'red';
        feedback.textContent = "Incorrect";
        feedback.style.color = 'red';
    }
});
