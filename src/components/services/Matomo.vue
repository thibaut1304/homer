<template>
  <Generic :item="item">
    <template #content>
      <p class="title is-4">{{ item.name }}</p>
      <p class="subtitle is-6">
        <template v-if="item.subtitle">
          {{ item.subtitle }}
        </template>
        <template v-else>
          <span v-if="siteCount">Sites online :  {{ siteCount }}</span>
          <span v-if="visitCount"> - Total visit today :  {{ visitCount }}</span>
        </template>
      </p>
    </template>
    <template #indicator>
      <div v-if="status" class="status" :class="status">
        {{ status }}
      </div>
    </template>
  </Generic>
</template>

<script>
import service from "@/mixins/service.js";

export default {
  name: "Matomo",
  mixins: [service],
  props: {
    item: Object,
  },
  data: () => ({
    fetchOk: null,
    siteCount: null,
    visitCount: null,
  }),
  computed: {
    status: function () {
      return this.fetchOk ? "online" : "offline";
    },
    showUpdateAvailable: function () {
      return this.isSmallScreenMethod();
    },
  },
  created() {
    this.fetchStatus();
  },
  methods: {
    isSmallScreenMethod: function () {
      return window.matchMedia("screen and (max-width: 1023px)").matches;
    },
    fetchStatus: async function () {
      const headers = {
        "Content-Type": "application/x-www-form-urlencoded",
      };

      const bodySites = new URLSearchParams({
        module: "API",
        method: "SitesManager.getAllSites",
        format: "JSON",
        token_auth: this.item.api_token,
      });

      try {
        const sitesRes = await this.fetch("/index.php", {
          method: "POST",
          headers,
          body: bodySites,
        });
        this.siteCount = sitesRes.length;
        console.log(sitesRes)

        // Pour chaque site, on prépare une requête de stats
        const visitRequests = sitesRes.map((site) => {
          const body = new URLSearchParams({
            module: "API",
            method: "VisitsSummary.get",
            idSite: site.idsite,
            period: "day",
            date: "today",
            format: "JSON",
            token_auth: this.item.api_token,
          });
          return this.fetch("/index.php", {
            method: "POST",
            headers,
            body,
          });
        });

        const visitResults = await Promise.all(visitRequests);
        const totalVisits = visitResults.reduce((sum, siteData) => {
          return sum + (siteData.nb_visits || 0);
        }, 0);

        this.visitCount = totalVisits;
        this.fetchOk = true;
      } catch (e) {
        console.error(e);
        this.fetchOk = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
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
