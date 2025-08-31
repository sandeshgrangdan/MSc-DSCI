import os
import json

from utils.config import config


class FileHandler:
    def __init__(self) -> None:
        # Create folder if it does not exist
        os.makedirs(config.output_dir, exist_ok=True)

    def write_file(self, content, filename: str):
        with open(f"{config.output_dir}/{filename}", "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)


file_handler = FileHandler()
