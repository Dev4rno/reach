import typing as t
import os
from dotenv import load_dotenv
from core.utils.str import parse_env_var_to_list

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path)

class EnvHandler:    
    def __init__(self):
        """Add new variables below"""
        self.state = {
            "node_env": self.get("NODE_ENV", "development"),
            "base_url": self.get("BASE_URL"),
            "sender": self.get("SENDER_EMAIL"),
            "client_local": self.get("CLIENT_URL_LOCAL"),
            "client_prod": self.get("CLIENT_URL_PROD"),
            "analytics_key": self.get("API_ANALYTICS_KEY"),
        }
        self.mongo = {
            "uri": self.get("MONGO_URI"),
            "db": self.get("DATABASE_NAME"),
        }
        self.mailjet = {
            "api_key": self.get("MAILJET_API_KEY"),
            "secret_key": self.get("MAILJET_SECRET_KEY"),
        }
        self.jwt = {
            "algorithm": self.get("ALGORITHM"),
            "secret": self.get("JWT_SECRET_KEY"),
        }
        self.auth = {
            "allow_headers": parse_env_var_to_list(self.get("ALLOW_HEADERS")),
            "allow_origins": parse_env_var_to_list(self.get("ALLOW_ORIGINS")),
        }

    def get(self, key: str, default: t.Union[t.Any, None] = None, cast: t.Union[type, None] = None) -> any:
        """
        Fetch an environment variable with optional casting and default fallback.
        - (key) Name of the environment variable.
        - (default) Default value if the variable is not found.
        - `cast`: Type to cast the value into (e.g., int, float, bool).
        - `returns`: The value of the environment variable.
        - `raises`: `KeyError` if the variable is not found and no default is provided.
        """
        value = os.getenv(key, default)
        if value is None:
            raise KeyError(f"Missing required environment variable: {key}")        
        if cast:
            try:
                value = cast(value)
            except ValueError as e:
                raise ValueError(f"Error casting environment variable {key} to {cast}: {e}")
        
        return value
    
env = EnvHandler()