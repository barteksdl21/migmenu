document.addEventListener('DOMContentLoaded', function() {
    const deleteLinks = document.querySelectorAll('.delete-menu');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const menuLink = this.getAttribute('data-link');
            if (confirm('Are you sure you want to delete this menu?')) {
                deleteMenu(menuLink);
            }
        });
    });

    function deleteMenu(link) {
        fetch(`/delete/${link}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'  // If you're using CSRF protection
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Menu deleted successfully!');
                location.reload();  // Reload the page to reflect the changes
            } else {
                alert('Error deleting menu: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the menu.');
        });
    }
});