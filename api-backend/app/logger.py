import logging
import os
from logging.handlers import RotatingFileHandler
import emoji

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "..", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_NUM = getattr(logging, LOG_LEVEL, logging.INFO)

LOG_EMOJIS: dict[str, str] = {
    "DEBUG": "🔍",
    "INFO": "🪧",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🔥"
}

class MqttLogger:
	def __init__(self):
		self.enabled = False
		self.client = None
		self.host = os.getenv("MQTT_IP_BROKER")
		self.port = os.getenv("MQTT_PORT_BROKER")
		self.user = os.getenv("MQTT_USERNAME")
		self.password = os.getenv("MQTT_PASSWORD")
		self.topic = os.getenv("MQTT_TOPIC")
		if not all([self.host, self.port, self.user, self.password, self.topic]):
			print("⚠️ MQTT disabled or misconfigured.", flush=True)
			return

		try:
			import paho.mqtt.client as mqtt
			self.client = mqtt.Client(transport="websockets")
			self.client.username_pw_set(self.user, self.password)
			self.client.connect(self.host, int(self.port))
			self.client.loop_start()
			self.enabled = True
			print("✅ MQTT connected and ready.", flush=True)
		except Exception as e:
			print(f"❌ MQTT error: {e}", flush=True)
			self.enabled = False

	def publish(self, message: str):
		if self.enabled and self.client:
			try:
				self.client.publish(self.topic, message)
			except Exception as e:
				print(f"❌ Error while sending MQTT message: {e}", flush=True)

mqtt_logger = MqttLogger()

class EmojiFormatter(logging.Formatter):
	"""Adds an emoji corresponding to the log level without error."""
	def format(self, record) -> str:
		if hasattr(record, "levelname") and record.levelname:
			if not any(emoji in record.levelname for emoji in LOG_EMOJIS.values()):
				emoji = LOG_EMOJIS.get(record.levelname, "📌")
				record.levelname = f"{emoji}  {record.levelname}"
		return super().format(record)

class EmojiLogger(logging.Logger):
	"""Logger that automatically adds emojis to messages."""
	def __init__(self, name: str, log_file: str, level=logging.INFO, mqtt_enabled: bool = True, to_console: bool = True,  to_file: bool = True) -> None:
		super().__init__(name, level)

		if self.hasHandlers():
			return

		self.setLevel(level)
		self.propagate = False
		self.mqtt_enabled = mqtt_enabled

		if to_file:
			if not os.path.exists(LOG_DIR):
				os.makedirs(LOG_DIR, mode=0o777)
			file_handler = RotatingFileHandler(os.path.join(LOG_DIR, log_file), maxBytes=1_000_000, backupCount=10)
			file_handler.setFormatter(EmojiFormatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
			file_handler.setLevel(level)
			self.addHandler(file_handler)

		if to_console:
			console_handler = logging.StreamHandler()
			console_handler.setFormatter(EmojiFormatter("%(asctime)s - %(levelname)s - %(message)s"))
			console_handler.setLevel(level)
			self.addHandler(console_handler)

	def emoji_log(self, level: int, message: str) -> None:
		"""Automatically adds an emoji to logs."""
		message = emoji.emojize(message, language="alias")
		self.log(level, message)

	def debug(self, message: str, *args, **kwargs) -> None:
		formatted = emoji.emojize(message, language="alias")
		if mqtt_logger.enabled:
			mqtt_logger.publish(f"[DEBUG] {formatted}")
		super().debug(formatted, *args, **kwargs)

	def info(self, message: str, *args, **kwargs) -> None:
		formatted = emoji.emojize(message, language="alias")
		if mqtt_logger.enabled:
			mqtt_logger.publish(f"[INFO] {formatted}")
		super().info(formatted, *args, **kwargs)

	def warning(self, message: str, *args, **kwargs) -> None:
		formatted = emoji.emojize(message, language="alias")
		if mqtt_logger.enabled:
			mqtt_logger.publish(f"[WARNING] {formatted}")
		super().warning(formatted, *args, **kwargs)

	def error(self, message: str, *args, **kwargs) -> None:
		formatted = emoji.emojize(message, language="alias")
		if mqtt_logger.enabled:
			mqtt_logger.publish(f"[ERROR] {formatted}")
		super().error(formatted, *args, **kwargs)

	def critical(self, message: str, *args, **kwargs) -> None:
		formatted = emoji.emojize(message, language="alias")
		if mqtt_logger.enabled:
			mqtt_logger.publish(f"[CRITICAL] {formatted}")
		super().critical(formatted, *args, **kwargs)


logger_api      = EmojiLogger("api_logger",     "api.log",      LOG_LEVEL_NUM, to_file=False)
# logger_error    = EmojiLogger("error_logger",   "error.log",    LOG_LEVEL_NUM)
# logger_access   = EmojiLogger("access_logger",  "access.log",   LOG_LEVEL_NUM, to_console=False)
