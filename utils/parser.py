import toml
from pydantic import ValidationError
from models import AppConfig

def parse_app_config(config_path: str) -> AppConfig:
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        return AppConfig(**config_data)
    except FileNotFoundError:
        raise FileNotFoundError(f"conf file:{config_path} not found")
    except ValidationError as e:
        raise ValidationError(f'conf file validate failed:{e}')
