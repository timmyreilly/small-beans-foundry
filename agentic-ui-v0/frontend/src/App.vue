<template>
  <div id="app">
    <ChatInterface />
  </div>
</template>

<script setup lang="ts">
import ChatInterface from './components/ChatInterface.vue'
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
</style>