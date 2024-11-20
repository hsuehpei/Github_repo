<template>
  <el-row class="jc-e">
    <el-button v-if="csvtype === 'all'" @click="popup.exportConfirm = true" :loading="loading.table">匯出所有組織CSV</el-button>
    <el-button v-else @click="downloadCSV()">匯出CSV</el-button>

    <el-dialog
      v-model="popup.exportConfirm"
      title="匯出所有組織CSV !"
      width="50%">
      <div>
        <p v-if="!loading.table">請注意！匯出所有資料可能會大量消耗 API 呼叫次數，當達到一定次數後可能會限制使用，建議<span class="red">1小時</span>匯出一次。</p>
        <p v-else>請耐心等候....</p>
        <el-button @click="$emit('getEveryOrgsRepo'), popup.exportConfirm = false" :loading="loading.table">匯出</el-button>
      </div>
    </el-dialog>  

  </el-row>
</template>

<script>
export default {
  name: 'ExportCSV',
  props: ['ALL_REPOSITORIES', 'REPOSITORIES', 'readyToDownload', 'orgPick', 'loading', 'csvtype'],
  data() {
    return {
      popup: {
        exportConfirm: false
      }
    }
  },
  watch: {
    readyToDownload(newValue) {
      if (newValue) {
        this.downloadAllCSV()
      }
    }
  },
  methods: {
    convertToCSV(data, includeOrg = false) {
      const csvRows = [
        includeOrg ? "組織,專案,分倉類別,分倉項目,分倉說明,存取人員,權限" : "專案,分倉類別,分倉項目,分倉說明,存取人員,權限"
      ];
    
      data.forEach(item => {
        if (item.collaborators.length > 0) {
          item.collaborators.forEach(collab => {
            csvRows.push(this.formatCSVRow(item, collab.name || collab.login, collab.role_name, includeOrg));
          });
        } else {
          // 處理沒有存取人員的情況
          csvRows.push(this.formatCSVRow(item, "", "", includeOrg));
        }
      });

      return csvRows.join('\n');
    },
    formatCSVRow(item, collaborator, role, includeOrg = false) {
      const projectName = item.projectName ? item.projectName.replace(/"/g, '""') : "";
      const projectCategory = item.projectCategory ? item.projectCategory.replace(/"/g, '""') : "";
      const description = item.description ? item.description.replace(/"/g, '""') : "";
      const repoName = item.repo ? item.repo.replace(/"/g, '""') : ""; // 确保使用正确的字段名
      const org = item.org ? item.org.replace(/"/g, '""') : ""; // 添加组织字段
      const fields = includeOrg
        ? [
          `"${org}"`,
          `"${projectName}"`,
          `"${projectCategory}"`,
          `"${repoName}"`,
          `"${description}"`,
          `"${collaborator}"`,
          `"${role}"`
        ]
        : [
          `"${projectName}"`,
          `"${projectCategory}"`,
          `"${repoName}"`,
          `"${description}"`,
          `"${collaborator}"`,
          `"${role}"`
        ];
      return fields.join(',');
    },
    downloadCSV() {
      const data = this.REPOSITORIES;
      if (data.length === 0) {
        ElMessageBox.alert('暫無下載資料', '', { 
          type: 'warning', 
          confirmButtonText: '確認', 
          title: '警告',
          showClose: true,
          closeOnClickModal: true,
          closeOnPressEscape: false,
          modal: true,
          lockScroll: true,
          showCancelButton: false
        });
        return; // No data to export
      }

      const csvString = this.convertToCSV(data);

      const BOM = '\uFEFF'; // Add BOM to support UTF-8
      const blob = new Blob([BOM + csvString], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", `${this.orgPick}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    downloadAllCSV() {
      let allData = [];
      
      Object.keys(this.ALL_REPOSITORIES.repos).forEach(org => {
        const orgData = this.ALL_REPOSITORIES.repos[org].map(item => ({
          ...item,
          org
        }));
        allData = allData.concat(orgData);
      });

      if (this.ALL_REPOSITORIES.message) {
        ElMessageBox.alert(this.ALL_REPOSITORIES.message, '', { 
          type: 'warning', 
          confirmButtonText: '確認', 
          title: '警告',
          showClose: true,
          closeOnClickModal: true,
          closeOnPressEscape: false,
          modal: true,
          lockScroll: true,
          showCancelButton: false
        });
      }

      const csvString = this.convertToCSV(allData, true);

      const BOM = '\uFEFF'; // Add BOM to support UTF-8
      const blob = new Blob([BOM + csvString], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", `all_repositories.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);


      this.$emit('resetDownloadStatus');
      // this.popup.exportConfirm = false;
    }
  }
}

</script>