const axios = require("axios");
const orgsStorage = require('./orgsController');
require("dotenv").config();

// 倉庫查詢
// const fetchOrgRepos = async (req, res) => {
//   const orgName = req.params.orgName;  // This captures the 'orgName' from the route parameter
//   const token = process.env.GITHUB_TOKEN;

//   try {
//     const repos = await getOrgRepos(orgName, token);

//     const collaboratorsPromises = repos.map(repo =>
//       getCollaborators(orgName, repo.name, token).catch(error => {
//         console.error(`Failed to fetch collaborators for ${repo.name}:`, error);
//         return []; // Return an empty array in case of error
//       })
//     );

//     // Wait for all the promises to resolve
//     const allCollaborators = await Promise.all(collaboratorsPromises);

//     const reposWithCollaborators = repos.map((repo, index) => ({
//       full_name: repo.full_name,
//       description: repo.description,
//       collaborators: allCollaborators[index],
//     }));

//     res.json(reposWithCollaborators);
//   } catch (error) {
//     console.error(error.response.data.message || "Error fetching");
//     res.status(500).send(error.response.data.message || "Error fetching");
//   }
// };

const fetchUserOrgs = async (req, res) => {
  const orgName = req.params.orgName;  // This captures the 'orgName' from the route parameter
  // const token = process.env.GITHUB_TOKEN;
  const token = process.env[`ORG_${orgName}_TOKEN`]

  try {
    const user = await getOrgMembers(orgName, token);

    res.json(user);
  } catch (error) {
    console.error(error.response.data.message || "Error fetching");
    res.status(500).send(error.response.data.message || "Error fetching");
  }
}

async function getCollaborators(orgName, repoName, token) {
  const collaboratorsUrl = `https://api.github.com/repos/${orgName}/${repoName}/collaborators?affiliation=all&per_page=100`;
  try {
    const collaboratorsResponse = await axios.get(collaboratorsUrl, {
      headers: { Authorization: `token ${token}` }
    });
    const collaborators = collaboratorsResponse.data;

    // 獲取協作者全名
    const detailedCollaborators = await Promise.all(collaborators.map(async collaborator => {
      const userUrl = `https://api.github.com/users/${collaborator.login}`;
      try {
        const userResponse = await axios.get(userUrl, {
          headers: { Authorization: `token ${token}` }
        });
        return {
          login: collaborator.login,
          avatar_url: collaborator.avatar_url,
          permissions: collaborator.permissions,
          role_name: collaborator.role_name,
          name: userResponse.data.name  // 添加全名
        };
      } catch (error) {
        console.error(`Error fetching details for user ${collaborator.login}:`, error);
        return {
          login: collaborator.login,
          avatar_url: collaborator.avatar_url,
          permissions: collaborator.permissions,
          role_name: collaborator.role_name,
          name: 'Unavailable'
        };
      }
    }));

    return detailedCollaborators;
  } catch (error) {
    console.error(`Error fetching collaborators for repo ${repoName}:`, error);
    throw error;  // Re-throw the error to be caught in the calling function
  }
}

const getOrgMembers = async (orgName, token) => {
  let allRepos = [];
  let page = 1;
  let perPage = 100

  while (true) {
    const url = `https://api.github.com/orgs/${orgName}/members`;
    const response = await axios.get(url, {
      headers: { Authorization: `token ${token}` },
      params: { page, per_page: perPage }
    });
    allRepos = allRepos.concat(response.data);
    if (response.data.length < perPage) {
      break;
    }
    page++;
    await sleep(300); // 等待300毫秒再發送下一次請求
  }
  return allRepos;
};

const getOrgRepos = async (orgName, token) => {
  let allRepos = [];
  let page = 1;
  let perPage = 100

  while (true) {
    const url = `https://api.github.com/orgs/${orgName}/repos`;
    const response = await axios.get(url, {
      headers: { Authorization: `token ${token}` },
      params: { page, per_page: perPage }
    });
    allRepos = allRepos.concat(response.data);
    if (response.data.length < perPage) {
      break;
    }
    page++;
    await sleep(300); // 等待300毫秒再發送下一次請求
  }
  return allRepos;
};

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

