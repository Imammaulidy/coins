const path = require("path");

module.exports = {
  apps: [
    {
      name: "coins-bot",
      script: path.join(__dirname, "bot.py"),
      cwd: path.join(__dirname, ".."),
      interpreter: "python",
      autorestart: true,
      watch: false,
      max_memory_restart: "300M",
      env: {
        RISH_APPLICATION_ID: "com.termux",
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};
