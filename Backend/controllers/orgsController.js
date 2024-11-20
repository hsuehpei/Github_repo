// orgsController.js
let orgs = [];

const setOrgs = (newOrgs) => {
    orgs = newOrgs;
};

const getOrgs = () => {
    return orgs;
};

module.exports = {
    setOrgs,
    getOrgs,
};