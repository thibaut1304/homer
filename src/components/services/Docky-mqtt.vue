<template>
  <Generic :item="item">
    <template #content>
      <!-- Title -->
      <p class="title is-4">{{ item.name }}</p>

      <!-- Body -->
      <p class="subtitle is-6">
        <!-- <div v-if="loading">
          <strong>Loading…</strong>
        </div>
        <div v-else-if="error">
          <strong class="danger">Erreur</strong>
        </div> -->
        <template v-if="item.subtitle">
          {{ item.subtitle }}
        </template>
        <!-- MQTT broker metrics -->
        <template v-else-if="mode === 'mqtt' && data">
          <span class="margined">Version : {{ data.version }}</span>
          <span v-if="!this.showVersionMobile" class="margined">Uptime : {{ data.uptime }}</span>
          <span class="margined">Clients : {{ data.active_clients }}</span>
        </template>

        <!-- Zigbee2MQTT metrics -->
        <template v-else-if="mode === 'z2m' && data">
          <span class="margined">Version : {{ data.version }}</span>
          <span class="margined">Devices : {{ data.device_count }}</span>
        </template>
      </p>
    </template>

    <!-- top‑right indicator -->
    <template #indicator>
      <i v-if="loading" class="fa fa-circle-notch fa-spin fa-2xl"></i>
      <i v-if="error" class="fa fa-exclamation-circle fa-2xl danger"></i>
      <div v-else class="status" :class="status">
        {{ status }}
      </div>
    </template>
  </Generic>
</template>

<script>
import Generic from "./Generic.vue";
import service from "@/mixins/service.js";

export default {
  name: "Docky-mqtt",
  components: { Generic },
  mixins: [service],
  props: { item: Object },
  data: () => ({
    fetchOk: null,
    data: null,
    loading: true,
    error: false,
  }),
  computed: {
    showVersionMobile: function () {
      return this.isSmallScreenMethod();
    },
    mode() {
      return (this.item.info || "mqtt").toLowerCase();
    },
    status: function () {
      if (this.fetchOk === null) return null;
      return this.fetchOk ? "online" : "offline";
    },
    fontClass() {
      return {
        "is-size-7-mobile": this.item.small_font_on_small_screens,
        "is-small": this.item.small_font_on_desktop,
      };
    },
  },
  created() {
    this.fetchData();
  },
  methods: {
    isSmallScreenMethod: function () {
      return window.matchMedia("screen and (max-width: 1023px)").matches;
    },
    async fetchData() {
      let url;
      if (this.mode === "mqtt") {
        url = `/api/docky/v0/infos/mosquitto/${this.item.broker_id}`;
      } else if (this.mode === "z2m") {
        url = `/api/docky/v0/infos/z2m/${this.item.broker_id}`;
      }
      try {
        this.data = await this.fetch(url, {
          headers: { Authorization: `Bearer ${this.item.api_token}` },
        });
        this.fetchOk = true;
      } catch (e) {
        this.error = true;
        this.fetchOk = false;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.danger { color: red; }
.margined:not(:first-child) { margin-left: 0.5rem; }
.status {
  font-size: 0.8rem;
  color: var(--text-title);
  white-space: nowrap;
  margin-left: 0.25rem;

  &.online:before {
    background-color: #94e185;
    border-color: #78d965;
    box-shadow: 0 0 5px 1px #94e185;
  }

  &.offline:before {
    background-color: #c9404d;
    border-color: #c42c3b;
    box-shadow: 0 0 5px 1px #c9404d;
  }

  &:before {
    content: " ";
    display: inline-block;
    width: 7px;
    height: 7px;
    margin-right: 10px;
    border: 1px solid #000;
    border-radius: 7px;
  }
}
</style>

