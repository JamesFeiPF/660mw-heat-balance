<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 水泵图标 -->
    <circle cx="24" cy="24" r="14" :stroke="color" stroke-width="2.5" fill="none"/>
    <!-- 泵壳 -->
    <path d="M24 10 L24 38" :stroke="color" stroke-width="2" opacity="0.5"/>
    <!-- 叶轮 -->
    <path d="M24 24 L14 14" :stroke="color" stroke-width="2.5"/>
    <path d="M24 24 L34 14" :stroke="color" stroke-width="2.5"/>
    <path d="M24 24 L34 34" :stroke="color" stroke-width="2.5"/>
    <path d="M24 24 L14 34" :stroke="color" stroke-width="2.5"/>
    <!-- 中心 -->
    <circle cx="24" cy="24" r="4" :fill="color"/>
    <!-- 进出口 -->
    <rect x="2" y="20" width="8" height="8" rx="1" :stroke="color" stroke-width="1.5" fill="none"/>
    <rect x="38" y="20" width="8" height="8" rx="1" :stroke="color" stroke-width="1.5" fill="none"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
