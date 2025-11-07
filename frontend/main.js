// DOM elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const contextSelect = document.getElementById('contextSelect');
const sessionDisplay = document.getElementById('sessionDisplay');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');

// Initialize session
let sessionId = 'BRG-' + Math.random().toString(36).substr(2, 9).toUpperCase();
sessionDisplay.textContent = sessionId;

// Backend API URL - adjust this to match your backend URL
const API_URL = 'http://localhost:8000'; // Change this to your backend URL

// File handling
let uploadedFiles = [];

fileInput.addEventListener('change', function(e) {
    handleFiles(e.target.files);
});

function handleFiles(files) {
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        uploadedFiles.push(file);
        displayFilePreview(file);
    }
    // Reset file input to allow uploading the same file again
    fileInput.value = '';
}

function displayFilePreview(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    
    const fileIcon = document.createElement('img');
    fileIcon.src = getFileIcon(file.type);
    
    const fileName = document.createElement('span');
    fileName.textContent = file.name;
    
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-file';
    removeBtn.innerHTML = '×';
    removeBtn.onclick = function() {
        removeFile(file, fileItem);
    };
    
    fileItem.appendChild(fileIcon);
    fileItem.appendChild(fileName);
    fileItem.appendChild(removeBtn);
    filePreview.appendChild(fileItem);
}

function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) {
        return 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzM0OThkYiI+PHBhdGggZD0iTTggMTZjLTEuMSAwLTItLjktMi0ycy45LTIgMi0yIDIgLjkgMiAyLS45IDItMiAyem02LTEwaC04Yy0xLjEgMC0yIC45LTIgMnYxMmMwIDEuMS45IDIgMiAyaDhjMS4xIDAgMi0uOSAyLTJ2LTEyYzAtMS4xLS45LTItMi0yem0tNCAxNGMtMi4yMSAwLTQtMS43OS00LTRzMS43OS00IDQtNCA0IDEuNzkgNCA0LTEuNzkgNC00IDR6Ii8+PC9zdmc+';
    } else if (fileType.includes('pdf')) {
        return 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2U3NDNjYyI+PHBhdGggZD0iTTIwIDJoLThsLTIgMmgtOGMtMS4xIDAtMiAuOS0yIDJ2MTJjMCAxLjEuOSAyIDIgMmgxNmMxLjEgMCAyLS45IDItMnYtMTRjMC0xLjEtLjktMi0yLTJ6bS04LjUgMTJoLTMuNWMtLjMgMC0uNS0uMi0uNS0uNXYtMWMwLS4zLjItLjUuNS0uNWgzLjVjLjMgMCAuNS4yLjUuNXYxYzAgLjMtLjIuNS0uNS41em0zLTZoLTYuNWMtLjMgMC0uNS0uMi0uNS0uNXYtMWMwLS4zLjItLjUuNS0uNWg2LjVjLjMgMCAuNS4yLjUuNXYxYzAgLjMtLjIuNS0uNS41eiIvPjwvc3ZnPg==';
    } else if (fileType.includes('word') || fileType.includes('document')) {
        return 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzJlNzJjZCI+PHBhdGggZD0iTTE0IDJoLTZsLTItMmgtNmMtMS4xIDAtMiAuOS0yIDJ2MTZjMCAxLjEuOSAyIDIgMmgxNmMxLjEgMCAyLS45IDItMnYtMTJsLTYtNnptLTItMTB2NGg0bC00LTR6bTggMTRoLTEydi0xMmg2djZoNnY2eiIvPjwvc3ZnPg==';
    } else {
        return 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzlmNTliNiI+PHBhdGggZD0iTTE0IDJoLTZsLTItMmgtNmMtMS4xIDAtMiAuOS0yIDJ2MTZjMCAxLjEuOSAyIDIgMmgxNmMxLjEgMCAyLS45IDItMnYtMTJsLTYtNnptLTItMTB2NGg0bC00LTR6bTggMTRoLTEydi0xMmg2djZoNnY2eiIvPjwvc3ZnPg==';
    }
}

function removeFile(file, fileElement) {
    uploadedFiles = uploadedFiles.filter(f => f !== file);
    fileElement.remove();
}

function takePhoto() {
    alert("Camera functionality would be implemented here. For this demo, you can upload images using the file upload button.");
}

