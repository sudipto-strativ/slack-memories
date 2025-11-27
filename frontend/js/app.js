/**
 * Main Application Logic
 * Coordinates user interactions, API calls, and UI updates
 */

// Application state
let currentChannels = [];
let currentItems = [];

// Debounce function for input handling
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize the application
 */
async function initApp() {
    // Set default date range (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
    
    // Load channels
    await loadChannels();
    
    // Setup event listeners
    setupEventListeners();
    
    // Trigger confetti animation on load
    triggerConfetti();
}

/**
 * Load channels from API and setup search
 */
async function loadChannels() {
    try {
        const channels = await fetchChannels();
        currentChannels = channels;
        setupChannelSearch(channels);
    } catch (error) {
        console.error('Failed to load channels:', error);
        showToast('Failed to load channels. Please refresh the page.', 'error');
    }
}

/**
 * Setup channel search functionality
 */
function setupChannelSearch(channels) {
    const channelSearch = document.getElementById('channelSearch');
    const channelDropdown = document.getElementById('channelDropdown');
    const selectedChannelId = document.getElementById('selectedChannelId');
    
    /**
     * Render channels in dropdown
     */
    function renderChannels(channelsToRender) {
        if (channelsToRender.length === 0) {
            channelDropdown.innerHTML = '<div class="channel-dropdown-item">No channels found</div>';
            channelDropdown.classList.remove('d-none');
            return;
        }
        
        // Render channels
        channelDropdown.innerHTML = channelsToRender.map(channel => `
            <div class="channel-dropdown-item" data-channel-id="${channel.id}" data-channel-name="${channel.name}">
                # ${channel.name}
            </div>
        `).join('');
        
        channelDropdown.classList.remove('d-none');
        
        // Add click handlers
        channelDropdown.querySelectorAll('.channel-dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const channelId = item.dataset.channelId;
                const channelName = item.dataset.channelName;
                channelSearch.value = `# ${channelName}`;
                selectedChannelId.value = channelId;
                channelDropdown.classList.add('d-none');
            });
        });
    }
    
    // Show all channels when input is focused/clicked
    channelSearch.addEventListener('focus', () => {
        renderChannels(channels);
    });
    
    channelSearch.addEventListener('click', () => {
        renderChannels(channels);
    });
    
    // Filter channels as user types
    channelSearch.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        
        // Remove the "# " prefix if user typed it
        const cleanSearchTerm = searchTerm.replace(/^#\s*/, '');
        
        if (cleanSearchTerm === '') {
            // Show all channels when search is empty
            renderChannels(channels);
            selectedChannelId.value = '';
            return;
        }
        
        // Filter channels
        const filtered = channels.filter(channel => 
            channel.name.toLowerCase().includes(cleanSearchTerm)
        );
        
        renderChannels(filtered);
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!channelSearch.contains(e.target) && !channelDropdown.contains(e.target)) {
            channelDropdown.classList.add('d-none');
        }
    });
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Apply filters button
    document.getElementById('applyFilters').addEventListener('click', handleApplyFilters);
    
    // Retry button
    document.getElementById('retryButton').addEventListener('click', handleApplyFilters);
    
    // Enter key on date inputs
    ['startDate', 'endDate'].forEach(id => {
        document.getElementById(id).addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleApplyFilters();
            }
        });
    });
}

/**
 * Handle apply filters button click
 */
async function handleApplyFilters() {
    const channelId = document.getElementById('selectedChannelId').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const uniqueReactions = document.getElementById('uniqueReactions').checked;
    
    // Validation
    if (!channelId) {
        showToast('Please select a channel', 'error');
        return;
    }
    
    if (!startDate || !endDate) {
        showToast('Please select both start and end dates', 'error');
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        showToast('Start date must be before end date', 'error');
        return;
    }
    
    // Show loading state
    showLoadingState();
    const applyButton = document.getElementById('applyFilters');
    const spinner = document.getElementById('loadingSpinner');
    applyButton.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        const params = {
            channel_id: channelId,
            start_date: startDate,
            end_date: endDate,
            unique_reactions: uniqueReactions
        };
        
        // Always fetch photos
        const items = await fetchPhotos(params);
        
        currentItems = items;
        renderResults(items, 'photos', true);
        
        if (items.length === 0) {
            showToast('No results found for the selected filters', 'info');
        } else {
            showToast(`Found ${items.length} ${items.length === 1 ? 'photo' : 'photos'}`, 'success');
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        showErrorState(error.message || 'An error occurred while fetching data');
        showToast(error.message || 'Failed to fetch data', 'error');
    } finally {
        applyButton.disabled = false;
        spinner.classList.add('d-none');
    }
}


/**
 * Trigger confetti animation
 */
function triggerConfetti() {
    if (typeof confetti !== 'undefined') {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

/**
 * Initialize app when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

