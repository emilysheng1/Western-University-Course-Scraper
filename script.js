document.getElementById('subscriptionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const classNumber = document.getElementById('classNumber').value;
    
    fetch('http://127.0.0.1:5000/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email, classNumber: classNumber }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Subscription successful!');
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});
5