// Ensure this script only runs when the page has fully loaded
window.onload = function() {
    // Handle toast message
    const urlParams = new URLSearchParams(window.location.search);
    const toastMessage = urlParams.get('toast');
    if (toastMessage) {
        showToast(decodeURIComponent(toastMessage));
        // Remove 'toast' parameter from URL
        urlParams.delete('toast');
        window.history.replaceState({}, document.title, `${window.location.pathname}?${urlParams.toString()}`);
    }

    // Handle client-side error messages
    const wordForm = document.getElementById('word-form');
    const errorMessage = document.getElementById('error-message');
    const regex = /^[A-Za-z,]+$/;

    wordForm.addEventListener('submit', function(event) {
        const wordInput = document.getElementById('word').value;

        if (!regex.test(wordInput)) {
            event.preventDefault(); // Prevent form submission
            errorMessage.style.display = 'block'; // Show error message
        } else {
            errorMessage.style.display = 'none'; // Hide error message
        }
    });
};

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add("show");
    
    // Remove 'show' class after animation duration
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3300); // Adjust this value if needed
}



//filter popup
function openModal() {
    document.getElementById("filterModal").style.display = "block";
}

function closeModal() {
    document.getElementById("filterModal").style.display = "none";
}

window.onclick = function(event) {
    var modal = document.getElementById("filterModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
}