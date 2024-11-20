<template>
  <div class="main">
    <el-container>
      <el-header class="header">
        <el-col :span="12">
          <div class="title" @click="getLimit()">Github分倉儀表板</div>
        </el-col>
        <el-col :span="12">
          <exportCSV 
            :ALL_REPOSITORIES="ALL_REPOSITORIES"
            :readyToDownload="readyToDownload"
            :orgPick="orgPick"
            :loading="loading"
            :csvtype="'all'"
            @getEveryOrgsRepo="getEveryOrgsRepo"
            @resetDownloadStatus="readyToDownload = false"
          />        
        </el-col>
      </el-header>
      <el-container class="container">
        <el-aside :width="asideWidth">
          <el-button @click="isCollapsed = !isCollapsed">
            <el-icon>
              <Expand v-if="isCollapsed"/>
              <Fold v-else/>
            </el-icon>
          </el-button>
          <el-menu
            class="el-menu-vertical-demo"
          >
            <el-menu-item 
              v-for="(item, index) in orgsList"
              :disabled="loading.table"
              :key="index"
              :index="index.toString()"
              @click="onClickOrgs(item)"
            >
              <img :src="item.avatar_url" alt="" class="avatar">
              <template #title>{{ item.name || item.login }}</template>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main v-if="orgsList.length > 0">

          <el-row v-show="orgPick">
            <el-col :span="12" class="mb-10">
              <div class="fs-22"><span class="fw-b">{{ orgPick }}</span></div>
            </el-col>
            <el-col :span="12">
              <exportCSV 
                :REPOSITORIES="REPOSITORIES"
                :orgPick="orgPick"
                :loading="loading"
              />
            </el-col>
            <el-col :span="24" class="mb-10">
              <el-radio-group v-model="orgsType" size="large">
                <el-radio-button
                  v-for="item in orgsTypeOptions"
                  :disabled="loading.table"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                >
                </el-radio-button>
              </el-radio-group>
            </el-col>
            <el-col :span="24">
              <el-row class="role-lists">
                <el-col :span="16">
                  <div v-if="orgPick">
                    最後更新時間：{{ updateDate }}
                    <el-button @click="getOrgRepos(orgPick)" :loading="loading.table" style="height: 30px; width: 30px;">
                      <el-icon :size="20" v-if="!loading.table">
                        <RefreshRight />
                      </el-icon>
                    </el-button>
                  </div>
                </el-col>
              </el-row>
            </el-col>
            <el-col :span="24">
              <el-row class="role-lists jc-e">
                <div class="admin-color">A: Admin</div>
                <div class="maintain-color">M: Maintain</div>
                <div class="write-color">W: Write</div>
                <div class="triage-color">T: Triage</div>
                <div class="read-color">R: Read</div>
              </el-row>
            </el-col>
          </el-row>

          <el-table v-if="orgsType === 'repo'" v-loading="loading.table" :data="REPOSITORIES" :empty-text="noDataDisplayText" style="width: 100%">
            <el-table-column label="倉庫" width="300">
              <template #default="scope">
                <div class="first-column-text">{{ scope.row.repo }}</div>
                <div>{{ scope.row.description }}</div>
              </template>
            </el-table-column>            
            <el-table-column label="專案" width="300">
              <template #default="scope">
                <div>{{ scope.row.projectName ? scope.row.projectName : '--' }}</div>
              </template>
            </el-table-column>            
            <el-table-column label="分倉類別" width="300">
              <template #default="scope">
                <div>{{ scope.row.projectCategory ? scope.row.projectCategory : '--' }}</div>
              </template>
            </el-table-column>            
            <el-table-column label="存取人員">
              <template #default="scope">
                <div v-for="(item, index) in scope.row.collaborators" :key="index">
                  <span :class="roleInfo(item.role_name).colorClass">
                    ({{ roleInfo(item.role_name).abbreviation }})
                  </span>
                  <img :src="item.avatar_url" alt="" class="avatar ml-5">
                  <a class="second-column-text" @click="getUserOrgs(item)">
                    <span>{{ formatUndefinedName(item.name, item.login) }}</span>
                  </a>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-table v-if="orgsType === 'user'" v-loading="loading.table" :data="USERS" :empty-text="noDataDisplayText" style="width: 100%">
            <el-table-column label="存取人員">
              <template #default="scope">
                <el-row>
                  <img :src="scope.row.avatar_url" alt="" class="avatar">
                  <div class="first-column-text">
                    <span>{{ formatUndefinedName(scope.row.name, scope.row.login) }}</span>
                  </div>
                </el-row>
              </template>
            </el-table-column>
            <el-table-column label="倉庫">
              <template #default="scope">
                <div v-for="(owner, index) in scope.row.details" :key="index" @click="">
                  <span :class="roleInfo(owner.role_name).colorClass">
                    ({{ roleInfo(owner.role_name).abbreviation }})
                  </span>
                  <a class="second-column-text" @click="getRepoUser(owner)">{{ owner.repo }} </a>                  
                </div>
              </template>
            </el-table-column>
          </el-table>

        </el-main>
        
        <!-- 使用者權限跳窗 -->
        <el-dialog
          v-model="userPermission.popup"
          title="使用者權限"
          width="50%">
          <div v-if="loading.userPermission">
            <p>資料載入中, 請稍後...</p>
          </div>          
          <div v-else-if="userPermission.repos.length > 0">
            <el-row class="ai-c">
              <img :src="userPermission.avatar_url" alt="" class="avatar">
              <h2>{{ formatUndefinedName(userPermission.name, userPermission.login) }}</h2>
            </el-row>
            <div v-for="repo in userPermission.repos" :key="repo.id">
              <p>
                <span :class="roleInfo(repo.permission).colorClass" class="mr-5">({{ roleInfo(repo.permission).abbreviation }})</span> 
                <span>{{ repo.repository }}</span>
              </p>
            </div>
          </div>
          <div v-else>
            <p>No repositories found or no permissions available.</p>
          </div>
        </el-dialog>

        <!-- 倉庫權限跳窗 -->
        <el-dialog
          v-model="repoPermission.popup"
          title="倉庫權限"
          width="50%">
          <div v-if="loading.repoPermission">
            <p>資料載入中, 請稍後...</p>
          </div>
          <div v-else-if="repoPermission.collaborators.length > 0">
            <el-row class="ai-c">
              <h2>{{ repoPermission.repo }}</h2>
            </el-row>
            <div v-for="collaborators in repoPermission.collaborators">
              <el-row class="pb-5">
                <span :class="roleInfo(collaborators.role_name).colorClass">({{ roleInfo(collaborators.role_name).abbreviation }})</span> 
                <img :src="collaborators.avatar_url" alt="" class="avatar ml-5">
                <!-- <span class="">{{ collaborators.login }}</span> -->
                <span>{{ findNameByLogin(collaborators.login) }}</span>
              </el-row>
            </div>
          </div>
          <div v-else>
            <p>No repositories found or no permissions available.</p>
          </div>
        </el-dialog>

        <!-- API 呼叫剩餘次數跳窗 -->
        <el-dialog
          v-model="showApiLimit"
          :title="orgPick + ' TOKEN API 呼叫限制'"
          width="50%">
          <div>
            <ul>
              <li>
                <span>可使用次數:</span>
                {{ limitation.rate.limit }}
              </li>
              <li>
                <span>已使用次數:</span>
                {{ limitation.rate.used }}
              </li>
              <li class="red">
                <span>剩餘次數:</span>
                {{ limitation.rate.remaining }}
              </li>
              <li>
                <span>重置時間:</span>
                {{ new Date(limitation.rate.reset * 1000).toLocaleString() }}
              </li>
            </ul>
          </div>
        </el-dialog>

      </el-container>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessageBox } from 'element-plus';
