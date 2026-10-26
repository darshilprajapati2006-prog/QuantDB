import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Keep disposable optimizer output separate from the legacy tracked cache.
  cacheDir: 'node_modules/.vite-quantdb',
  // Keep React and ReactDOM on one module instance, including Vite's dev
  // optimizer. A split instance leaves the hooks dispatcher unset at runtime.
  resolve: { dedupe: ['react', 'react-dom'] },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime', 'react-dom/client'],
  },
  server: { proxy: { '/api': 'http://localhost:8000' } },
  test: { environment: 'jsdom' },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('/firebase/')) return 'firebase';
          if (id.includes('/@tanstack/')) return 'query';
          if (id.includes('/recharts/') || id.includes('/d3-') || id.includes('/victory-vendor/')) return 'charts';
          if (id.includes('/react-router/')) return 'router';
          if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/scheduler/')) return 'react';
        },
      },
    },
  },
});
