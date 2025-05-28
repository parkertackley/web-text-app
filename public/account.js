console.log('GLOBAL USER', globaluser);
//document.getElementById('user-account').innerHTML = `<h3>Hello, ${globaluser}!</h3>`

// Displaying hello message after page loads
document.addEventListener('DOMContentLoaded', function() {
    fetch('/get-username', {
        method: 'GET',
        credentials: 'include'  // Ensures cookies are sent with the request
    })
    .then(response => response.json())
    .then(data => {
        if (data.username) {
            document.getElementById('user-account').innerHTML = `<h3>Hello, ${data.username}!</h3>`;
        }
    })
    .catch(error => console.error('Error getting username', error));
});



// Update Username
document.getElementById('update-username-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevents the redirect

    const formData = new FormData(this);
    fetch('/update-username', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
        alert(data.message);
        window.location.href = '/account'; // Redirect to the account page
    }).catch(error => console.error('Error:', error));
});


// Password Update
document.getElementById('change-password-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevents the redirect

    const formData = new FormData(this);
    fetch('/change-password', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
        alert(data.message);
        window.location.href = '/account'; // Redirect to the account page
    }).catch(error => console.error('Error:', error));
});