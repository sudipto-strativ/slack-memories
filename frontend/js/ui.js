/**
 * UI Rendering Functions
 * Handles all DOM manipulation and UI state management
 */

/**
 * Get proxy URL for Slack image
 * @param {string} imageUrl - Original Slack image URL
 * @returns {string} Proxy URL
 */
function getProxyImageUrl(imageUrl) {
    if (!imageUrl) return '';
    const encodedUrl = encodeURIComponent(imageUrl);
    // API_BASE_URL is defined in api.js
    return `${API_BASE_URL}/proxy-image?url=${encodedUrl}`;
}

/**
 * Show loading state with skeleton cards
 */
function showLoadingState() {
    document.getElementById('loadingState').classList.remove('d-none');
    document.getElementById('emptyState').classList.add('d-none');
    document.getElementById('errorState').classList.add('d-none');
    document.getElementById('resultsContainer').classList.add('d-none');
    
    const skeletonContainer = document.getElementById('skeletonCards');
    skeletonContainer.innerHTML = '';
    
    // Create 6 skeleton cards
    for (let i = 0; i < 6; i++) {
        const skeletonCard = document.createElement('div');
        skeletonCard.className = 'col-md-4 col-sm-6 mb-4';
        skeletonCard.innerHTML = `
            <div class="skeleton-card">
                <div class="skeleton-image"></div>
                <div class="skeleton-text"></div>
                <div class="skeleton-text" style="width: 60%;"></div>
                <div class="skeleton-text" style="width: 40%;"></div>
            </div>
        `;
        skeletonContainer.appendChild(skeletonCard);
    }
}

/**
 * Show empty state
 */
function showEmptyState() {
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('emptyState').classList.remove('d-none');
    document.getElementById('errorState').classList.add('d-none');
    document.getElementById('resultsContainer').classList.add('d-none');
}

/**
 * Show error state with message and retry button
 * @param {string} errorMessage - Error message to display
 */
function showErrorState(errorMessage) {
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('emptyState').classList.add('d-none');
    document.getElementById('errorState').classList.remove('d-none');
    document.getElementById('resultsContainer').classList.add('d-none');
    
    document.getElementById('errorMessage').textContent = errorMessage;
}

/**
 * Render a single emoji (handles custom emojis)
 * @param {string} emojiName - Emoji name (e.g., ':+1:' or 'custom_emoji')
 * @param {Object} emojiCache - Cache of emoji info
 * @returns {Promise<string>} HTML string for emoji
 */
async function renderEmoji(emojiName, emojiCache = {}) {
    // Check if it's a custom emoji (contains only alphanumeric, underscore, dash, or starts with :)
    const cleanName = emojiName.replace(/:/g, '');
    const isCustomEmoji = /^[a-zA-Z0-9_-]+$/.test(cleanName) && cleanName.length > 0;
    
    // If it's a standard emoji (contains unicode), render directly
    if (!isCustomEmoji) {
        return `<span class="emoji">${emojiName}</span>`;
    }
    
    // Check cache first
    if (emojiCache[cleanName]) {
        const emojiInfo = emojiCache[cleanName];
        if (emojiInfo.url) {
            return `<img src="${emojiInfo.url}" alt="${emojiName}" class="emoji-image" style="width: 20px; height: 20px; vertical-align: middle;">`;
        }
    }
    
    // Try to get emoji info (async, but we'll render placeholder for now)
    // For now, render as text and let the async update happen
    return `<span class="emoji emoji-custom" data-emoji="${cleanName}">:${cleanName}:</span>`;
}

/**
 * Render emoji reactions as pills
 * @param {Object} emojiReactions - Object mapping emoji to count
 * @returns {string} HTML string for emoji pills
 */
function renderEmojiPills(emojiReactions) {
    if (!emojiReactions || Object.keys(emojiReactions).length === 0) {
        return '<div class="text-muted">No reactions</div>';
    }
    
    // Sort by count (descending) and take top 5
    const sortedEmojis = Object.entries(emojiReactions)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    
    return sortedEmojis.map(([emoji, count]) => {
        const cleanName = emoji.replace(/:/g, '');
        const isCustomEmoji = /^[a-zA-Z0-9_-]+$/.test(cleanName) && cleanName.length > 0;
        
        // For custom emojis, render with data attribute for async loading
        const emojiHtml = isCustomEmoji 
            ? `<span class="emoji emoji-custom" data-emoji-name="${cleanName}" style="display: inline-block; width: 20px; height: 20px; vertical-align: middle; background: #f0f0f0; border-radius: 4px;">:${cleanName}:</span>`
            : `<span class="emoji">${emoji}</span>`;
        
        return `
            <div class="emoji-pill" data-emoji="${cleanName}" data-is-custom="${isCustomEmoji}">
                ${emojiHtml}
                <span class="count">${count}</span>
            </div>
        `;
    }).join('');
}

/**
 * Get medal emoji for rank
 * @param {number} rank - Item rank
 * @returns {string} Medal emoji or empty string
 */
function getMedalEmoji(rank) {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '';
}

