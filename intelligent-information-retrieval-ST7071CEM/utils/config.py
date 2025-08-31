import os

from dotenv import load_dotenv


class MyEnvConfig:
    def __init__(self) -> None:
        load_dotenv()
        self.main_link = self._get_required_env("WEB_LINK")
        self.org_ids = self._get_required_env("ORG_IDS")
        self.auth_url = f"{self.main_link}/en/persons"
        self.robots_txt_url = f"{self.main_link}/robots.txt"

        self.output_dir = "outputs"
        self.pubs_file = "pubs.json"
        self.index_file = "index.json"

        self.cu_auth_url = (
            f"{self.main_link}/en/organisations/coventry-university/persons"
        )
        self.dep = "fbl-school-of-economics-finance-and-accounting"
        self.pub_link = f"{self.main_link}/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/"
        self.author_link = f"{self.main_link}/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/"

    def _get_required_env(self, var_name):
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Required environment variable '{var_name}' is not set")
        return value


config = MyEnvConfig()
