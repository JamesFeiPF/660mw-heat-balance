<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 管道图标 -->
    <rect x="4" y="18" width="40" height="12" rx="6" :stroke="color" stroke-width="2.5" fill="none"/>
    <!-- 流动箭头 -->
    <path d="M14 24 L20 20 L20 28 Z" :fill="color" opacity="0.7"/>
    <path d="M28 24 L34 20 L34 28 Z" :fill="color" opacity="0.7"/>
    <!-- 法兰 -->
    <line x1="4" y1="16" x2="4" y2="32" :stroke="color" stroke-width="2"/>
    <line x1="44" y1="16" x2="44" y2="32" :stroke="color" stroke-width="2"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
