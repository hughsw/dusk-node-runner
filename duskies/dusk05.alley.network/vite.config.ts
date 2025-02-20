import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '0.0.0.0',
    allowedHosts: ['duskies.network'],
    //allowedHosts: ['dusk05.alley.network'],
  },
  plugins: [sveltekit()],
});
