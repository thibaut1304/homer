function needsPluginBackend(obj) {
	if (typeof obj === 'string') {
		return obj.startsWith('secret://');
	}
	if (Array.isArray(obj)) {
		return obj.some(needsPluginBackend);
	}
	if (typeof obj === 'object' && obj !== null) {
		return Object.values(obj).some(needsPluginBackend);
	}
	return false;
}

export default {
	props: {
		proxy: Object,
	},
	created: function () {
		// custom service often consume info from an API using the item link (url) as a base url,
		// but sometimes the base url is different. An optional alternative URL can be provided with the "endpoint" key.
		this.endpoint = this.item.endpoint || this.item.url;

		if (this.endpoint && this.endpoint.endsWith("/")) {
			this.endpoint = this.endpoint.slice(0, -1);
		}

		this.useSecretProxy = this.item["api-backend-secret"] === true;
	},
	methods: {
		fetch: function (path, init, json = true) {
			let options = {};

			if (this.proxy?.useCredentials) {
				options.credentials = "include";
			}

			if (this.proxy?.headers && !!this.proxy.headers) {
				options.headers = this.proxy.headers;
			}

			// Each item can override the credential settings
			if (this.item.useCredentials !== undefined) {
				options.credentials =
					this.item.useCredentials === true ? "include" : "omit";
			}

			// Each item can have their own headers
			if (this.item.headers !== undefined && !!this.item.headers) {
				options.headers = this.item.headers;
			}

			options = Object.assign(options, init);

			if (path.startsWith("/")) {
				path = path.slice(1);
			}

			let url = this.endpoint;

			if (path) {
				url = `${this.endpoint}/${path}`;
			}

			// Si plugin activé -> go backend
			if (needsPluginBackend(this.item)) {
				const backendUrl = `/server/?service=${encodeURIComponent(this.item.type)}&url=${encodeURIComponent(url)}`;

				return fetch(backendUrl, options).then((response) => {
					if (!response.ok) {
						throw new Error(
							`SecretProxy: backend not available (${response.status} error)`
						);
					}
					return json ? response.json() : response.text();
				});
			}


			// Sinon comportement normal
			return fetch(url, options).then((response) => {
				let success = response.ok;
				if (Array.isArray(this.item.successCodes)) {
					success = this.item.successCodes.includes(response.status);
				}

				if (!success) {
					throw new Error(
						`Ping: target not available (${response.status} error)`,
					);
				}

				return json ? response.json() : response.text();
			});
		},
	},
};
