<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 汽轮机图标 -->
    <circle cx="24" cy="24" r="16" :stroke="color" stroke-width="2.5" fill="none"/>
    <circle cx="24" cy="24" r="8" :stroke="color" stroke-width="1.5" fill="none" opacity="0.5"/>
    <!-- 叶片 -->
    <line x1="24" y1="8" x2="24" y2="16" :stroke="color" stroke-width="2"/>
    <line x1="24" y1="32" x2="24" y2="40" :stroke="color" stroke-width="2"/>
    <line x1="8" y1="24" x2="16" y2="24" :stroke="color" stroke-width="2"/>
    <line x1="32" y1="24" x2="40" y2="24" :stroke="color" stroke-width="2"/>
    <line x1="12.7" y1="12.7" x2="18.3" y2="18.3" :stroke="color" stroke-width="2"/>
    <line x1="29.7" y1="29.7" x2="35.3" y2="35.3" :stroke="color" stroke-width="2"/>
    <line x1="12.7" y1="35.3" x2="18.3" y2="29.7" :stroke="color" stroke-width="2"/>
    <line x1="29.7" y1="18.3" x2="35.3" y2="12.7" :stroke="color" stroke-width="2"/>
    <!-- 中心点 -->
    <circle cx="24" cy="24" r="3" :fill="color"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
