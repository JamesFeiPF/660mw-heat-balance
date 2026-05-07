<template>
  <div class="home-view">
    <Toolbar />
    <div class="main-content">
      <ComponentPanel />
      <ModelCanvas />
      <PropertyPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import Toolbar from '../components/Toolbar.vue'
import ComponentPanel from '../components/ComponentPanel.vue'
import ModelCanvas from '../components/ModelCanvas.vue'
import PropertyPanel from '../components/PropertyPanel.vue'
</script>

<style scoped>
.home-view {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #1a1a2e;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
