import os
import threading
import yaml
from watchdog.observers.polling import PollingObserver

from watchdog.events import FileSystemEventHandler
from logger import logger_api

CONFIG_FILE = "/app/secrets/config_secret.yml"
_secrets_cache = {}
_lock = threading.Lock()


class ConfigFileHandler(FileSystemEventHandler):
	def on_modified(self, event):
		if event.src_path.endswith(CONFIG_FILE):
			logger_api.debug("[:rocket:] Change detected in the secrets file.")
			_reload_secrets()


def _reload_secrets():
	global _secrets_cache
	try:
		with open(CONFIG_FILE, "r") as f:
			data = yaml.safe_load(f) or {}
			with _lock:
				_secrets_cache = data
			logger_api.debug("[:white_check_mark:] Secrets successfully reloaded.")
	except Exception as e:
		logger_api.debug(f"[:x:] Error while reloading {CONFIG_FILE}: {e}")


def get_secrets():
	with _lock:
		return _secrets_cache.copy()


def start_watcher():
	_reload_secrets()
	event_handler = ConfigFileHandler()
	observer = PollingObserver()
	observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE) or ".", recursive=False)
	observer.daemon = True
	observer.start()
