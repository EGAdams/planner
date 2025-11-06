const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = 3000;
const ADMIN_DASHBOARD_PORT = 3030;

// Proxy API requests to the Admin Dashboard backend
app.use('/api', createProxyMiddleware({
  target: `http://localhost:${ADMIN_DASHBOARD_PORT}`,
  changeOrigin: true,
  ws: true, // Proxy websockets as well for SSE
}));

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Catch-all for HTML5 pushState routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server Monitor App running on http://localhost:${PORT}`);
});
