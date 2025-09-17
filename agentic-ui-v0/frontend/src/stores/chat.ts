import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message, Session } from '../types'

export interface AgentMode {
  id: string
  name: string
  description: string
  available: boolean
}

export const useChatStore = defineStore('chat', () => {
  const currentSession = ref<Session | null>(null)
  const isLoading = ref(false)
  const agentMode = ref<string>('single') // 'single' or 'multi'
  const availableAgentModes = ref<AgentMode[]>([
    {
      id: 'single',
      name: 'Single Agent',
      description: 'Standard AI assistant with general conversation capabilities',
      available: true
    },
    {
      id: 'multi',
      name: 'Multi-Agent Research',
      description: 'Collaborative AI team with internet research and summarization capabilities',
      available: false // Will be updated from backend
    }
  ])

  const createSession = () => {
    currentSession.value = {
      id: crypto.randomUUID(),
      messages: []
    }
    return currentSession.value
  }

  const addMessage = (content: string, role: 'user' | 'assistant'): Message => {
    if (!currentSession.value) {
      createSession()
    }

    const message: Message = {
      id: crypto.randomUUID(),
      content,
      role,
      timestamp: new Date()
    }

    currentSession.value!.messages.push(message)
    return message
  }

  const clearSession = () => {
    if (currentSession.value) {
      currentSession.value.messages = []
    }
  }

  const setAgentMode = (mode: string) => {
    const availableMode = availableAgentModes.value.find(m => m.id === mode)
    if (availableMode && availableMode.available) {
      agentMode.value = mode
      // Clear session when switching modes to avoid confusion
      clearSession()
    }
  }

  const updateAvailableAgentModes = (modes: AgentMode[]) => {
    availableAgentModes.value = modes
  }

  return {
    currentSession,
    isLoading,
    agentMode,
    availableAgentModes,
    createSession,
    addMessage,
    clearSession,
    setAgentMode,
    updateAvailableAgentModes
  }
})