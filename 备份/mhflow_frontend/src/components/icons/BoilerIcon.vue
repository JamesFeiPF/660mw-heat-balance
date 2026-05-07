<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 锅炉图标 -->
    <rect x="6" y="8" width="36" height="32" rx="4" :stroke="color" stroke-width="2.5" fill="none"/>
    <rect x="10" y="12" width="28" height="24" rx="2" :stroke="color" stroke-width="1.5" fill="none" opacity="0.5"/>
    <!-- 火焰 -->
    <path d="M18 30 C18 26, 22 22, 22 18 C22 22, 26 22, 26 18 C26 22, 30 26, 30 30 C30 33, 27 35, 24 35 C21 35, 18 33, 18 30Z" :fill="color" opacity="0.8"/>
    <!-- 蒸汽 -->
    <path d="M20 12 C20 10, 22 10, 22 8" stroke="white" stroke-width="1.5" opacity="0.6"/>
    <path d="M26 12 C26 10, 28 10, 28 8" stroke="white" stroke-width="1.5" opacity="0.6"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
