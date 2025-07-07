import re
from fastapi import FastAPI, Request, HTTPException, Query, Response
import httpx
from fastapi.middleware.cors import CORSMiddleware
import base64
from watcher import start_watcher, get_secrets
from logger import logger_api
from dotenv import load_dotenv
load_dotenv()

import os
from distutils.util import strtobool

TIMEOUT = bool(strtobool(os.getenv("TIMEOUT", "false")))

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:8080",
		"http://127.0.0.1:8080",
		"*"
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# class StrictOriginMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         origin = request.headers.get("origin") or request.headers.get("referer")
#         if origin and not any(origin.startswith(trusted) for trusted in TRUSTED_ORIGINS):
#             raise HTTPException(status_code=403, detail="Forbidden origin")
#         return await call_next(request)

# app.add_middleware(StrictOriginMiddleware)

start_watcher()

def resolve_secret_value(value: str, service_secrets: dict, header_key: str = "") -> str:
	"""
	Replace secret://... by its value if it exists.
	Also supports Basic base64(secret://...) in Authorization header.
	"""
	# Cas 1 — remplace directement si secret://
	if isinstance(value, str) and "secret://" in value:
		def replacer(match):
			secret_key = match.group(1).lower()
			secret_value = service_secrets.get(secret_key)
			if not secret_value:
				logger_api.error(f"Secret '{secret_key}' not found for key '{header_key}'")
				raise HTTPException(status_code=422, detail=f"Secret '{secret_key}' not found")
			return secret_value

		value = re.sub(r"secret://([a-zA-Z0-9_\-]+)", replacer, value)

	# Cas 2 — Authorization: Basic base64(secret://...)
	if header_key.lower() == "authorization" and value.startswith("Basic "):
		encoded = value[len("Basic "):].strip()
		try:
			decoded = base64.b64decode(encoded).decode()
		except Exception:
			return value

		if decoded.startswith("secret://"):
			secret_key = decoded[len("secret://"):].lower()
			secret_value = service_secrets.get(secret_key)
			if not secret_value:
				logger_api.error(f"Secret '{secret_key}' not found in Authorization: Basic")
				raise HTTPException(status_code=422, detail=f"Secret '{secret_key}' not found")
			re_encoded = base64.b64encode(secret_value.encode()).decode()
			return f"Basic {re_encoded}"

	return value

@app.api_route("/api-proxy/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_query(service: str = Query(...), url: str = Query(...), request: Request = None):
	secrets_config = get_secrets()
	logger_api.info(f":link: Proxy request for service={service}, url={url}")
	logger_api.debug(f":incoming_envelope: Method: {request.method}")
	logger_api.debug(f":receipt: Incoming headers: {dict(request.headers)}")

	# Look up secrets for the requested service
	if service not in secrets_config:
		logger_api.warning(f"Service '{service}' not found in secrets config")
		raise HTTPException(status_code=404, detail=f"Service '{service}' not found in secrets config")
	service_secrets = secrets_config.get(service)
	if not isinstance(service_secrets, dict) or not service_secrets:
		logger_api.warning(f"No secret values defined for service '{service}'")
		raise HTTPException(status_code=400, detail=f"No secret values defined for service '{service}'")

	# Filter out unwanted headers
	excluded_headers = {"host", "connection", "origin", "referer", "sec-fetch-mode", "sec-fetch-site", "sec-fetch-dest", "sec-fetch-user", "upgrade-insecure-requests", "pragma", "cache-control"}
	service_secrets_lower = {k.lower(): v for k, v in service_secrets.items()}
	headers = {}

	for key, value in request.headers.items():
		if key.lower() in excluded_headers:
			continue
		headers[key] = resolve_secret_value(value, service_secrets_lower, header_key=key)
		# logger_api.debug(f":x: :x: {key} - {value}")

	logger_api.debug(f":test_tube: Final headers sent to backend: {headers}")

	body = await request.body()

	if TIMEOUT:
		timeout = httpx.Timeout(
				connect=5.0,
				read=15.0,
				write=5.0,
				pool=None,
				)
	else:
		timeout = httpx.Timeout(5.0)

	# Proxy HTTP brut
	try:
		async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
			logger_api.debug(":incoming_envelope: Sending request to backend")
			logger_api.debug(f"  :link: URL: {url}")
			logger_api.debug(f"  :incoming_envelope: Method: {request.method}")
			logger_api.debug(f"  :receipt: Headers sent: {headers}")
			logger_api.debug(f"  	:package: Body: {body[:500]!r}")

			response = await client.request(
				method=request.method,
				url=url,
				headers=headers,
				content=body if body else None
			)

		excluded_response_headers = {"content-length", "transfer-encoding", "content-encoding", "connection"}

		response_headers = {
			k: v for k, v in response.headers.items()
			if k.lower() not in excluded_response_headers
		}
		response_headers["Access-Control-Allow-Origin"] = "*"

		return Response(
			content=response.content,
			status_code=response.status_code,
			headers=response_headers,
			media_type=response.headers.get("content-type")
		)

	except Exception as e:
		import traceback
		logger_api.error(":x: Exception caught during backend request")
		logger_api.error(traceback.format_exc())
		raise HTTPException(status_code=500, detail=f"Erreur d’appel distant: {str(e)}")

# @app.get("/secrets")
# def show_secrets():
#     return get_secrets()
