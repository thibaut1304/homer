<template>
	<Generic :item="item">
	  <template #content>
		<p class="title is-4">{{ this.item.container }}</p>
		<p class="subtitle is-6">
		  <template v-if="data">
			<div v-if="loading">
			  <strong>Loading...</strong>
			</div>
			<div v-else-if="error">
			  <strong class="danger">Erreur de chargement</strong>
			</div>
			<div v-else class="metrics">
			  <span class="margined danger" v-if="data.status !== 'running'">Stopped</span>

			  <span v-if="data.cpu_percent" class="margined">CPU:
				<span :class="statusClass(data.cpu_percent)">
				  {{ data.cpu_percent }}%
				</span>
			  </span>

			  <span v-if="data.memory" class="margined">Mem:
				<span :class="statusClass(data.memory.percent)">
				  {{ data.memory.percent }}%
				</span>
				/ {{ Math.ceil(data.memory.limit_mb / 1000) }} GB
			  </span>

			  <span v-if="data.uptime" class="margined is-hidden-mobile">
				Uptime: <strong>{{ data.uptime }}</strong>
			  </span>
			  <span v-if="data.restart" class="margined is-hidden-mobile">
				Restart: <strong>{{ data.restart }}</strong>
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
	name: "Docky",
	components: { Generic },
	mixins: [service],
	props: { item: Object },
	data: () => ({
	  data: null,
	  error: false,
	  loading: true,
	}),
	created() {
	  this.fetchData();
	},
	methods: {
		statusClass(value) {
			if (value > 80) return "danger";
			if (value > 50) return "warning";
			return "healthy";
		},
		async fetchData() {
		try {
			const response = await this.fetch(
			`/api/docky/v0/containers/metrics/${this.item.container}`,
			{
				headers: {
					Authorization: `Bearer ${this.item.api_token}`,
				},
			}
			);
			for (const [host, containers] of Object.entries(response)) {
				if (Array.isArray(containers) && containers.length > 0) {
					this.data = containers[0];
					this.item.host = host;
					console.log(this.data);
					console.log(this.item.host);

					break;
				}
			}

			if (!this.data) {
				console.warn("Aucune donnée de container trouvée !");
				this.error = true;
			}
			this.loading = false;
		} catch (err) {
			this.error = true;
			this.loading = false;
		}
		},
	},
  };
  </script>

  <style scoped>
  .healthy { color: green; }
  .warning { color: orange; }
  .danger  { color: red; }
  .metrics .margined:not(:first-child) { margin-left: 0.5rem; }
  </style>
