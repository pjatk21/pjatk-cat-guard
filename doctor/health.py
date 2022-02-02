import json
import logging
from datetime import datetime
from pathlib import Path


class DockerDoctor:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.__fn = f'health-{service_name}.json'

        if Path(self.__fn).exists():
            with open(self.__fn, 'r') as f:
                try:
                    self.__content: dict = json.load(f)
                except json.JSONDecodeError:
                    logging.warning('Failed to load health file %s, recreating!', self.__fn)
                    self.__content = {}
        else:
            self.__content = {}

    def __update_file(self):
        with open(self.__fn, 'w') as f:
            json.dump(self.__content, f)

    def update_module(self, module_name: str):
        self.__content.update({module_name: [datetime.now().astimezone().isoformat(), True]})
        self.__update_file()

    def fail_module(self, module_name: str):
        self.__content.update({module_name: [datetime.now().astimezone().isoformat(), False]})
        self.__update_file()