/**
 * Render a photo card
 * @param {Object} photo - Photo object
 * @param {number} rank - Photo rank
 * @returns {string} HTML string for photo card
 */
function renderPhotoCard(photo, rank) {
    const medal = getMedalEmoji(rank);
    const rankClass = rank <= 3 ? `rank-${rank}` : '';
    const mediaType = photo.media_type || 'image';
    const isVideo = mediaType === 'video';
    
    // Render image or video based on media type
    const mediaElement = isVideo
        ? `<video class="card-media" loading="lazy" muted playsinline preload="metadata" data-video-id="${photo.id}">
             <source src="${getProxyImageUrl(photo.url)}" type="video/mp4">
             Your browser does not support the video tag.
           </video>
           <div class="video-play-overlay" data-overlay-id="${photo.id}">▶</div>`
        : `<img src="${getProxyImageUrl(photo.url)}" alt="Photo ${rank}" class="card-media" loading="lazy" 
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23ddd%22 width=%22400%22 height=%22300%22/%3E%3Ctext fill=%22%23999%22 font-family=%22sans-serif%22 font-size=%2220%22 dy=%2210.5%22 font-weight=%22bold%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22%3EImage not available%3C/text%3E%3C/svg%3E'">`;
    
    return `
        <div class="col-md-4 col-sm-6 mb-4">
            <div class="trophy-card ${rankClass} fade-in" data-id="${photo.id}" data-type="photo" data-media-type="${mediaType}">
                ${medal ? `<div class="medal-badge">${medal}</div>` : ''}
                ${!medal ? `<div class="rank-number">#${rank}</div>` : ''}
                
                <div class="card-image-container ${isVideo ? 'video-container' : ''}">
                    ${mediaElement}
                </div>
                
                <div class="card-body-custom">
                    <div class="total-reactions-badge">
                        ${photo.total_reactions} ${photo.total_reactions === 1 ? 'reaction' : 'reactions'}
                    </div>
                    
                    ${photo.uploader_name ? `<div class="uploader-name mt-2">By ${photo.uploader_name}</div>` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render a message card
 * @param {Object} message - Message object
 * @param {number} rank - Message rank
 * @returns {string} HTML string for message card
 */
function renderMessageCard(message, rank) {
    const medal = getMedalEmoji(rank);
    const rankClass = rank <= 3 ? `rank-${rank}` : '';
    // Safety check for text property
    const messageText = message.text || '';
    const truncatedText = messageText.length > 200 ? messageText.substring(0, 200) + '...' : messageText;
    const needsExpansion = messageText.length > 200;
    
    return `
        <div class="col-md-4 col-sm-6 mb-4">
            <div class="trophy-card ${rankClass} fade-in" data-id="${message.id}" data-type="message">
                ${medal ? `<div class="medal-badge">${medal}</div>` : ''}
                ${!medal ? `<div class="rank-number">#${rank}</div>` : ''}
                
                <div class="card-body-custom">
                    <div class="message-text" id="msg-${message.id}">
                        ${truncatedText || '(No text content)'}
                    </div>
                    ${needsExpansion ? `<a href="#" class="expand-text-btn" data-id="${message.id}">Read more</a>` : ''}
                    
                    <div class="total-reactions-badge">
                        ${message.total_reactions} ${message.total_reactions === 1 ? 'reaction' : 'reactions'}
                    </div>
                    
                    ${message.author_name ? `<div class="author-name mt-2">By ${message.author_name}</div>` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render podium view for top 3 items
 * @param {Array} items - Array of top 3 items
 * @param {string} type - Item type ('photo' or 'message')
 */
function renderPodiumView(items, type) {
    const podiumContainer = document.getElementById('podiumView');
    podiumContainer.innerHTML = '';
    
    if (items.length === 0) return;
    
    const top3 = items.slice(0, 3);
    
    top3.forEach((item, index) => {
        const rank = index + 1;
        const podiumItem = document.createElement('div');
        podiumItem.className = `podium-item rank-${rank}`;
        
        // Handle both 'photo' and 'photos' for type checking
        const isPhoto = type === 'photo' || type === 'photos';
        if (isPhoto) {
            podiumItem.innerHTML = renderPhotoCard(item, rank);
        } else {
            podiumItem.innerHTML = renderMessageCard(item, rank);
        }
        
        podiumContainer.appendChild(podiumItem);
    });
}

/**
 * Render results grid
 * @param {Array} items - Array of items to render
 * @param {string} type - Item type ('photo' or 'message')
 * @param {boolean} showPodium - Whether to show podium for top 3
 */
function renderResults(items, type, showPodium = true) {
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('emptyState').classList.add('d-none');
    document.getElementById('errorState').classList.add('d-none');
    document.getElementById('resultsContainer').classList.remove('d-none');
    
    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = '';
    
    if (items.length === 0) {
        showEmptyState();
        return;
    }
    
    // Store original items for modal lookup
    const allItems = [...items];
    
    // Clear podium view (we're not using it anymore)
    document.getElementById('podiumView').innerHTML = '';
    
    // Render all items in grid (no podium view)
    items.forEach((item, index) => {
        const rank = index + 1;
        // Handle both 'photo' and 'photos' for type checking
        const isPhoto = type === 'photo' || type === 'photos';
        const cardHtml = isPhoto
            ? renderPhotoCard(item, rank)
            : renderMessageCard(item, rank);
        
        resultsGrid.insertAdjacentHTML('beforeend', cardHtml);
    });
    
    // Add click handlers for cards
    document.querySelectorAll('.trophy-card').forEach(card => {
        const mediaType = card.dataset.mediaType;
        
        // Set up video event listeners
        if (mediaType === 'video') {
            const video = card.querySelector('video');
            const overlay = card.querySelector('.video-play-overlay');
            
            if (video && overlay) {
                // Hide overlay when video plays
                video.addEventListener('play', () => {
                    overlay.style.display = 'none';
                });
                
                // Show overlay when video pauses
                video.addEventListener('pause', () => {
                    overlay.style.display = 'flex';
                });
                
                // Show overlay when video ends
                video.addEventListener('ended', () => {
                    overlay.style.display = 'flex';
                });
            }
        }
        
        card.addEventListener('click', (e) => {
            // Don't trigger modal if clicking on video play button
            if (e.target.closest('.video-play-overlay')) {
                return;
            }
            
            const itemId = card.dataset.id;
            const itemType = card.dataset.type;
            
            // If it's a video card, play/pause the video on click
            if (mediaType === 'video') {
                const video = card.querySelector('video');
                if (video && e.target !== video) {
                    // Toggle play/pause
                    if (video.paused) {
                        video.play();
                    } else {
                        video.pause();
                    }
                    return;
                }
            }
            
            // Search in all items (including top 3)
            const item = allItems.find(i => i.id === itemId);
            if (item) {
                showDetailModal(item, itemType);
            }
        });
    });
    
    // Add expand text handlers
    document.querySelectorAll('.expand-text-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const messageId = btn.dataset.id;
            const messageText = document.getElementById(`msg-${messageId}`);
            // Search in all items (including top 3)
            const item = allItems.find(m => m.id === messageId);
            if (item && messageText) {
                messageText.textContent = item.text || '(No text content)';
                messageText.classList.add('expanded');
                btn.style.display = 'none';
            }
        });
    });
    
}

/**
 * Show detail modal for photo or message
 * @param {Object} item - Photo or message object
 * @param {string} type - Item type ('photo' or 'message')
 */
function showDetailModal(item, type) {
    const modal = new bootstrap.Modal(document.getElementById('detailModal'));
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('detailModalLabel');
    
    // Handle both 'photo' and 'photos' for type checking
    const isPhoto = type === 'photo' || type === 'photos';
    if (isPhoto) {
        const mediaType = item.media_type || 'image';
        const isVideo = mediaType === 'video';
        const titleText = isVideo ? 'Video' : 'Photo';
        
        modalTitle.textContent = `${titleText} #${item.rank || 'N/A'}`;
        
        // Render image or video based on media type
        const mediaElement = isVideo
            ? `<video class="modal-image modal-video" controls autoplay>
                 <source src="${getProxyImageUrl(item.url)}" type="video/mp4">
                 Your browser does not support the video tag.
               </video>`
            : `<img src="${getProxyImageUrl(item.url)}" alt="Photo detail" class="modal-image" 
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22800%22 height=%22600%22%3E%3Crect fill=%22%23ddd%22 width=%22800%22 height=%22600%22/%3E%3Ctext fill=%22%23999%22 font-family=%22sans-serif%22 font-size=%2220%22 dy=%2210.5%22 font-weight=%22bold%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22%3EImage not available%3C/text%3E%3C/svg%3E'">`;
        
        modalBody.innerHTML = `
            ${mediaElement}
            <div class="modal-info-section">
                <div class="modal-info-item">
                    <span class="modal-info-label">Total Reactions:</span>
                    <span class="modal-info-value">${item.total_reactions}</span>
                </div>
                ${item.uploader_name ? `
                <div class="modal-info-item">
                    <span class="modal-info-label">Uploaded by:</span>
                    <span class="modal-info-value">${item.uploader_name}</span>
                </div>
                ` : ''}
            </div>
        `;
    } else {
        modalTitle.textContent = `Message #${item.rank || 'N/A'}`;
        
        modalBody.innerHTML = `
            <div class="message-text expanded mb-4">${item.text}</div>
            <div class="modal-info-section">
                <div class="modal-info-item">
                    <span class="modal-info-label">Total Reactions:</span>
                    <span class="modal-info-value">${item.total_reactions}</span>
                </div>
                ${item.author_name ? `
                <div class="modal-info-item">
                    <span class="modal-info-label">Author:</span>
                    <span class="modal-info-value">${item.author_name}</span>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    modal.show();
}


/**
 * Show toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type ('success', 'error', 'info')
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toastBody');
    
    toast.className = `toast`;
    if (type === 'error') {
        toast.classList.add('text-bg-danger');
    } else if (type === 'success') {
        toast.classList.add('text-bg-success');
    } else {
        toast.classList.add('text-bg-info');
    }
    
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

