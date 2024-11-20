const express = require('express');
const router = express.Router();
// const { fetchOrgRepos, fetchUserOrgs, fetchOrgReposWithCollaborators, fetchEveryRepos } = require('../controllers/organizationController');
const { fetchUserOrgs, fetchOrgReposWithCollaborators, fetchEveryRepos } = require('../controllers/organizationController');

// 獲取組織的所有倉庫和它們的Collaborators
// EX: /orgs/IGS-ARCADE-DIVISION-RD3/repos
// router.get("/:orgName/repos", fetchOrgRepos);
router.get("/:orgName/repos", fetchOrgReposWithCollaborators);

// 獲取組織的所有成員
router.get("/:orgName/members", fetchUserOrgs);

// 獲取所有組織的所有倉庫
router.get("/everyrepos", fetchEveryRepos);

module.exports = router;