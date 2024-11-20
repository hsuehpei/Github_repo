const axios = require("axios");
const orgsStorage = require('./orgsController');
require("dotenv").config();

const fetchRepositories = async (req, res) => {
  const token = process.env.GITHUB_TOKEN;
  const url = "https://api.github.com/user/repos";

  try {
    const response = await axios.get(url, {
      headers: {
        Authorization: `token ${token}`,
      },
    });
    res.json(response.data);
  } catch (error) {
    console.error("Error fetching:", error.response.data);
    res.status(500).send(error.response.data.message || "Error fetching");
  }
}

const fetchOrgs = async (req, res) => {
  // const token = process.env.GITHUB_TOKEN;
  // const url = "https://api.github.com/user/orgs";

  try {
    // Step 1: Fetch the list of organizations
    // const response = await axios.get(url, {
    //   headers: {
    //     Authorization: `token ${token}`,
    //   },
    // });

    // const orgs = response.data;

    // 從 process.env 動態獲取組織名稱
    const orgs = Object.keys(process.env)
      .filter(key => key.startsWith('ORG_') && key.endsWith('_TOKEN'))
      .map(key => key.slice(4, -6));

    console.log("Organizations to fetch:", orgs);

    // Step 2: Fetch detailed info for each organization
    const orgDetailsPromises = orgs.map(async (org) => {
      try {
        const token = process.env[`ORG_${org}_TOKEN`];
        if (!token) {
          throw new Error(`Token for organization ${org} not found.`);
        }
        const orgUrl = `https://api.github.com/orgs/${org}`;
        const orgResponse = await axios.get(orgUrl, {
          headers: {
            Authorization: `token ${token}`,
          },
        });
        return orgResponse.data;
      } catch (error) {
        console.error(`Error fetching details for organization ${org}:`, error.response?.data || error.message);
        throw error;
      }
    });

    const orgDetails = await Promise.all(orgDetailsPromises);

    // Step 3: Respond with the detailed info
    res.json(orgDetails);
  } catch (error) {
    console.error("Error fetching organizations:", error.response?.data || error.message);
    res.status(500).send(error.response?.data?.message || "Error fetching organizations");
  }
};

const fetchUserOrgs = async (req, res) => {
  const orgName = req.params.orgName;
  const username = req.params.username;
  const token = process.env.GITHUB_TOKEN;

  try {
    const repos = await getOrgRepos(orgName, token);
    const userPermissions = await Promise.all(repos.map(async (repo) => {
      const repoUrl = `https://api.github.com/repos/${orgName}/${repo.name}/collaborators/${username}/permission`;
      try {
        const repoResponse = await axios.get(repoUrl, {
          headers: { Authorization: `token ${token}` }
        });
        return {
          repository: repo.name,
          permission: repoResponse.data.permission
        };
      } catch (repoError) {
        console.error(`Error accessing repo ${repo.name}:`, repoError.response ? repoError.response.status : repoError);
        return { repository: repo.name, permission: "error", error: repoError.response ? repoError.response.status : 'Unknown error' };
      }
    }));

    const filteredPermissions = userPermissions.filter(permission => permission.permission !== "none");

    res.json(filteredPermissions);
  } catch (error) {
    console.error('Error retrieving organization repositories:', error.response ? error.response.status : error);
    res.status(500).send(`Error retrieving repository information: ${error.message || error}`);
  }
};

const getOrgRepos = async (orgName, token) => {
  let allRepos = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const url = `https://api.github.com/orgs/${orgName}/repos`;
    const response = await axios.get(url, {
      headers: { Authorization: `token ${token}` },
      params: { page, per_page: 100 }
    });
    allRepos = allRepos.concat(response.data);
    hasMore = response.data.length === 100;
    page++;
    await sleep(300); // 等待300毫秒以避免速率限制
  }

  return allRepos;
};

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

module.exports = {
  fetchRepositories,
  fetchOrgs,
  fetchUserOrgs
};
