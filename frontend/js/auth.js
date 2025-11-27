/**
 * Authentication Module
 * Handles secret key authentication
 */

const AUTH_STORAGE_KEY = 'slack_memories_authenticated';

/**
 * Check if user is already authenticated
 */
function checkAuthentication() {
    const isAuthenticated = sessionStorage.getItem(AUTH_STORAGE_KEY) === 'true';
    
    if (isAuthenticated) {
        showMainContent();
    } else {
        showSecretCover();
        // Focus input after a short delay
        setTimeout(() => {
            const secretInput = document.getElementById('secretKeyInput');
            if (secretInput) secretInput.focus();
        }, 200);
    }
}

/**
 * Show secret cover screen
 */
function showSecretCover() {
    const cover = document.getElementById('secretCover');
    const mainContent = document.getElementById('mainContent');
    
    if (cover) cover.classList.remove('d-none');
    if (mainContent) mainContent.classList.add('d-none');
    
    // Focus on input
    setTimeout(() => {
        const secretInput = document.getElementById('secretKeyInput');
        if (secretInput) {
            secretInput.focus();
        }
    }, 100);
}

/**
 * Show main content
 */
function showMainContent() {
    const cover = document.getElementById('secretCover');
    const mainContent = document.getElementById('mainContent');
    
    if (cover) cover.classList.add('d-none');
    if (mainContent) mainContent.classList.remove('d-none');
}

/**
 * Handle secret key submission
 */
async function handleSecretSubmit(e) {
    if (e) {
        e.preventDefault();
    }
    
    const secretInput = document.getElementById('secretKeyInput');
    const submitBtn = document.getElementById('secretSubmitBtn');
    const spinner = document.getElementById('secretSpinner');
    const btnText = submitBtn?.querySelector('.btn-text');
    const errorDiv = document.getElementById('secretError');
    const successDiv = document.getElementById('secretSuccess');
    
    if (!secretInput) return;
    
    const secretKey = secretInput.value.trim();
    
    // Hide previous messages
    if (errorDiv) errorDiv.classList.add('d-none');
    if (successDiv) successDiv.classList.add('d-none');
    
    if (!secretKey) {
        if (errorDiv) {
            errorDiv.classList.remove('d-none');
        }
        return;
    }
    
    // Disable form
    if (submitBtn) {
        submitBtn.disabled = true;
        if (btnText) btnText.textContent = 'Verifying...';
        if (spinner) spinner.classList.remove('d-none');
    }
    secretInput.disabled = true;
    
    try {
        const result = await verifySecretKey(secretKey);
        
        if (result.success) {
            // Store authentication state
            sessionStorage.setItem(AUTH_STORAGE_KEY, 'true');
            
            // Show success message
            if (successDiv) {
                successDiv.classList.remove('d-none');
            }
            
            // Hide cover and show main content after a delay
            setTimeout(() => {
                showMainContent();
            }, 1500);
        } else {
            throw new Error('Invalid key');
        }
    } catch (error) {
        // Show error
        if (errorDiv) {
            errorDiv.classList.remove('d-none');
        }
        
        // Re-enable form
        if (submitBtn) {
            submitBtn.disabled = false;
            if (btnText) btnText.textContent = 'Unlock';
            if (spinner) spinner.classList.add('d-none');
        }
        secretInput.disabled = false;
        secretInput.value = '';
        secretInput.focus();
    }
}

/**
 * Initialize authentication
 */
function initAuth() {
    // Check authentication on load
    checkAuthentication();
    
    // Setup form submission
    const secretForm = document.getElementById('secretForm');
    if (secretForm) {
        secretForm.addEventListener('submit', handleSecretSubmit);
    }
    
    // Focus on input when cover is shown
    if (document.getElementById('secretCover') && !document.getElementById('secretCover').classList.contains('d-none')) {
        setTimeout(() => {
            const secretInput = document.getElementById('secretKeyInput');
            if (secretInput) secretInput.focus();
        }, 100);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

