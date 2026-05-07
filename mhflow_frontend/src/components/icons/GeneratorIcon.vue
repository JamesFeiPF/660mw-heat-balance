<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 发电机图标 -->
    <circle cx="24" cy="24" r="16" :stroke="color" stroke-width="2.5" fill="none"/>
    <!-- 定子 -->
    <circle cx="24" cy="24" r="10" :stroke="color" stroke-width="1.5" fill="none" opacity="0.5"/>
    <!-- 转子 -->
    <circle cx="24" cy="24" r="4" :fill="color"/>
    <!-- 闪电 -->
    <path d="M26 14 L20 24 L25 24 L22 34 L30 22 L25 22 Z" :fill="color" opacity="0.8"/>
    <!-- 接线端 -->
    <rect x="38" y="18" width="6" height="4" rx="1" :fill="color" opacity="0.6"/>
    <rect x="38" y="26" width="6" height="4" rx="1" :fill="color" opacity="0.6"/>
    <line x1="38" y1="20" x2="40" y2="20" :stroke="color" stroke-width="1.5"/>
    <line x1="38" y1="28" x2="40" y2="28" :stroke="color" stroke-width="1.5"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