import 'element-plus/dist/index.css';
import { ElIcon } from 'element-plus';
import { RefreshRight, Expand, Fold } from '@element-plus/icons-vue';
import exportCSV from '@/components/exportCSV.vue';
import { org1, org2, org3, org4, org5 } from '@/staticData/orgs.js';

export default {
  components: {
    exportCSV,
    ElIcon,
    RefreshRight,
    Expand,
    Fold
  },
  data() {
    return {
      showApiLimit: false,
      limitation: {},
      isCollapsed: false,
      asideWidth: '300px',
      orgsList: [],
      orgPick: '',
      ALL_REPOSITORIES: {},
      readyToDownload: false,
      REPOSITORIES: [],
      USERS: [],
      orgReposStatus: 0,
      updateDate: '',
      orgsType: 'repo',
      orgsTypeOptions: [
        {
          value: 'repo',
          label: '倉庫',
        },
        {
          value: 'user',
          label: '人員',
        },
      ],
      loading: {
        orgsList: false,
        table: false,
        userPermission: false,
        repoPermission: false
      },
      userPermission: {
        repos: [],
        login: '',
        name: '',
        popup: false
      },
      repoPermission: {
        collaborators: [],
        repo: '',
        name: '',
        popup: false
      },
    }
  },
  computed: {
    src() {
      return '## Project Metadata - **專案**: 金好運 - **分倉類別**: 後端服務'
    },
    noDataDisplayText() {
      if (this.orgReposStatus === 401) {
        return 'Permission Denied'
      } else if (this.orgReposStatus === 2) {
        return 'No Owner PAT'
      } else {
        return this.loading.table ? '資料載入中...' : '暫無資料'
      }
    }
  },
  watch: {
    orgsType() {
      if (this.orgPick) {
        if (this.orgsType === 'repo' && this.REPOSITORIES.length === 0) {
          this.getOrgRepos(this.orgPick)
        }
      } else {
        this.showMessageBox('請先選擇組織', 'Warning', 'warning')
      }
    },
    isCollapsed(newVal) {
      this.asideWidth = newVal ? '64px' : '300px'; // 根據收合狀態調整寬度
    }
  },
  mounted() {
    this.getOrgs()
  },
  methods: {
    // 取得API限制
    async getLimit() {
      try {
        const resp = await axios.get(`${import.meta.env.VITE_Backend_API}/rate_limit?orgName=${this.orgPick}`)
        this.limitation = resp.data
        this.showApiLimit = true
        console.log('getLimit:', resp)
      } catch (e) {
        console.log('Resp error:', e)
        this.showMessageBox(e.response.data, 'Error message', 'error')
      }
    },
    // 取得組織
    async getOrgs() {
      this.loading.orgsList = true
      let resp = null
      try {
        resp = await axios.get(`${import.meta.env.VITE_Backend_API}/user/orgs`)
        if (resp.data) {
          this.orgsList = resp.data
        }
        console.log('getOrgs:', resp)
      } catch (e) {
        this.showMessageBox(e.response.data, 'Error message', 'error')
      }
      this.loading.orgsList = false
    },
    // --------------- 取得組織的倉庫 --------------- //
    async getOrgRepos(orgPick) {
      this.loading.table = true;

      try {
        const resp = await axios.get(`${import.meta.env.VITE_Backend_API}/orgs/${orgPick}/repos`);
        this.getOrgRepos_apiResponse(resp);
      } catch (error) {
        this.getOrgRepos_apiError(error);
      } finally {
        this.loading.table = false;
      }
    },
    getOrgRepos_apiResponse(resp) {
      if (resp.data.status === 2) {
        this.REPOSITORIES = [];
        this.USERS = [];
        this.orgReposStatus = 2;
        this.showMessageBox(resp.data.error, 'Warning', 'warning');
      } else {
        this.isCollapsed = true; // 關閉側邊欄
        this.orgReposStatus = 0;
        this.REPOSITORIES = resp.data.map(el => ({
          repo: el.name,
          collaborators: el.collaborators,
          description: el.description,
          projectName: el.customProperties.find(cp => cp.property_name === 'project')?.value,
          projectCategory: el.customProperties.find(cp => cp.property_name === 'category')?.value
        }));

        this.USERS = this.aggregateUserData(this.REPOSITORIES);

        this.updateDate = new Date().toLocaleString();
      }
      console.log('getOrgRepos:', resp);
    },
    aggregateUserData(repositories) {
      const userData = {};
      repositories.forEach(repo => {
        repo.collaborators.forEach(collaborator => {
          if (!userData[collaborator.login]) {
            userData[collaborator.login] = {
              avatar_url: collaborator.avatar_url,
              name: collaborator.name,
              details: []
            };
          }
          userData[collaborator.login].details.push({
            repo: repo.repo,
            role_name: collaborator.role_name
          });
        });
      });
      return Object.keys(userData).map(login => ({
        login,
        ...userData[login]
      }));
    },
    getOrgRepos_apiError(error) {
      console.error('API Error:', error);
      if (error.response && error.response.data.status === 401) {
        this.orgReposStatus = 401;
        this.showMessageBox('Permission Denied', 'Warning', 'warning');
      } else {
        this.showMessageBox((error.response && error.response.data) || 'Unknown Error', 'Error', 'error');
      }
    },

    async getUserOrgs(user) {
      this.loading.userPermission = true
      this.userPermission.popup = true

      try {
        const transformedData = this.REPOSITORIES.map(project => ({
          collaborator: project.collaborators.find(c => c.login === user.login),
          project
        })).filter(item => item.collaborator) // 只保留找到合作者的項目
          .map(item => ({
            repository: item.project.repo,
            permission: item.collaborator.role_name
          }));

        // Update the userPermission object with the transformed data and user details
        this.userPermission.repos = transformedData;
        this.userPermission.login = user.login;
        this.userPermission.name = user.name || ''
        this.userPermission.avatar_url = user.avatar_url;

        console.log('getUserOrgs:', transformedData);
      } catch (e) {
        this.userPermission.repos = [];
        this.showMessageBox('An error occurred while processing data.', 'Error message', 'error');
      }

      this.loading.userPermission = false;
    },
    async getRepoUser(owner) {
      this.loading.repoPermission = true
      this.repoPermission.popup = true
      try {
        const transformedData = this.REPOSITORIES.find(project => project.repo === owner.repo);
        this.repoPermission.collaborators = transformedData.collaborators;
        this.repoPermission.repo = owner.repo
      } catch (error) {
        this.showMessageBox(error, 'Error message', 'error')  
      }
      this.loading.repoPermission = false;
    },

    async getEveryOrgsRepo() {
      this.loading.table = true
      this.ALL_REPOSITORIES = {}
      
      try {
        const resp = await axios.get(`${import.meta.env.VITE_Backend_API}/orgs/everyrepos`)
        this.ALL_REPOSITORIES = resp.data
        this.readyToDownload = true
        console.log('getEveryOrgsRepo:', resp)     
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message || "Error fetching"
        this.showMessageBox(`${errorMsg}, 請稍後重試`, 'Error message', 'error')
      } finally {
        this.loading.table = false
      }
    },

    onClickOrgs(item) {
      this.isCollapsed = false

      this.orgsType = 'repo'

      this.orgPick = item.login
      this.getOrgRepos(item.login)
    },
    showMessageBox(message, title, type) {
      ElMessageBox.alert(message, title, {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        closeOnClickModal: true,
        type: type
      })
      .then(() => console.log("Confirmed"))
      .catch((err) => console.log("Error: ", err));
    },
    roleInfo(role) {
      const roles = {
        'admin': { abbreviation: 'A', colorClass: 'admin-color' },
        'maintain': { abbreviation: 'M', colorClass: 'maintain-color' },
        'write': { abbreviation: 'W', colorClass: 'write-color' },
        'triage': { abbreviation: 'T', colorClass: 'triage-color' },
        'read': { abbreviation: 'R', colorClass: 'read-color' },
      };

      return roles[role] || { abbreviation: '', colorClass: '' };
    },
    findNameByLogin(login) {
      const user = this.USERS.find(user => user.login === login) || []
      return this.formatUndefinedName(user.name, user.login)
    },
    formatUndefinedName(name, id) {
      return name ? name : `Undefined name (${id})`;
    },
    formatMenuItem(item) {
      return item.replace('IGS-ARCADE-DIVISION-', 'ACD_');
    },
    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style lang="scss" scoped>
.main {
  height: 100vh;
  .header {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 5vh;
    background-color: #007e87;
    box-shadow: #000 -1px 0px 4px 0px;
    z-index: 10;
    .title {
      font-size: 20px;
      font-weight: bold;
      color: #fff;
    }
  }
  .container {
    height: 95vh;
  }
}

img.avatar {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}

.role-lists {
  display: flex;
  > div {
    margin: 10px 10px 0 0;
  }
  // flex-direction: column;
}

.el-table__body-wrapper .first-column-text {
  font-size: 18px;
}

.el-table__body-wrapper .second-column-text {
  &:hover {
    color: #002b87;
    text-decoration: underline;
    cursor: pointer;
  }
}

.admin-color {
  color: #ff0000;
}

.maintain-color {
  color: #ffa500;
}

.write-color {
  color: #008000;
}

.triage-color {
  color: #0d0080;
}

.read-color {
  color: #5c0080;
}

</style>
