// Admin Users Management JavaScript

let storesList = [];

// Store current user ID (will be set from template)
let currentUserId = null;

// Load users on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get current user ID from meta tag or data attribute
    const userIdMeta = document.querySelector('meta[name="current-user-id"]');
    if (userIdMeta) {
        currentUserId = parseInt(userIdMeta.content);
    }
    
    loadUsers();
    loadStores();
    
    // Handle role change in add user form
    document.getElementById('addUserRole').addEventListener('change', function() {
        toggleStoreSelect('addUserRole', 'addUserStore', 'storeSelectContainer');
    });
    
    // Handle role change in edit user form
    document.getElementById('editUserRole').addEventListener('change', function() {
        toggleStoreSelect('editUserRole', 'editUserStore', 'editStoreSelectContainer');
    });
});

// Load all users
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        if (!response.ok) {
            throw new Error('שגיאה בטעינת משתמשים');
        }
        const data = await response.json();
        displayUsers(data.users);
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersTableBody').innerHTML = 
            '<tr><td colspan="8" class="text-center text-danger">שגיאה בטעינת משתמשים</td></tr>';
    }
}

// Load stores for dropdown
async function loadStores() {
    try {
        const response = await fetch('/api/filters');
        const data = await response.json();
        storesList = data.stores;
        
        // Populate store selects
        populateStoreSelect('addUserStore', storesList);
        populateStoreSelect('editUserStore', storesList);
    } catch (error) {
        console.error('Error loading stores:', error);
    }
}

// Populate store select dropdown
function populateStoreSelect(selectId, stores) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">בחר סניף...</option>';
    stores.forEach(store => {
        const option = document.createElement('option');
        option.value = store.store_id;
        option.textContent = `${store.store_name} (${store.city})`;
        select.appendChild(option);
    });
}

// Toggle store select visibility based on role
function toggleStoreSelect(roleSelectId, storeSelectId, containerId) {
    const role = document.getElementById(roleSelectId).value;
    const container = document.getElementById(containerId);
    
    if (role === 'store_manager') {
        container.style.display = 'block';
        document.getElementById(storeSelectId).required = true;
    } else {
        container.style.display = 'none';
        document.getElementById(storeSelectId).required = false;
        document.getElementById(storeSelectId).value = '';
    }
}

// Display users in table
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    // Update count
    const countElement = document.getElementById('usersCount');
    if (countElement) {
        countElement.textContent = `${users ? users.length : 0} משתמשים`;
    }
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">אין משתמשים</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.user_id}</td>
            <td>${user.username}</td>
            <td>
                <span class="badge ${user.role === 'admin' ? 'bg-danger' : 'bg-primary'}">
                    ${user.role === 'admin' ? 'מנהל מערכת' : 'מנהל סניף'}
                </span>
            </td>
            <td>${user.store_name || 'N/A'}</td>
            <td>${user.created_at || 'N/A'}</td>
            <td>${user.last_login || 'מעולם לא'}</td>
            <td>
                <span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${user.is_active ? 'פעיל' : 'לא פעיל'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editUser(${user.user_id})">
                    <i class="bi bi-pencil"></i> ערוך
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.user_id}, '${user.username}')" ${user.user_id === currentUserId ? 'disabled title="לא ניתן למחוק את המשתמש שלך"' : ''}>
                    <i class="bi bi-trash"></i> מחק
                </button>
            </td>
        </tr>
    `).join('');
}

// Add new user
async function addUser() {
    const form = document.getElementById('addUserForm');
    const formData = new FormData(form);
    
    const userData = {
        username: formData.get('username'),
        password: formData.get('password'),
        role: formData.get('role'),
        store_id: formData.get('role') === 'store_manager' ? parseInt(formData.get('store_id')) : null
    };
    
    if (userData.role === 'store_manager' && !userData.store_id) {
        showNotification('נא לבחור סניף למנהל סניף', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('משתמש נוסף בהצלחה!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
            form.reset();
            loadUsers();
        } else {
            showNotification('שגיאה: ' + (data.error || 'שגיאה ביצירת משתמש'), 'error');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        alert('שגיאה ביצירת משתמש');
    }
}

// Edit user
async function editUser(userId) {
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        const user = data.users.find(u => u.user_id === userId);
        
        if (!user) {
            showNotification('משתמש לא נמצא', 'error');
            return;
        }
        
        // Populate edit form
        document.getElementById('editUserId').value = user.user_id;
        document.getElementById('editUsername').value = user.username;
        document.getElementById('editUserRole').value = user.role;
        document.getElementById('editUserStore').value = user.store_id || '';
        document.getElementById('editIsActive').checked = user.is_active;
        
        // Toggle store select
        toggleStoreSelect('editUserRole', 'editUserStore', 'editStoreSelectContainer');
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading user:', error);
        alert('שגיאה בטעינת פרטי משתמש');
    }
}

// Update user
async function updateUser() {
    const form = document.getElementById('editUserForm');
    const formData = new FormData(form);
    const userId = parseInt(formData.get('user_id'));
    
    const userData = {
        username: formData.get('username'),
        role: formData.get('role'),
        store_id: formData.get('role') === 'store_manager' ? parseInt(formData.get('store_id')) : null,
        is_active: document.getElementById('editIsActive').checked
    };
    
    // Only include password if provided
    const password = formData.get('password');
    if (password) {
        userData.password = password;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('משתמש עודכן בהצלחה!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
            loadUsers();
        } else {
            showNotification('שגיאה: ' + (data.error || 'שגיאה בעדכון משתמש'), 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        alert('שגיאה בעדכון משתמש');
    }
}

// Delete user
async function deleteUser(userId, username) {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את המשתמש "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('משתמש נמחק בהצלחה!', 'success');
            loadUsers();
        } else {
            showNotification('שגיאה: ' + (data.error || 'שגיאה במחיקת משתמש'), 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('שגיאה במחיקת משתמש');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification-toast');
    if (existing) {
        existing.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show notification-toast`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Change password
function showChangePasswordModal() {
    const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
    modal.show();
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showNotification('סיסמאות לא תואמות', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showNotification('סיסמה חייבת להכיל לפחות 6 תווים', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('סיסמה שונתה בהצלחה!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
            document.getElementById('changePasswordForm').reset();
        } else {
            showNotification('שגיאה: ' + (data.error || 'שגיאה בשינוי סיסמה'), 'error');
        }
    } catch (error) {
        console.error('Error changing password:', error);
        alert('שגיאה בשינוי סיסמה');
    }
}

