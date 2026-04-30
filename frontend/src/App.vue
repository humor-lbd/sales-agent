<!--
文件作用：
- 作为 Vue 根组件，承载页面路由出口和顶层过渡效果。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
