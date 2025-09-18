const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy for your backend API (including auth)
  app.use(
    ['/token', '/auth', '/login', '/activity-data', '/activity-summary', '/top-window-titles', '/productivity-analysis', '/daily-hours'],
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
    })
  );

  // Proxy for ActivityWatch API
  app.use(
    '/aw-api',
    createProxyMiddleware({
      target: 'http://localhost:5600',
      changeOrigin: true,
      pathRewrite: {
        '^/aw-api': '/api/0',
      },
    })
  );
};