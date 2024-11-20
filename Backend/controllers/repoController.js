const axios = require("axios");
require("dotenv").config();

const fetchCollaborators = async (req, res) => {
  const token = process.env.GITHUB_TOKEN;
  const owner = req.params.owner;
  const repo = req.params.repo;
  let allCollaborators = [];
  let page = 1;
  let hasMore = true;

  try {
    while (hasMore) {
      const url = `https://api.github.com/repos/${owner}/${repo}/collaborators`;
      const response = await axios.get(url, {
        headers: {
          Authorization: `token ${token}`,
        },
        params: { page, per_page: 100 }
      });

      allCollaborators = allCollaborators.concat(response.data);
      hasMore = response.data.length === 100;  // 檢查是否還有更多頁面
      page++;  // 準備請求下一頁
      await sleep(300); // 等待300毫秒以避免速率限制
    }
    res.json(allCollaborators);
  } catch (error) {
    console.error("Error fetching:", error.response.data);
    res.status(500).send(error.response.data.message || "Error fetching");
  }
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

module.exports = {
  fetchCollaborators
};
