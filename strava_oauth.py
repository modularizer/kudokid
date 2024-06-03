import logging
import time
import datetime
from abc import abstractmethod, ABC
from pathlib import Path
import threading
import webbrowser

import requests
from socketwrench import serve, Response
import yaml

class Scopes:
    """Enumerates the Strava API scopes which we have used/included in this project.
    For ease of use, we just request all scopes, but if you don't need all of them, you can request only the ones you need.
    """
    read = "read"
    read_all = "read_all"
    profile_read_all = "profile:read_all"
    profile_write = "profile:write"
    activity_read = "activity:read"
    activity_read_all = "activity:read_all"
    activity_write = "activity:write"

    all_read_scopes = (read, read_all, profile_read_all, activity_read, activity_read_all)
    all = (read, read_all, profile_read_all, profile_write, activity_read, activity_read_all, activity_write)


class OauthWebServer:
    def __init__(self, cleanup_event):
        self.code = None
        self.state = None
        self.scope = None
        self.cleanup_event = cleanup_event

    def exchange_token(self, state: str = "", code: str = "", scope: str = ""):
        self.state = state
        self.code = code
        self.scope = scope
        self.cleanup_event.set()
        return Response("you're authorized! you can close this tab now.")


class StravaOauth(ABC):
    """Handles OAuth2.0 for Strava API by running a thread that refreshes the token when needed.

    On the first run, or whenever the process has been dead long enough for the token to expire,
    it will open a browser window for you to authorize the app.
    """
    def __init__(self, secrets_yaml: Path = Path("secrets.yaml")):
        self.secrets_yaml = secrets_yaml
        if not self.secrets_yaml.exists():
            self.init_secret()
        with self.secrets_yaml.open("r") as f:
            self.secrets = yaml.safe_load(f)
        self.client_id = self.secrets["client_id"]
        self.client_secret = self.secrets["client_secret"]
        self.expires_at = self.secrets.get("expires_at", time.time())

        self.cleanup_oauth_loop = threading.Event()
        self.oauth_if_needed(Scopes.all)

        self.oauth_thread = threading.Thread(target=self.oauth_loop, args=(Scopes.all, 60))
        self.oauth_thread.start()

    def init_secret(self):
        input("You will need to create a Strava API application. Press Enter to continue to the Strava API website, the once complete, return here and follow instructions")
        webbrowser.open("https://www.strava.com/settings/api")
        client_id = input("Enter your client ID: ")
        client_secret = input("Enter your client secret: ")
        with open("secrets.yaml", "w") as f:
            yaml.dump({
                "client_id": client_id,
                "client_secret": client_secret
            }, f)

    @property
    def expires_in(self):
        return self.expires_at - time.time()

    @property
    def access_token(self):
        return self.secrets["access_token"]

    @property
    def refresh_token(self):
        return self.secrets["refresh_token"]

    @property
    def scope(self):
        return self.secrets.get("scope", "")

    def update_secrets(self, data):
        self.secrets.update(data)
        with self.secrets_yaml.open("w") as f:
            yaml.dump(self.secrets, f)
        self.expires_at = self.secrets.get("expires_at", time.time())
        self.set_access_token(self.access_token)
    @abstractmethod
    def set_access_token(self, access_token):
        pass

    def oauth_if_needed(self, scopes: tuple[str] = Scopes.all):
        if self.expires_in < 0:
            self.oauth(scopes)
        else:
            self.refresh()

    def oauth_loop(self, scopes: tuple[str] = Scopes.all, interval=60):
        while not self.cleanup_oauth_loop.is_set():
            self.oauth(scopes)
            print(f"Token expires in {self.expires_in} seconds")
            expires_in = self.expires_in
            sleep_time = max(min(expires_in, interval), 0)
            time.sleep(sleep_time)

    def oauth(self, scopes: tuple[str] = Scopes.all, force=False):
        if (set(self.scope.split(",")) == set(scopes)) and (not force) and (self.expires_in > 1):
            self.refresh()
            return

        scope = ",".join(scopes)
        link = f"http://www.strava.com/oauth/authorize?client_id={self.client_id}&response_type=code&redirect_uri=http://localhost:8000/exchange_token&approval_prompt=force&scope={scope}"
        ce = threading.Event()
        ows = OauthWebServer(ce)
        webbrowser.open(link)
        serve(ows, port=8000, cleanup_event=ce)

        r = requests.post("https://www.strava.com/oauth/token", {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": ows.code,
            "grant_type": "authorization_code"
        }).json()

        self.update_secrets({
            "access_token": r["access_token"],
            "refresh_token": r["refresh_token"],
            "expires_at": r["expires_at"],
            "scope": ows.scope
        })

    def refresh(self):
        r = requests.post("https://www.strava.com/oauth/token", {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }).json()
        self.update_secrets({
            "access_token": r["access_token"],
            "refresh_token": r["refresh_token"],
            "expires_at": r["expires_at"]
        })


