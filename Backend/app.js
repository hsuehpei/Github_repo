const express = require("express");
const cors = require("cors");
const app = express();
const axios = require("axios");

const userRoutes = require('./routes/userRoutes');
const organizationRoutes = require('./routes/organizationRoutes');
const repoRoutes = require('./routes/repoRoutes');

// 日誌記錄中間件
function logMiddleware(req, res, next) {
  const startTime = Date.now();
  res.on('finish', () => {
      const duration = Date.now() - startTime;
      console.log(`${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`);
      console.log(`time: ${new Date().toLocaleString()}`);
      console.log(`from: ${req.ip}`);
  });
  next();
}

// 註冊中間件
app.use(logMiddleware);

app.use(cors());
app.use(express.json()); // Middleware for parsing JSON bodies

// 註冊路由
app.use("/rate_limit", async (req, res) => {
  const orgName = req.query.orgName;
  const tokenKey = `ORG_${orgName.toUpperCase()}_TOKEN`; // 各組織的 token key
  const token = process.env[tokenKey] || process.env.GITHUB_TOKEN;

  const url = `https://api.github.com/rate_limit`;
  // const token = process.env.GITHUB_TOKEN;

  const response = await axios.get(url, {
    headers: { Authorization: `token ${token}` },
  });

  res.json(response.data);
});

app.use("/user", userRoutes);
app.use("/orgs", organizationRoutes);
app.use("/repos", repoRoutes);

// 啟動服務器
const PORT = process.env.PORT || 7800;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
