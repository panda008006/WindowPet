const http = require('http');
const fs = require('fs');
const path = require('path');

const dist = path.resolve(__dirname, 'website/dist');

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.json': 'application/json; charset=utf-8',
  '.mp4': 'video/mp4'
};

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/pet-api')) {
    const targetPath = req.url.replace(/^\/pet-api/, '') || '/';
    const proxyReq = http.request(
      {
        hostname: '127.0.0.1',
        port: 8787,
        path: targetPath,
        method: req.method,
        headers: { ...req.headers, host: '127.0.0.1:8787' },
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res);
      }
    );
    proxyReq.on('error', (err) => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Backend API unavailable: ' + err.message }));
    });
    req.pipe(proxyReq);
    return;
  }

  let urlPath = req.url.split('?')[0].split('#')[0];
  if (urlPath === '/' || !urlPath) urlPath = '/index.html';
  const filePath = path.join(dist, urlPath);

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': mime[ext] || 'application/octet-stream',
      'Access-Control-Allow-Origin': '*'
    });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // SPA fallback
    const indexPath = path.join(dist, 'index.html');
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      });
      fs.createReadStream(indexPath).pipe(res);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found');
    }
  }
});

const PORT = 4173;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`WindowPet preview server listening on http://localhost:${PORT}`);
});
