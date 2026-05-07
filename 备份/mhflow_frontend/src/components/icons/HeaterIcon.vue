<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 加热器图标 -->
    <rect x="6" y="6" width="36" height="36" rx="4" :stroke="color" stroke-width="2.5" fill="none"/>
    <!-- 热交换波纹 -->
    <path d="M12 16 L20 16 L20 20 L28 20 L28 16 L36 16" :stroke="color" stroke-width="2" opacity="0.7"/>
    <path d="M12 28 L20 28 L20 32 L28 32 L28 28 L36 28" :stroke="color" stroke-width="2" opacity="0.7"/>
    <!-- 温度计 -->
    <rect x="22" y="20" width="4" height="12" rx="2" :fill="color" opacity="0.4"/>
    <circle cx="24" cy="35" r="3" :fill="color" opacity="0.6"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
