// static/js/menu_creator.js

let categoryCounter = 0;
let itemCounter = 0;

function initializeCounters() {
    const categories = document.querySelectorAll('.category');
    const items = document.querySelectorAll('.item');
    categoryCounter = categories.length;
    itemCounter = items.length;
}

function addCategory() {
    categoryCounter++;
    const categoryId = `new-category-${categoryCounter}`;
    const categoryHtml = `
        <div id="${categoryId}" class="category" draggable="true">
            <input type="text" name="categories[${categoryId}][name]" placeholder="Category Name" required>
            <input type="hidden" name="categories[${categoryId}][order]" value="${categoryCounter}">
            <button type="button" onclick="addItem('${categoryId}')">Add Item</button>
            <div class="items-container"></div>
        </div>
    `;
    document.getElementById('menuStructure').insertAdjacentHTML('beforeend', categoryHtml);
    makeElementDraggable(document.getElementById(categoryId));
}

function addItem(categoryId) {
    itemCounter++;
    const itemId = `new-item-${itemCounter}`;
    const itemHtml = `
        <div class="item" draggable="true" data-item-id="${itemId}">
            <input type="text" name="items[${itemId}][name]" placeholder="Item Name" required>
            <input type="text" name="items[${itemId}][description]" placeholder="Description">
            <input type="number" name="items[${itemId}][price]" placeholder="Price" step="0.01" required>
            <input type="hidden" name="items[${itemId}][order]" value="${itemCounter}">
            <input type="hidden" name="items[${itemId}][category_id]" value="${categoryId.split('-')[1]}">
        </div>
    `;
    document.querySelector(`#${categoryId} .items-container`).insertAdjacentHTML('beforeend', itemHtml);
}

function makeElementDraggable(element) {
    new Sortable(element.querySelector('.items-container'), {
        group: 'shared',
        animation: 150,
        onEnd: function (evt) {
            updateOrder(evt.to);
            updateCategoryAssignment(evt.item, evt.to);
        }
    });

    new Sortable(element.parentNode, {
        group: 'categories',
        animation: 150,
        onEnd: function (evt) {
            updateCategoryOrder();
        }
    });
}

function updateOrder(container) {
    const items = container.children;
    for (let i = 0; i < items.length; i++) {
        const orderInput = items[i].querySelector('input[name$="[order]"]');
        if (orderInput) {
            orderInput.value = i + 1;
        }
    }
}

function updateCategoryAssignment(item, newContainer) {
    const categoryId = newContainer.closest('.category').id.split('-')[1];
    const itemId = item.dataset.itemId;
    const categoryInput = item.querySelector(`input[name="items[${itemId}][category_id]"]`);
    categoryInput.value = categoryId;
}

function updateCategoryOrder() {
    const categories = document.querySelectorAll('.category');
    categories.forEach((category, index) => {
        const orderInput = category.querySelector('input[name$="[order]"]');
        if (orderInput) {
            orderInput.value = index + 1;
        }
    });
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    initializeCounters();
    document.querySelectorAll('.category').forEach(makeElementDraggable);
});

// Add event listener to the form submission
document.getElementById('menuForm').addEventListener('submit', function(e) {
    e.preventDefault();
    updateCategoryOrder();
    this.submit();
});