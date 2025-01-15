document.addEventListener('DOMContentLoaded', function() {
    // Add to cart button functionality
    const addToCartButtons = document.querySelectorAll('.btn-add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            fetch(`/add_to_cart/${productId}`, { method: 'GET' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Product added to cart!');
                    } else {
                        alert('Failed to add product to cart.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while adding the product to cart.');
                });
        });
    });

    // Remove from cart button functionality
    const removeFromCartButtons = document.querySelectorAll('.btn-remove-from-cart');
    removeFromCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            fetch(`/remove_from_cart/${productId}`, { method: 'GET' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Product removed from cart!');
                        location.reload();
                    } else {
                        alert('Failed to remove product from cart.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while removing the product from cart.');
                });
        });
    });
});