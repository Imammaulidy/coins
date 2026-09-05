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
  return '127.0.0.1';
}

const localIp = getLocalIp();
const rootDir = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

// Deteksi Python interpreter yang valid secara dinamis (Cross-Platform)
let pythonPath = 'python';
if (isWin) {
  const venvPythonw = path.resolve(rootDir, '.venv', 'Scripts', 'pythonw.exe');
  const venvPython = path.resolve(rootDir, '.venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvPythonw)) {
    pythonPath = venvPythonw;
  } else if (fs.existsSync(venvPython)) {
    pythonPath = venvPython;
  } else {
    pythonPath = 'python';
  }
} else {
  // Linux / Android Termux
  const venvPython = path.resolve(rootDir, '.venv', 'bin', 'python');
  if (fs.existsSync(venvPython)) {
    pythonPath = venvPython;
  } else {
    pythonPath = 'python';
  }
}

// Deteksi binary cloudflared secara dinamis (Cross-Platform)
let cloudflaredPath = 'cloudflared';
if (isWin) {
  const winBin = path.resolve(__dirname, 'bin', 'cloudflared.exe');
  if (fs.existsSync(winBin)) {
    cloudflaredPath = winBin;
  }
} else {
  const termuxBin = path.resolve(__dirname, 'bin', 'cloudflared');
  const prefixBin = '/data/data/com.termux/files/usr/bin/cloudflared';
  if (fs.existsSync(prefixBin)) {
    cloudflaredPath = prefixBin;
  } else if (fs.existsSync(termuxBin)) {
    cloudflaredPath = termuxBin;
  }
}

// Tentukan argumen tunnel: gunakan loopback 127.0.0.1 agar kebal terhadap perubahan IP dinamis/mode pesawat
let tunnelArgs = `tunnel run --url http://127.0.0.1:5000 triomerak`;
const tokenFile = path.resolve(rootDir, 'cloudflare_token.txt');
let hasToken = false;
if (fs.existsSync(tokenFile)) {
  const token = fs.readFileSync(tokenFile, 'utf8').trim();
  if (token) {
    tunnelArgs = `tunnel run --token ${token}`;
    hasToken = true;
  }
}

const homeDir = os.homedir();
const hasCert = fs.existsSync(path.resolve(homeDir, '.cloudflared', 'cert.pem'));
const tunnelAutoRestart = hasToken || hasCert;

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
      autorestart: tunnelAutoRestart,
      watch: false
    }
  ]
};