////////////// GraphQL version //////////////
const fetchErrors = [];
const fetchEveryRepos = async (req, res) => {
  // const token = process.env.GITHUB_TOKEN;
  // const url = "https://api.github.com/user/orgs";

  try {
    const orgs = Object.keys(process.env)
      .filter(key => key.startsWith('ORG_') && key.endsWith('_TOKEN'))
      .map(key => key.slice(4, -6));

    // const response = await axios.get(url, {
    //   headers: {
    //     Authorization: `token ${token}`,
    //   },
    // });

    // const orgs = response.data;
    // const orgs = [
    //   {
    //     "login": "OLD-RD4-DWK"
    //   },
    //   {
    //     "login": "OLD-RD4-Fleet"
    //   },
    //   {
    //     "login": "IGS-ARCADE-DIVISION-RD2"
    //   },
    // ];
    const missingTokenOrgs = [];
    const permissionErrors = [];
    // const fetchErrors = [];

    // const allRepoPromises = orgs.map(async (org) => {
    //   const orgName = org;
    //   const tokenKey = `ORG_${orgName}_TOKEN`; // 各組織的 token key
    //   const orgToken = process.env[tokenKey];

    //   if (!orgToken) {
    //     console.warn(`未提供組織 Token: ${orgName}`);
    //     missingTokenOrgs.push(orgName);
    //     return null;
    //   }

    //   try {
    //     let slowlyFetch = true;
    //     const reposWithCollaborators = await fetchAllReposAndCollaborators(orgName, orgToken, slowlyFetch);
    //     return reposWithCollaborators;
    //   } catch (error) {
    //     const errorMsg = error.response?.data?.message || error.message || "Error fetching";
    //     console.error(`Error fetching for org ${orgName}: ${errorMsg}`);
    //     if (error.response?.status === 401 || error.response?.status === 403) {
    //       permissionErrors.push(`Organization: ${orgName}, Error: ${errorMsg}`);
    //     } else if (error.response?.status === 403 && errorMsg.includes('API rate limit exceeded')) {
    //       console.error('API rate limit exceeded. Stopping further requests.');
    //       return res.status(403).json({
    //         error: errorMsg,
    //         documentation_url: error.response?.data?.documentation_url,
    //         status: 403
    //       });
    //     } else {
    //       fetchErrors.push(`Organization: ${orgName}, Error: ${errorMsg}`);
    //     }
    //     return null;
    //   }
    // });

    const retryFetch = async (orgName, orgToken, retries = 3) => {
      let attempt = 0;
      while (attempt < retries) {
        try {
          let slowlyFetch = true;
          const reposWithCollaborators = await fetchAllReposAndCollaborators(orgName, orgToken, slowlyFetch);
          return reposWithCollaborators;
        } catch (error) {
          const errorMsg = error.response?.data?.message || error.message || "Error fetching";
          console.error(`Error fetching for org ${orgName} (Attempt ${attempt + 1}): ${errorMsg}`);

          if (error.response?.status === 401 || error.response?.status === 403) {
            permissionErrors.push(`Organization: ${orgName}, Error: ${errorMsg}`);
            break; // No point in retrying for authorization errors
          } else if (error.response?.status === 403 && errorMsg.includes('API rate limit exceeded')) {
            console.error('API rate limit exceeded. Stopping further requests.');
            return res.status(403).json({
              error: errorMsg,
              documentation_url: error.response?.data?.documentation_url,
              status: 403
            });
          } else {
            fetchErrors.push(`Organization: ${orgName}, Error: ${errorMsg}`);
          }

          attempt++;
        }
      }
      return null;
    };

    const allRepoPromises = orgs.map(async (org) => {
      const orgName = org;
      const tokenKey = `ORG_${orgName}_TOKEN`;
      const orgToken = process.env[tokenKey];

      if (!orgToken) {
        console.warn(`未提供組織 Token: ${orgName}`);
        missingTokenOrgs.push(orgName);
        return null;
      }

      return retryFetch(orgName, orgToken);
    });

    const allRepo = await Promise.all(allRepoPromises);

    const validRepos = allRepo.filter(repo => repo !== null);
    let allRepoMap = validRepos.flatMap((el) => {
      return el.flatMap(e => {
        if (e && e.owner && e.owner.login) {
          return {
            owner: e.owner.name,
            repo: e.name,
            collaborators: e.collaborators,
            description: e.description,
            projectName: e.customProperties.find(cp => cp.property_name === 'project')?.value,
            projectCategory: e.customProperties.find(cp => cp.property_name === 'category')?.value
          };
        } else {
          return [];
        }
      });
    });

    let result = {};
    allRepoMap.forEach(value => {
      if (value.owner) {
        if (!result[value.owner]) {
          result[value.owner] = [];
        }
        result[value.owner].push(value);
      }
    });

    let messages = [];
    if (missingTokenOrgs.length > 0) {
      messages.push(`未提供 Token 組織: ${missingTokenOrgs.join(', ')}`);
    }
    if (permissionErrors.length > 0) {
      messages.push(...permissionErrors);
    }
    if (fetchErrors.length > 0) {
      messages.push(...fetchErrors);
    }

    res.json({
      repos: result,
      message: messages.length > 0 ? messages.join('; ') : null
    });
  } catch (error) {
    const status = error.response?.status || 500;
    const message = error.response?.data?.message || error.message || "Error fetching repositories";
    console.error(`Error fetching repositories: ${message}`);
    res.status(status).json({
      error: message,
      status: status
    });
  }
};

