// static/js/menu_creator.js

let categoryCounter = 0;
let itemCounter = 0;

const dragIcon = '<svg class="drag-handle" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 6H16M8 12H16M8 18H16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function addCategory() {
    categoryCounter++;
    const categoryId = `new-category-${categoryCounter}`;
    const categoryHtml = `
        <div id="${categoryId}" class="category">
            ${dragIcon}
            <div>
                <input type="text" name="categories[${categoryId}][name]" placeholder="Category Name" required>
                <input type="hidden" name="categories[${categoryId}][order]" value="${categoryCounter}">
                <button type="button" onclick="addItem('${categoryId}')">Add Item</button>
                <div class="items-container"></div>
            </div>
        </div>
    `;
    document.getElementById('menuStructure').insertAdjacentHTML('beforeend', categoryHtml);
    makeElementDraggable(document.getElementById(categoryId));
    return categoryId;
}

function addItem(categoryId) {
    itemCounter++;
    const itemId = `new-item-${itemCounter}`;
    const itemHtml = `
        <div class="item" data-item-id="${itemId}">
            ${dragIcon}
            <div>
                <input type="text" name="items[${itemId}][name]" placeholder="Item Name" required>
                <input type="text" name="items[${itemId}][description]" placeholder="Description">
                <input type="number" name="items[${itemId}][price]" placeholder="Price" step="0.01" required>
                <input type="hidden" name="items[${itemId}][order]" value="${itemCounter}">
                <input type="hidden" name="items[${itemId}][category_id]" value="${categoryId}">
            </div>
        </div>
    `;
    document.querySelector(`#${categoryId} .items-container`).insertAdjacentHTML('beforeend', itemHtml);
}

function makeElementDraggable(element) {
    new Sortable(element.querySelector('.items-container'), {
        group: 'shared',
        animation: 150,
        handle: '.drag-handle',
        onEnd: function (evt) {
            updateOrder(evt.to);
            updateCategoryAssignment(evt.item, evt.to);
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
    const categoryId = newContainer.closest('.category').id;
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

document.addEventListener('DOMContentLoaded', function() {
    if (typeof isEditPage === 'undefined' || !isEditPage) {
        // This is the create page, so add initial category and item
        const initialCategoryId = addCategory();
        addItem(initialCategoryId);
    } else {
        // This is the edit page, so just initialize existing elements
        document.querySelectorAll('.category').forEach(makeElementDraggable);
    }

    // Initialize Sortable for the menuStructure
    new Sortable(document.getElementById('menuStructure'), {
        group: 'categories',
        animation: 150,
        handle: '.drag-handle',
        onEnd: function (evt) {
            updateCategoryOrder();
        }
    });
});

// Add event listener to the form submission
document.getElementById('menuForm').addEventListener('submit', function(e) {
    e.preventDefault();
    updateCategoryOrder();
    this.submit();
});