// Chat functionality - UPDATED TO CONNECT TO BACKEND
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';

    // Disable send button while processing
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span>⏳</span> Sending...';

    // Show typing indicator
    showTypingIndicator();

    try {
        // Prepare data to send to backend
        const requestData = {
            message: message,
            context: contextSelect.value,
            session_id: sessionId
        };

        // If there are uploaded files, handle them
        if (uploadedFiles.length > 0) {
            requestData.files = [];
            // For now, we'll just send file names and types
            // In a real implementation, you'd upload the actual files
            uploadedFiles.forEach(file => {
                requestData.files.push({
                    name: file.name,
                    type: file.type,
                    size: file.size
                });
            });
        }

        // Send message to backend
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        hideTypingIndicator();
        addMessage(data.response, 'ai');
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        
        // Fallback to local responses if backend is not available
        const fallbackResponse = generateFallbackResponse(message, contextSelect.value);
        addMessage(fallbackResponse, 'ai');
        
        // Show error message if backend is completely down
        if (error.message.includes('Failed to fetch')) {
            addMessage("Note: Currently using offline mode. Backend server appears to be unavailable.", 'ai');
        }
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span>📤</span> Send';
        
        // Clear uploaded files after sending
        uploadedFiles = [];
        filePreview.innerHTML = '';
    }
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const senderName = sender === 'user' ? 'You' : 'BarangAI';
    messageDiv.innerHTML = `<strong>${senderName}:</strong> ${content}`;
    
    // Add file attachments if any (for user messages)
    if (sender === 'user' && uploadedFiles.length > 0) {
        const attachmentsDiv = document.createElement('div');
        attachmentsDiv.className = 'attachments';
        
        uploadedFiles.forEach(file => {
            const attachmentDiv = document.createElement('div');
            attachmentDiv.className = 'attachment';
            
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                attachmentDiv.appendChild(img);
            } else {
                const docDiv = document.createElement('div');
                docDiv.className = 'attachment-doc';
                docDiv.innerHTML = `
                    <img src="${getFileIcon(file.type)}" alt="File icon">
                    <span>${file.name}</span>
                `;
                attachmentDiv.appendChild(docDiv);
            }
            
            attachmentsDiv.appendChild(attachmentDiv);
        });
        
        messageDiv.appendChild(attachmentsDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'typing';
    typingDiv.textContent = 'BarangAI is typing...';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Fallback response generator (only used when backend is unavailable)
function generateFallbackResponse(userMessage, context) {
    // More specific responses based on common questions
    const responses = {
        general: [
            "I understand you're asking about digital systems. Could you tell me which specific software or platform you need help with?",
            "That's a great digital literacy question! Let me help you step by step.",
            "I'd be happy to assist with your digital query. What specific task are you trying to accomplish?"
        ],
        documents: [
            "For document help, I can guide you through formatting, saving, or sharing documents. What specifically do you need?",
            "Document processing can include Word, Google Docs, or PDF files. Which one are you working with?",
            "I can help with creating barangay reports, certificates, or announcements. What document are you working on?"
        ],
        spreadsheets: [
            "Spreadsheets are great for barangay data! Are you working with Excel, Google Sheets, or another program?",
            "I can help with formulas, data organization, or creating charts for barangay reports.",
            "For spreadsheets, we can work on budgeting, resident lists, or event planning. What do you need?"
        ],
        presentations: [
            "Presentations help share barangay updates effectively. Are you using PowerPoint, Google Slides, or another tool?",
            "I can assist with slide design, content organization, or presentation delivery.",
            "Let me help you create engaging presentations for barangay meetings or community updates."
        ],
        communication: [
            "Digital communication tools can include email, messaging apps, or video calls. Which one do you need help with?",
            "I can guide you through setting up email, group chats, or video meetings for barangay coordination.",
            "Effective communication is key! Tell me which platform you're using and what you need to accomplish."
        ],
        internet: [
            "Internet browsing and online services are essential. Are you having trouble with websites, searches, or online forms?",
            "I can help with safe browsing, finding information online, or using government portals.",
            "Let me assist you with internet-related tasks. What specific website or online service are you trying to use?"
        ]
    };
    
    const contextResponses = responses[context] || responses.general;
    const randomResponse = contextResponses[Math.floor(Math.random() * contextResponses.length)];
    
    return randomResponse;
}

function clearChat() {
    if (confirm("Are you sure you want to clear the chat history?")) {
        chatMessages.innerHTML = `
            <div class="message ai-message">
                <strong>BarangAI:</strong> Hello! I'm here to help you with digital tasks. You can ask questions, upload documents, or even take photos to get assistance. Choose a category and let me know how I can help!
            </div>
        `;
        uploadedFiles = [];
        filePreview.innerHTML = '';
    }
}

// Allow sending message with Enter key (but allow Shift+Enter for new line)
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea as user types
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});