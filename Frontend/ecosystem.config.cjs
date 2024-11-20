module.exports = {
    apps : [{
      name: "Frontend",
      script: "npm",
      args: "run start",
      watch: true,
      autorestart: true,
      restart_delay: 1000
    }]
  };
  