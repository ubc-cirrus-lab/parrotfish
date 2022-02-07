import os
import re

API_KEY_DIR = ".aws/credentials"


class AWSCredentialsFetch:
    def __init__(self):
        self._fields = self._read_credentials_file()

    def get_access_key_id(self) -> str:
        return self._fields["aws_access_key_id"]

    def get_secret_access_key(self) -> str:
        return self._fields["aws_secret_access_key"]

    def _read_credentials_file(self) -> dict:
        fields = {}
        try:
            with open(os.path.join(os.path.expanduser("~"), API_KEY_DIR), "r") as file:
                for line in file.readlines():
                    match = re.search(r"(.*)\s*=\s*(.*)", line)
                    if match:
                        fields[match.group(1).strip()] = match.group(2).strip()
        except FileNotFoundError:
            print("Could not find the aws config using the '~/{API_KEY_DIR}' directory")
        return fields
