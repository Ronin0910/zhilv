<template>
  <div id="app">
    <a-layout style="min-height: 100vh">
      <a-layout-header class="app-header">
        <div class="header-brand" @click="router.push('/')">
          <span class="brand-icon">🌍</span>
          <span class="brand-text">智能旅行助手</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-link" active-class="nav-active">
            🏖️ 行程规划
          </router-link>
          <router-link to="/qa" class="nav-link" active-class="nav-active">
            🤖 智能问答
          </router-link>
        </nav>
      </a-layout-header>
      <a-layout-content style="padding: 0">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align: center; background: #f0f2f5">
        智能旅行助手 ©2026 基于 LangChain + RAG 框架
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
</style>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.header-brand:hover {
  opacity: 0.85;
}
.brand-icon {
  font-size: 28px;
}
.brand-text {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
}
.header-nav {
  display: flex;
  gap: 8px;
}
.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  padding: 8px 20px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.25s ease;
}
.nav-link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
}
.nav-active {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }
  .brand-text {
    font-size: 16px;
  }
  .nav-link {
    padding: 6px 14px;
    font-size: 13px;
  }
}
</style>

