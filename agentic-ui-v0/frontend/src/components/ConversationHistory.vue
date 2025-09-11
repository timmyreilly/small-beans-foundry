<template>
  <div class="conversation-history">
    <div class="history-header">
      <h3>Conversations</h3>
      <button @click="toggleExpanded" class="toggle-btn" :title="isExpanded ? 'Collapse' : 'Expand'">
        {{ isExpanded ? '▼' : '▲' }}
      </button>
    </div>
    
    <div v-if="isExpanded" class="history-content">
      <div class="history-actions">
        <button @click="createNewSession" class="new-session-btn">
          + New Conversation
        </button>
      </div>
      
      <div class="sessions-list">
        <div 
          v-for="session in chatStore.sessions" 
          :key="session.id"
          :class="['session-item', { active: session.id === chatStore.currentSession?.id }]"
          @click="loadSession(session.id)"
        >
          <div class="session-preview">
            <div class="session-title">
              {{ chatStore.getSessionTitle(session) }}
            </div>
            <div class="session-time">
              {{ formatSessionTime(getLastMessageTime(session)) }}
            </div>
            <div class="session-message-count">
              {{ session.messages.length }} messages
            </div>
          </div>
          <div class="session-actions">
            <button 
              @click.stop="deleteSession(session.id)" 
              class="delete-btn"
              :title="'Delete conversation'"
              v-if="chatStore.sessions.length > 1"
            >
              🗑️
            </button>
          </div>
        </div>
        
        <div v-if="!chatStore.sessions.length" class="no-sessions">
          <p>No conversation history yet</p>
          <small>Start a conversation to see it here</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import type { Session } from '../types'

const chatStore = useChatStore()
const isExpanded = ref(true)

onMounted(() => {
  // Initialize with current session if none exists
  if (!chatStore.currentSession && chatStore.sessions.length === 0) {
    chatStore.createSession()
  }
})

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const createNewSession = () => {
  chatStore.createSession()
}

const loadSession = async (sessionId: string) => {
  await chatStore.switchToSession(sessionId)
}

const deleteSession = (sessionId: string) => {
  if (confirm('Are you sure you want to delete this conversation?')) {
    chatStore.deleteSession(sessionId)
  }
}

const getLastMessageTime = (session: Session): Date | null => {
  if (session.messages.length === 0) return session.createdAt || new Date()
  return session.messages[session.messages.length - 1].timestamp
}

const formatSessionTime = (timestamp: Date | null) => {
  if (!timestamp) return ''
  
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return time.toLocaleDateString()
  }
}
</script>

<style scoped>
.conversation-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
}

.history-header h3 {
  margin: 0;
  color: #1e40af;
  font-size: 1.1rem;
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  color: #64748b;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background: #f1f5f9;
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-actions {
  padding: 1rem;
}

.new-session-btn {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.new-session-btn:hover {
  background: #2563eb;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  margin: 0.25rem 0;
  background: white;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.session-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.session-item.active {
  background: #eff6ff;
  border-color: #3b82f6;
}

.session-preview {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 0.75rem;
  color: #64748b;
}

.session-message-count {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.125rem;
}

.session-actions {
  display: flex;
  align-items: center;
  margin-left: 0.5rem;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  color: #64748b;
  transition: all 0.2s;
  opacity: 0;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.no-sessions {
  text-align: center;
  padding: 2rem 1rem;
  color: #64748b;
}

.no-sessions p {
  margin: 0 0 0.5rem 0;
  font-weight: 500;
}

.no-sessions small {
  color: #94a3b8;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .conversation-history {
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .history-header {
    padding: 0.75rem 1rem;
  }
  
  .history-content {
    max-height: 200px;
  }
  
  .session-item {
    padding: 0.5rem;
  }
  
  .session-title {
    font-size: 0.9rem;
  }
}
</style>