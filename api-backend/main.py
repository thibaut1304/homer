from fastapi import FastAPI, Request, HTTPException, Query, Response
import httpx
import yaml
import os
from fastapi.middleware.cors import CORSMiddleware
# from urllib.parse import unquote

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Charge les secrets depuis config_secret.yml
SECRETS_PATH = os.path.join(os.path.dirname(__file__), "config_secret.yml")

if os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH, "r") as f:
        secrets_config = yaml.safe_load(f)
else:
    secrets_config = {}


@app.api_route("/api-proxy/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_query(service: str = Query(...), url: str = Query(...), request: Request = None):
	print(f"Requête proxy pour service={service}, url={url}", flush=True)
	print(f"Méthode: {request.method}", flush=True)
	print(f"Headers reçus :", dict(request.headers), flush=True)
	body = await request.body()
	print(f"Corps brut: {body[:300]!r}", flush=True)
	# if request.method == "OPTIONS":
		# return Response(status_code=204)

	# Cherche les secrets pour ce service
	service_secrets = secrets_config.get(service)
	if not service_secrets:
		raise HTTPException(status_code=404, detail="Service secrets not found")

	# Exclus les headers relou
	excluded_headers = {"host", "connection", "origin", "referer", "sec-fetch-mode", "sec-fetch-site", "sec-fetch-dest", "sec-fetch-user", "upgrade-insecure-requests", "pragma", "cache-control"}
	headers = {}
	for key, value in request.headers.items():
		if key.lower() in excluded_headers:
			continue
		if value.startswith("secret://"):
			_, secret_key = value.split("secret://")[-1].split(":")
			secret_value = service_secrets.get(secret_key)
			if not secret_value:
				raise HTTPException(status_code=403, detail=f"Secret {secret_key} not found for {service}")
			headers[key] = secret_value
		else:
			headers[key] = value
	print("🧪 Headers finaux envoyés vers le vrai service :", headers, flush=True)

	# Récupère le corps brut
	body = await request.body()
	# decoded_url = unquote(url)

	# Proxy HTTP brut
	try:
		async with httpx.AsyncClient(verify=False) as client:
			print("📤 Requête envoyée vers le backend :", flush=True)
			print(f"  🔗 URL : {url}", flush=True)
			print(f"  📤 Méthode : {request.method}", flush=True)
			print(f"  🧾 Headers envoyés :", headers, flush=True)
			print(f"  📦 Body : {body[:500]!r}", flush=True)

			response = await client.request(
				method=request.method,
				url=url,
				headers=headers,
				content=body if body else None
			)

		# Proxy "bête" de la réponse
		# SUpprime header encore relou de la res
		excluded_response_headers = {"content-length", "transfer-encoding", "content-encoding", "connection"}

		response_headers = {
			k: v for k, v in response.headers.items()
			if k.lower() not in excluded_response_headers
		}

		return Response(
			content=response.content,
			status_code=response.status_code,
			headers=response_headers,
			media_type=response.headers.get("content-type")
		)

	except Exception as e:
		import traceback
		print("❌ Exception attrapée :", flush=True)
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=f"Erreur d’appel distant: {str(e)}")
