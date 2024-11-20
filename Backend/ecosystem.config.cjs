module.exports = {
    apps : [{
      name: "Backend",
      script: "npm",
      args: "run start",
      watch: true,
      autorestart: true,
      restart_delay: 1000
    }]
  };
  