export default {
  root: "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/c401r2",
  esbuild: { jsx: "automatic" },
  define: { __HOLDSPEAK_BUILD__: JSON.stringify("canvas") },
  resolve: { alias: { "@w": "/Users/karol/dev/tools/wt-philo-4-01/web/src", react: "/Users/karol/dev/tools/wt-philo-4-01/web/node_modules/react", "react-dom": "/Users/karol/dev/tools/wt-philo-4-01/web/node_modules/react-dom" }, dedupe: ["react", "react-dom"] },
  server: { host: "127.0.0.1", port: 4417, strictPort: true, fs: { allow: ["/Users/karol/dev/tools/wt-philo-4-01/web", "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/c401r2"] } },
};
