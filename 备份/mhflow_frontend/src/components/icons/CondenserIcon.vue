<template>
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 凝汽器图标 -->
    <rect x="4" y="12" width="40" height="24" rx="3" :stroke="color" stroke-width="2.5" fill="none"/>
    <!-- 冷却管 -->
    <line x1="10" y1="18" x2="38" y2="18" :stroke="color" stroke-width="1.5" opacity="0.6"/>
    <line x1="10" y1="22" x2="38" y2="22" :stroke="color" stroke-width="1.5" opacity="0.6"/>
    <line x1="10" y1="26" x2="38" y2="26" :stroke="color" stroke-width="1.5" opacity="0.6"/>
    <line x1="10" y1="30" x2="38" y2="30" :stroke="color" stroke-width="1.5" opacity="0.6"/>
    <!-- 进出水口 -->
    <circle cx="4" cy="20" r="3" :fill="color" opacity="0.8"/>
    <circle cx="4" cy="28" r="3" :fill="color" opacity="0.8"/>
    <circle cx="44" cy="20" r="3" :fill="color" opacity="0.8"/>
    <circle cx="44" cy="28" r="3" :fill="color" opacity="0.8"/>
    <!-- 水滴 -->
    <path d="M24 14 C24 14, 22 17, 22 18.5 C22 19.9, 22.9 21, 24 21 C25.1 21, 26 19.9, 26 18.5 C26 17, 24 14, 24 14Z" :fill="color" opacity="0.5"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  color?: string
}>()
</script>