const fetchOrgReposWithCollaborators = async (req, res) => {
  const orgName = req.params.orgName;
  const tokenKey = `ORG_${orgName}_TOKEN`; // 各組織的 token key
  const token = process.env[tokenKey];

  if (!token) {
    return res.json(
      {
        error: "Access token not provided.",
        status: 2
      }
    );
  }

  try {
    const reposWithCollaborators = await fetchAllReposAndCollaborators(orgName, token);
    res.json(reposWithCollaborators);
  } catch (error) {
    console.error(error.response.data.message ? error.response.data.message : "Error fetching");
    res.status(500).json(
      {
        error: error.response.data.message ? error.response.data.message : "Error fetching",
        status: error.response.status
      }
    );
  }
};

async function fetchAllReposAndCollaborators(orgName, token, slowlyFetch) {
  let allRepos = [];
  let endCursor = null; // 初始化為 null, 這表示查詢的起始點
  let hasNextPage = true;

  while (hasNextPage) {
    const { repos, cursor, nextPage } = await fetchReposPage(orgName, token, endCursor, slowlyFetch);
    allRepos = allRepos.concat(repos);
    endCursor = cursor;
    hasNextPage = nextPage;
  }

  return allRepos;
}

async function fetchReposPage(orgName, token, afterCursor, slowlyFetch) {
  const graphqlQuery = {
    query: `
      query ($orgName: String!, $afterCursor: String) {
        organization(login: $orgName) {
          repositories(first: 50, after: $afterCursor) {
            edges {
              node {
                name
                description
                owner {
                  __typename
                  ... on User {
                    login
                    avatarUrl
                    name
                  }
                  ... on Organization {
                    login
                    avatarUrl
                    name
                  }
                }
                object(expression: "HEAD:README.md") {
                  ... on Blob {
                    text
                  }
                }
                collaborators(first: 50) {
                  edges {
                    node {
                      login
                      avatarUrl
                      name
                    }
                  }
                }
              }
              cursor
            }
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
      }
    `,
    variables: {
      orgName: orgName,
      afterCursor: afterCursor
    }
  };

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const response = await axios.post('https://api.github.com/graphql', JSON.stringify(graphqlQuery), { headers });
  const repos = await Promise.all(response.data.data.organization.repositories.edges.map(async (edge) => {
    return fetchRepoDetails(orgName, edge, token, slowlyFetch);
  }));

  const pageInfo = response.data.data.organization.repositories.pageInfo;

  return {
    repos: repos,
    cursor: pageInfo.endCursor,
    nextPage: pageInfo.hasNextPage
  };
}

const fetchRepoDetails = async (orgName, edge, token, slowlyFetch, retryCount = 0) => {
  const maxRetries = 3; // 最大重试次数

  const fetchCollaborators = async () => {
    const collaboratorsUrl = `https://api.github.com/repos/${orgName}/${edge.node.name}/collaborators?per_page=100`;
    if (slowlyFetch) await sleep(1000);
    return axios.get(collaboratorsUrl, {
      headers: { Authorization: `token ${token}` }
    });
  };

  const fetchProperties = async () => {
    const propertiesUrl = `https://api.github.com/repos/${orgName}/${edge.node.name}/properties/values`;
    if (slowlyFetch) await sleep(1000);
    return axios.get(propertiesUrl, {
      headers: { Authorization: `token ${token}` }
    });
  };

  try {
    const [collaboratorsResponse, propertiesResponse] = await Promise.all([fetchCollaborators(), fetchProperties()]);

    const collaborators = collaboratorsResponse.data;
    const properties = propertiesResponse.data;

    const collaboratorsInfo = collaborators.map(collab => ({
      login: collab.login,
      avatar_url: collab.avatar_url,
      name: edge.node.collaborators.edges.find(collabEdge => collabEdge.node.login === collab.login)?.node.name,
      role_name: collab.role_name
    }));

    return {
      name: edge.node.name,
      description: edge.node.description,
      owner: edge.node.owner,
      collaborators: collaboratorsInfo,
      customProperties: properties
    };
  } catch (error) {
    console.error(`無法獲取倉庫 ${edge.node.name} (組織: ${orgName}): ${error.cause || error.response?.data || error.message}`);

    if ((error.code === 'ETIMEDOUT' || error.response?.status === 502 || error.response?.status === 504) && retryCount < maxRetries) {
      console.warn(`Request for repo ${edge.node.name} failed with status code ${error.response?.status}. Retrying (${retryCount + 1}/${maxRetries})...`);
      await sleep(1000 * Math.pow(2, retryCount)); // 等待一段时间再重试（指数回退）
      return fetchRepoDetails(orgName, edge, token, slowlyFetch, retryCount + 1); // 重试请求
    } else {
      fetchErrors.push(`無法獲取倉庫 ${edge.node.name} (組織: ${orgName}): ${error.cause || error.response?.data || error.message}`);
      return {
        name: edge.node.name,
        description: edge.node.description,
        collaborators: [],
        customProperties: []
      };
    }

    // // return error
    // return {
    //   name: edge.node.name,
    //   description: edge.node.description,
    //   collaborators: [],
    //   customProperties: []
    // };
  }
};

module.exports = {
  // fetchOrgRepos,
  fetchUserOrgs,
  fetchOrgReposWithCollaborators,
  fetchEveryRepos
};
