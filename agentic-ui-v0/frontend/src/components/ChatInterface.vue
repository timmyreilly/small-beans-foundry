<template>
  <div class="chat-interface">
    <div class="chat-header">
      <h1>Agentic UI v0</h1>
      <p>Simple AutoGen Chat Assistant</p>
    </div>

    <div class="chat-container">
      <div class="messages" ref="messagesContainer">
        <div class="welcome" v-if="!chatStore.currentSession?.messages.length">
          <h3>👋 Welcome!</h3>
          <p>Start a conversation with your AI assistant. Ask me anything!</p>
        </div>
        
        <div 
          v-for="message in chatStore.currentSession?.messages" 
          :key="message.id"
          :class="['message', message.role]"
        >
          <div class="message-content">{{ sanitizeContent(message.content) }}</div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
        
        <div v-if="chatStore.isLoading" class="message assistant loading">
          <div class="message-content">
            <div class="spinner"></div>
            Thinking...
          </div>
        </div>
      </div>

      <div class="chat-input">
        <form @submit.prevent="sendMessage">
          <div class="input-group">
            <textarea 
              v-model="newMessage" 
              placeholder="Type your message here..."
              :disabled="chatStore.isLoading"
              @keydown.enter.prevent="sendMessage"
              rows="2"
            ></textarea>
            <div class="input-actions">
              <button 
                type="button" 
                @click="clearChat"
                class="clear-btn"
                :disabled="chatStore.isLoading"
              >
                Clear
              </button>
              <button 
                type="submit" 
                :disabled="chatStore.isLoading || !newMessage.trim()"
                class="send-btn"
              >
                Send
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import axios from 'axios'

const chatStore = useChatStore()
const newMessage = ref('')
const messagesContainer = ref<HTMLElement>()

onMounted(() => {
  if (!chatStore.currentSession) {
    chatStore.createSession()
  }
})

const sendMessage = async () => {
  if (!newMessage.value.trim() || chatStore.isLoading) return

  const messageText = newMessage.value.trim()
  newMessage.value = ''

  chatStore.addMessage(messageText, 'user')
  
  try {
    chatStore.isLoading = true
    
    const response = await axios.post('/api/chat', {
      message: messageText,
      session_id: chatStore.currentSession?.id
    })

    const sanitizedResponse = sanitizeContent(response.data.response)
    chatStore.addMessage(sanitizedResponse, 'assistant')

  } catch (error) {
    console.error('Error sending message:', error)
    let errorMessage = 'Sorry, there was an error processing your message.'
    
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      errorMessage = `Error: ${error.response.data.detail}`
    }
    
    chatStore.addMessage(errorMessage, 'assistant')
  } finally {
    chatStore.isLoading = false
  }
}

const clearChat = () => {
  chatStore.clearSession()
}

const sanitizeContent = (content: string): string => {
  if (!content) return ''
  
  // Handle escaped characters that might come from the backend
  let sanitized = content
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\\\/g, '\\')
  
  // Remove any wrapping quotes if the entire content is quoted
  sanitized = sanitized.trim()
  if ((sanitized.startsWith('"') && sanitized.endsWith('"')) ||
      (sanitized.startsWith("'") && sanitized.endsWith("'"))) {
    sanitized = sanitized.slice(1, -1)
  }
  
  return sanitized
}

const formatTime = (timestamp: Date) => {
  return new Date(timestamp).toLocaleTimeString()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.currentSession?.messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-interface {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.chat-header {
  padding: 1rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  text-align: center;
}

.chat-header h1 {
  margin: 0;
  color: #1e40af;
  font-size: 1.5rem;
}

.chat-header p {
  margin: 0.25rem 0 0 0;
  color: #64748b;
  font-size: 0.9rem;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.welcome {
  text-align: center;
  padding: 2rem;
  color: #64748b;
}

.welcome h3 {
  color: #1e40af;
  margin: 0 0 0.5rem 0;
}

.message {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  word-wrap: break-word;
}

.message.user {
  background: #3b82f6;
  color: white;
  align-self: flex-end;
  margin-left: auto;
}

.message.assistant {
  background: #f1f5f9;
  color: #334155;
  align-self: flex-start;
  border: 1px solid #e2e8f0;
}

.message.loading {
  opacity: 0.7;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.message-content {
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-right: 0.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chat-input {
  padding: 1rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-input textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.chat-input textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.input-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.clear-btn, .send-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.clear-btn {
  background: #f1f5f9;
  color: #64748b;
}

.clear-btn:hover:not(:disabled) {
  background: #e2e8f0;
}

.send-btn {
  background: #3b82f6;
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
}

.clear-btn:disabled, .send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .chat-container {
    margin: 0.5rem;
    border-radius: 0.5rem;
  }
  
  .message {
    max-width: 90%;
  }
  
  .chat-header {
    padding: 0.75rem 1rem;
  }
  
  .chat-header h1 {
    font-size: 1.25rem;
  }
}
</style>