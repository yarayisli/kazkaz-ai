import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_');
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000';
  return ({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          if (id.includes('@firebase/auth') || id.includes('firebase/auth')) return 'firebase-auth';
          if (id.includes('@firebase/firestore') || id.includes('firebase/firestore')) return 'firebase-firestore';
          if (id.includes('@firebase/app') || id.includes('firebase/app')) return 'firebase-core';
          if (id.includes('firebase')) return 'firebase-shared';
          if (id.includes('motion')) return 'motion';
          if (id.includes('lucide-react')) return 'icons';
          return undefined;
        },
      },
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  });
});
