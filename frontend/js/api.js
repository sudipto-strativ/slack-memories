/**
 * API Client for Slack Trophy Backend
 * Handles all HTTP requests to the FastAPI backend
 */

const API_BASE_URL = 'http://localhost:8000';
const REQUEST_TIMEOUT = 30000; // 30 seconds

/**
 * Make an HTTP request with error handling and timeout
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise} Response data
 */
async function apiRequest(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timeout. Please try again.');
        }
        
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Unable to connect to server. Please check if the backend is running.');
        }
        
        throw error;
    }
}

/**
 * Fetch list of available Slack channels
 * @returns {Promise<Array>} Array of channel objects
 */
async function fetchChannels() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/channels`);
        return response.channels || [];
    } catch (error) {
        console.error('Error fetching channels:', error);
        throw error;
    }
}

/**
 * Fetch photos from a channel within a date range
 * @param {Object} params - Query parameters
 * @param {string} params.channel_id - Slack channel ID
 * @param {string} params.start_date - Start date in YYYY-MM-DD format
 * @param {string} params.end_date - End date in YYYY-MM-DD format
 * @param {boolean} params.unique_reactions - Whether to count only unique reactions
 * @returns {Promise<Array>} Array of photo objects
 */
async function fetchPhotos(params) {
    try {
        const { channel_id, start_date, end_date, unique_reactions = false } = params;
        
        if (!channel_id || !start_date || !end_date) {
            throw new Error('Missing required parameters: channel_id, start_date, end_date');
        }

        const queryParams = new URLSearchParams({
            channel_id,
            start_date,
            end_date,
            unique_reactions: unique_reactions.toString()
        });

        const response = await apiRequest(`${API_BASE_URL}/photos?${queryParams}`);
        return response.items || [];
    } catch (error) {
        console.error('Error fetching photos:', error);
        throw error;
    }
}

/**
 * Fetch messages from a channel within a date range
 * @param {Object} params - Query parameters
 * @param {string} params.channel_id - Slack channel ID
 * @param {string} params.start_date - Start date in YYYY-MM-DD format
 * @param {string} params.end_date - End date in YYYY-MM-DD format
 * @param {boolean} params.unique_reactions - Whether to count only unique reactions
 * @returns {Promise<Array>} Array of message objects
 */
async function fetchMessages(params) {
    try {
        const { channel_id, start_date, end_date, unique_reactions = false } = params;
        
        if (!channel_id || !start_date || !end_date) {
            throw new Error('Missing required parameters: channel_id, start_date, end_date');
        }

        const queryParams = new URLSearchParams({
            channel_id,
            start_date,
            end_date,
            unique_reactions: unique_reactions.toString()
        });

        const response = await apiRequest(`${API_BASE_URL}/messages?${queryParams}`);
        return response.items || [];
    } catch (error) {
        console.error('Error fetching messages:', error);
        throw error;
    }
}

/**
 * Health check endpoint
 * @returns {Promise<Object>} Health status
 */
async function healthCheck() {
    try {
        return await apiRequest(`${API_BASE_URL}/health`);
    } catch (error) {
        console.error('Health check failed:', error);
        throw error;
    }
}

/**
 * Get proxy URL for Slack image
 * @param {string} imageUrl - Original Slack image URL
 * @returns {string} Proxy URL
 */
function getProxyImageUrl(imageUrl) {
    if (!imageUrl) return '';
    const encodedUrl = encodeURIComponent(imageUrl);
    return `${API_BASE_URL}/proxy-image?url=${encodedUrl}`;
}

/**
 * Get emoji info (for custom emojis)
 * @param {string} emojiName - Emoji name
 * @returns {Promise<Object>} Emoji info with URL
 */
async function getEmojiInfo(emojiName) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/emoji-info?emoji_name=${encodeURIComponent(emojiName)}`);
        return response;
    } catch (error) {
        console.error('Error fetching emoji info:', error);
        return { url: null, is_custom: false };
    }
}

