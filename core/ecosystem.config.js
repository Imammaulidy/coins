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

// Gunakan pythonw.exe agar murni berjalan di latar belakang tanpa memunculkan jendela console/terminal hitam kosong
const pythonwPath = path.resolve(rootDir, '.venv', 'Scripts', 'pythonw.exe');
const pythonExePath = path.resolve(rootDir, '.venv', 'Scripts', 'python.exe');
const pythonPath = fs.existsSync(pythonwPath) ? pythonwPath : pythonExePath;

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
      windowsHide: true,
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
      windowsHide: true,
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
      windowsHide: true,
      autorestart: true,
      watch: false
    }
  ]
};
