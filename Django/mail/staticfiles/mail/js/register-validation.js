document.addEventListener('DOMContentLoaded', function() {
  const password = document.getElementById('password');
  const confirmation = document.getElementById('confirmation');
  
  function checkPasswordsMatch() {
    if (password.value !== confirmation.value) {
      confirmation.setCustomValidity("Passwords do not match");
    } else {
      confirmation.setCustomValidity("");
    }
  }
  
  password.addEventListener('change', checkPasswordsMatch);
  confirmation.addEventListener('keyup', checkPasswordsMatch);
}); 