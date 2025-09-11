<template>
  <div id="app">
    <div class="app-layout">
      <ConversationHistory class="sidebar" />
      <ChatInterface class="main-chat" />
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatInterface from './components/ChatInterface.vue'
import ConversationHistory from './components/ConversationHistory.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f8fafc;
}

#app {
  width: 100%;
  height: 100vh;
}

.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 320px;
  flex-shrink: 0;
}

.main-chat {
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    max-height: 40vh;
  }
  
  .main-chat {
    flex: 1;
    min-height: 60vh;
  }
}
</style>