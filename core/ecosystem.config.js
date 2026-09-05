const path = require('path');
const fs = require('fs');
const os = require('os');

// Deteksi IP Lokal LAN aktif
function getLocalIp() {
  try {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
      for (const iface of interfaces[name]) {
        if (iface.family === 'IPv4' && !iface.internal) {
          return iface.address;
        }
      }
    }
  } catch (e) {}
  return '192.168.1.20';
}

const localIp = getLocalIp();
const rootDir = path.resolve(__dirname, '..');
const pythonPath = path.resolve(rootDir, '.venv', 'Scripts', 'python.exe');
const cloudflaredPath = path.resolve(__dirname, 'bin', 'cloudflared.exe');

// Tentukan argumen tunnel
let tunnelArgs = `tunnel run --url http://${localIp}:5000 triomerak`;
const tokenFile = path.resolve(rootDir, 'cloudflare_token.txt');
if (fs.existsSync(tokenFile)) {
  const token = fs.readFileSync(tokenFile, 'utf8').trim();
  if (token) {
    tunnelArgs = `tunnel run --token ${token}`;
  }
}

module.exports = {
  apps: [
    {
      name: 'coins-server',
      script: 'api_server.py',
      cwd: __dirname,
      interpreter: pythonPath,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        FLASK_ENV: 'production'
      }
    },
    {
      name: 'coins-bot',
      script: 'bot.py',
      cwd: __dirname,
      interpreter: pythonPath,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'coins-tunnel',
      script: cloudflaredPath,
      args: tunnelArgs,
      cwd: __dirname,
      interpreter: 'none',
      autorestart: true,
      watch: false
    }
  ]
};
