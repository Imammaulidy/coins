module.exports = {
  apps: [
    {
      name: "coins-bot",
      script: "core/bot.py",
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
