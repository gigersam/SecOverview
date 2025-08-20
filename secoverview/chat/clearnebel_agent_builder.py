import os
import requests
import json
import re
import markdown
from datetime import datetime, timedelta
from dotenv import load_dotenv
from django.utils.safestring import mark_safe
from django.utils.html import format_html

load_dotenv()

class ClearNebel:
    secoverview_endpoint = os.getenv("CLEARNEBEL_AGENT_BUILDER_URL", "https://localhost")
    username = os.getenv("CLEARNEBEL_AGENT_BUILDER_USERNAME", "username")
    password = os.getenv("CLEARNEBEL_AGENT_BUILDER_PASSWORD", "password")
    update_cycle = int(os.getenv("CLEARNEBEL_AGENT_BUILDER_PASSWORD_UPDATE_CYCLE", 20))
    access_token = None
    refresh_token = None
    last_token_update = None
    
    @property
    def headers(self):
        if self.access_token != None:
            return {"Authorization": f"Bearer {self.access_token}"}
        else:
            print("Warning: Access token is not set. Returning empty headers.")
            return None

    @staticmethod
    def _execute_before_task(pre_execution_method_name_str):
        """
        A decorator factory. Returns a decorator that will execute
        a specified instance method before the decorated method.
        """
        def decorator(target_method_func):
            """The actual decorator."""
            def wrapper(instance_self, *args, **kwargs):
                # 'instance_self' is the instance of MyTaskExecutor
                # Get the pre-execution method from the instance
                pre_exec_method = getattr(instance_self, pre_execution_method_name_str)

                print(f"--- Decorator in class: Calling '{pre_execution_method_name_str}' before '{target_method_func.__name__}' ---")
                pre_exec_method()  # Call the pre-execution method on the instance

                # Call the original target method
                result = target_method_func(instance_self, *args, **kwargs)
                return result
            return wrapper
        return decorator

    def _get_token(self):
        CREDENTIALS = {
            "username": self.username,
            "password": self.password
        }
        response = self._post_request(urlendpoint="/api/v1/token/", json=CREDENTIALS, headers=False)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get("access")
            self.refresh_token = tokens.get("refresh")
            self.last_token_update = datetime.now()
        else:
            print("Failed to get Secoverview token")
    
    def _refresh_access_token(self):
        REFRESH_DATA = {
            'refresh': self.refresh_token,
        }
        response = self._post_request(urlendpoint="/api/v1/token/refresh/", data=REFRESH_DATA, headers=False)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get("access")
            self.last_token_update = datetime.now()
        else:
            print("Failed to Secoverview refresh access token.")

    def _token_validation(self):
        if datetime.now() - self.last_token_update > timedelta(hours=self.update_cycle) or self.access_token is None and self.refresh_token is not None:
            self._refresh_access_token()
            return True
        elif self.last_token_update == None or self.access_token == None or self.refresh_token == None:
            self._get_token()
            return True
        else:
            return True

    def _post_request(self, urlendpoint: str = "/", data=None, json=None, headers=True, timeout=300, verify=False):
        headers_set = self.headers if headers == True else None
        url = self.secoverview_endpoint + urlendpoint
        return requests.post(url=url, data=data, json=json, headers=headers_set, timeout=3600, verify=verify)
    
    def _get_request(self, urlendpoint: str = "/", data=None, json=None, headers=True, timeout=300, verify=False):
        headers_set = self.headers if headers == True else None
        url = self.secoverview_endpoint + urlendpoint
        return requests.get(url=url, data=data, json=json, headers=headers_set, timeout=timeout, verify=verify)

    def get_response_as_html(self, query):
        data = {"query": f"{query}", "conversation_id": "" }
        request = self._post_request(urlendpoint="/api/v1/chat/", data=data, timeout=600)
        response_json =  json.loads(request.content.decode('utf-8'))
        html = markdown.markdown(response_json.get("response"))

        def wrap_thought(match):
            inner_html = match.group(1)
            return format_html(
                '<details class="thought-collapse"><summary>Show Thought</summary>{}</details>',
                mark_safe(inner_html)
            )

        processed = re.sub(r'<think>([\s\S]*?)</think>', wrap_thought, html)
        return mark_safe(processed)
    
    def __init__(self):
        self._get_token()


try:
    clearnebel = ClearNebel()
except Exception as e:
    clearnebel = None
