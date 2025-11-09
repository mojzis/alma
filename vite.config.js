import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'alma/static/dist',
    rollupOptions: {
      input: {
        editor: 'alma/static/js/editor.js'
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  optimizeDeps: {
    exclude: [
      '@codemirror/state',
      '@codemirror/view'
    ]
  }
})
