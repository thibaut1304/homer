<template>
  <Generic :item="item">
    <template #content>
      <p class="title is-4">{{ item.name }}</p>
      <p class="subtitle is-6">
        <template v-if="item.subtitle">
          {{ item.subtitle }}
        </template>
        <template v-else-if="data">

          <div v-if="loading">
            <strong>Loading...</strong>
          </div>
          <div v-else-if="error">
            <strong class="danger">Error loading VM info</strong>
          </div>
          <div v-else class="metrics" :class="{
            'is-size-7-mobile': item.small_font_on_small_screens,
            'is-small': item.small_font_on_desktop,
          }">
            <span class="margined">{{ type == "lxc" ? "LXC-Id" : "VM-Id"}}:
              <span v-if="data.status === 'stopped'" class="danger">Stopped</span>
              <span v-if="data.status === 'running'" class="has-text-weight-bold">{{ data.vmid }}</span>
            </span>
            <span v-if="data.cpu && isValueShown('cpu')" class="margined">CPU: 
              <span class="has-text-weight-bold" :class="statusClass(data.cpu)">
                {{ (data.cpu * 100).toFixed(1)}}%
              </span>
            </span>
            <span v-if="data.mem && isValueShown('mem')" class="margined">Mem: 
              <span class="has-text-weight-bold" :class="statusClass(memoryUsed)">
                {{ memoryUsed}}%</span>
              </span>
            <span v-if="data.blockstat && data.blockstat.scsi0 && isValueShown('disk')" class="margined">Disk: 
              <span class="has-text-weight-bold" :class="statusClass(diskUsed)">
                {{ diskUsed }}%

              </span>
            </span>
            <span v-if="data.uptime && isValueShown('uptime')" class="margined">Uptime: 
              <span class="has-text-weight-bold">
                {{ uptimeFormatted }}

              </span>
            </span>
          </div>
        </template>
      </p>
    </template>
    <template #indicator>
      <i v-if="loading" class="fa fa-circle-notch fa-spin fa-2xl"></i>
      <i v-if="error" class="fa fa-exclamation-circle fa-2xl danger"></i>
    </template>
  </Generic>
</template>

<script>
import service from "@/mixins/service.js";
import Generic from "./Generic.vue";

export default {
  name: "ProxmoxVM",
  components: {
    Generic,
  },
  mixins: [service],
  props: {
    item: Object,
  },
  data: () => ({
    data: null,
    memoryUsed: 0,
    diskUsed: 0,
    uptimeFormatted: 0,
    type: "",
    instance_id: "",
    warning_value : 50,
    danger_value: 80,
    error: false,
    loading: true,
  }),
  created() {
    if (this.item.vm_id && this.item.lxc_id) {
      console.error("You cannot use `vm_id` and `lxc_id` at the same time");
      this.error = true;
      this.loading = false;
      return;
    }
    this.instance_id = this.item.vm_id || this.item.lxc_id;
    this.type = this.item.vm_id ? "qemu" : "lxc";
    this.warning_value = this.item.warning_value || this.warning_value;
    this.danger_value = this.item.danger_value || this.danger_value;
    this.fetchStatus();
  },
  methods: {
    statusClass(value) {
      if (value > this.danger_value) return "danger";
      if (value > this.warning_value) return "warning";
      return "healthy";
    },
    formatUptime(seconds) {
      const j = Math.floor(seconds / 86400);
      const h = Math.floor((seconds % 86400) / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = seconds % 60;
      if (j >= 7) {
        return `${j} days ${h}h`;
      } else if (j >= 1) {
        return `${j} day ${h}h ${m}m`;
      } else {
        return `${h}h ${m}m ${s}s`;
      }
    },
    fetchStatus: async function () {
      try {
        const options = {
          headers: {
            Authorization: this.item.api_token,
          },
        };
        const lxc_qemu = await this.fetch(
          `/api2/json/nodes/${this.item.node}/${this.type}/${this.instance_id}/status/current`,
          options
        );
        this.data = lxc_qemu.data;
        this.memoryUsed = ((this.data.mem * 100) / this.data.maxmem).toFixed(1);
        if (this.data.blockstat && this.data.blockstat.scsi0) {
          const usedDiskSpace = this.data.blockstat.scsi0.wr_highest_offset;
          this.diskUsed = ((usedDiskSpace * 100) / this.data.maxdisk).toFixed(1);
        }
        this.uptimeFormatted = this.formatUptime(this.data.uptime);
        this.error = false;
      } catch (err) {
        console.log(err);
        this.error = true;
      }
      this.loading = false;
    },
    isValueShown(value) {
      return this.item.hide.indexOf(value) == -1;
    },
  },
};
</script>

<style scoped lang="scss">
.healthy {
  color: green;
}

.warning {
  color: orange;
}

.danger {
  color: red;
}

.metrics .margined:not(:first-child) {
  margin-left: 0.3rem;
}
.is-small {
  font-size: small;
}
</style>