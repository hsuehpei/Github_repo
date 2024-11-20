const express = require('express');
const router = express.Router();
const { fetchRepositories, fetchOrgs, fetchUserOrgs } = require('../controllers/userController');

// 取得使用者的資料
router.get("/repos", fetchRepositories);

// 取得使用者的組織
router.get("/orgs", fetchOrgs);

// 取得使用者的組織的倉庫
router.get("/:orgName/:username/repos", fetchUserOrgs);

module.exports = router;