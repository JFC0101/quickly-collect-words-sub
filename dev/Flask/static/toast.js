function showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.className = 'toast show';
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');  // Remove 'show' to hide toast
        document.body.removeChild(toast);  // Optionally remove the toast from the DOM
    }, 3300);  // Toast显示时长
}


