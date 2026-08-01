const target = process.env['HERMES_PROXY_TARGET'] ?? 'http://localhost:8000';

module.exports = {
  '/api': {
    target,
    secure: false,
    changeOrigin: true,
    logLevel: 'warn',
  },
};
