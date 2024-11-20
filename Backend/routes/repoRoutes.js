const express = require('express');
const router = express.Router();
const { fetchCollaborators } = require('../controllers/repoController');

// 取得使用者的資料
router.get("/:owner/:repo/collaborators", fetchCollaborators);

module.exports = router;