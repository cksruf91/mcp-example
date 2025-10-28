const API_BASE_URL = 'http://localhost:8000';
let currentMode = 'normal';
let roomId = 'test-room-' + Date.now();
let chatHistory = []; // Store chat history as [["user", "message"], ["assistant", "response"]]

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function addMessage(text, isUser = false) {
    const container = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Apply markdown rendering for assistant messages
    if (!isUser && text) {
        bubble.innerHTML = marked.parse(text);
    } else {
        bubble.textContent = text;
    }

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString();

    messageDiv.appendChild(bubble);
    messageDiv.appendChild(time);
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;

    return messageDiv;
}

function addLoadingIndicator() {
    const container = document.getElementById('chatContainer');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loadingIndicator';

    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'message-bubble';
    loadingBubble.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;

    loadingDiv.appendChild(loadingBubble);
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;

    return loadingDiv;
}

function removeLoadingIndicator() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

function showError(message) {
    const container = document.getElementById('chatContainer');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Error: ${message}`;
    container.appendChild(errorDiv);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    addMessage(message, true);
    input.value = '';

    const sendBtn = document.querySelector('.send-btn');
    sendBtn.disabled = true;

    const loading = addLoadingIndicator();

    try {
        if (currentMode === 'normal') {
            await sendNormalMessage(message);
        } else {
            await sendStreamMessage(message);
        }
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to send message');
    } finally {
        removeLoadingIndicator();
        sendBtn.disabled = false;
    }
}

async function sendNormalMessage(text) {
    const response = await fetch(`${API_BASE_URL}/pne/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: text,
            roomId: roomId,
            history: chatHistory
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const assistantMessage = data.message || data.text || JSON.stringify(data);
    addMessage(assistantMessage);

    // Update chat history
    chatHistory.push(["user", text]);
    chatHistory.push(["assistant", assistantMessage]);
}

async function sendStreamMessage(text) {
    const response = await fetch(`${API_BASE_URL}/pne/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: text,
            roomId: roomId,
            history: chatHistory
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = '';
    let buffer = '';
    let currentEvent = null;  // Move outside the loop to persist across chunks

    removeLoadingIndicator();
    const messageDiv = addMessage('');
    const bubble = messageDiv.querySelector('.message-bubble');

    console.log('Starting SSE stream...');

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            console.log('Stream done');
            break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
            const trimmedLine = line.trim();
            console.log('Processing line:', JSON.stringify(line));

            if (trimmedLine === '') {
                // Empty line marks the end of an event
                console.log('Empty line - resetting event');
                currentEvent = null;
            } else if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
                console.log('Event type:', currentEvent);
            } else if (line.startsWith('data: ')) {
                const dataStr = line.slice(6).trim();
                console.log('Data string:', dataStr);

                if (dataStr && dataStr !== '[DONE]') {
                    try {
                        const data = JSON.parse(dataStr);
                        console.log('Parsed data:', data, 'Event:', currentEvent);

                        if (currentEvent === 'stream') {
                            // Stream mode: accumulate and display contents
                            if (data.contents) {
                                // Remove status message styling when streaming starts
                                bubble.classList.remove('status-message');
                                accumulatedText += data.contents;
                                bubble.textContent = accumulatedText;
                                console.log('Accumulated text length:', accumulatedText.length);
                            }
                        } else {
                            // Non-stream mode: display status message
                            if (data.message) {
                                // Add status message styling for non-stream events
                                bubble.classList.add('status-message');
                                bubble.textContent = `[${currentEvent || 'working'}] ${data.message}`;
                                console.log('Status message:', data.message);
                            }
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e, dataStr);
                    }
                }
            }
        }
    }

    console.log('Final accumulated text:', accumulatedText);

    // After streaming is complete, render markdown
    if (accumulatedText) {
        // Remove status message styling for final response
        bubble.classList.remove('status-message');
        bubble.innerHTML = marked.parse(accumulatedText);

        // Update chat history
        chatHistory.push(["user", text]);
        chatHistory.push(["assistant", accumulatedText]);
    } else {
        // If no accumulated text, keep the last status message
        console.warn('No accumulated text, keeping status message');
    }
}

async function showTools() {
    const modal = document.getElementById('toolsModal');
    const toolsList = document.getElementById('toolsList');

    modal.classList.add('show');
    toolsList.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/tool/list`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const tools = data.tools || [];

        if (tools.length === 0) {
            toolsList.innerHTML = '<p>No tools available</p>';
            return;
        }

        toolsList.innerHTML = tools.map(tool => `
            <div class="tool-item">
                <div class="tool-name">${tool.name || 'Unnamed Tool'}</div>
                <div class="tool-description">${tool.description || 'No description available'}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tools:', error);
        toolsList.innerHTML = `<div class="error-message">Failed to load tools: ${error.message}</div>`;
    }
}

function closeModal() {
    document.getElementById('toolsModal').classList.remove('show');
}

function resetChat() {
    // Confirm before resetting
    if (!confirm('Are you sure you want to reset the chat history? This action cannot be undone.')) {
        return;
    }

    // Clear chat history
    chatHistory = [];

    // Clear chat container (keep only the welcome message)
    const container = document.getElementById('chatContainer');
    container.innerHTML = `
        <div class="message assistant">
            <div class="message-bubble">
                Hello! I'm your MCP assistant with Plan-and-Execute capabilities!
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;

    // Generate new room ID
    roomId = 'test-room-' + Date.now();

    console.log('Chat history reset successfully');
}

// Close modal when clicking outside
document.getElementById('toolsModal').addEventListener('click', (e) => {
    if (e.target.id === 'toolsModal') {
        closeModal();
    }
});