import time
import datetime
from pathlib import Path
import threading
import webbrowser

import requests
from socketwrench import serve, Response
import yaml


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


class Scopes:
    read = "read"
    read_all = "read_all"
    profile_read_all = "profile:read_all"
    profile_write = "profile:write"
    activity_read = "activity:read"
    activity_read_all = "activity:read_all"
    activity_write = "activity:write"

    all_read_scopes = (read, read_all, profile_read_all, activity_read, activity_read_all)
    all = (read, read_all, profile_read_all, profile_write, activity_read, activity_read_all, activity_write)


class Streams:
    time = "time"
    latlng = "latlng"
    distance = "distance"
    altitude = "altitude"
    velocity_smooth = "velocity_smooth"
    heartrate = "heartrate"
    cadence = "cadence"
    watts = "watts"
    temp = "temp"
    moving = "moving"
    grade_smooth = "grade_smooth"

    basic = [time, latlng, distance, altitude, velocity_smooth, heartrate, moving, grade_smooth]
    all = [time, latlng, distance, altitude, velocity_smooth, heartrate, cadence, watts, temp, moving, grade_smooth]

class KudoKidAPI:
    base_url = "https://www.strava.com/api/v3"

    def __init__(self):
        if not Path("secrets.yaml").exists():
            self.prompt_setup()
        with Path("secrets.yaml").open("r") as f:
            self.secrets = yaml.safe_load(f)
        self.client_id = self.secrets["client_id"]
        self.client_secret = self.secrets["client_secret"]
        self.expires_at = self.secrets.get("expires_at", time.time())

        self.cleanup_oauth_loop = threading.Event()
        self.oauth_thread = threading.Thread(target=self.oauth_loop, args=(Scopes.all, 60))
        self.oauth_thread.start()

        if not Path("athlete_info.yaml").exists():
            self.get_athlete_info(zones=True, stats=True)

    def prompt_setup(self):
        input("You will need to create a Strava API application. Press Enter to continue to the Strava API website, the once complete, return here and follow instructions")
        webbrowser.open("https://www.strava.com/settings/api")
        client_id = input("Enter your client ID: ")
        client_secret = input("Enter your client secret: ")
        with open("secrets.yaml", "w") as f:
            yaml.dump({
                "client_id": client_id,
                "client_secret": client_secret
            }, f)

    def get_athlete_info(self, zones=False, stats=False):
        self.athlete_info = self.get("/athlete")
        if zones:
            self.athlete_info["zones"] = self.get("/athlete/zones")
        if stats:
            self.athlete_info["stats"] = self.get("/athletes/{id}/stats", {"id": self.athlete_info["id"]})
        with open("athlete_info.yaml", "w") as f:
            yaml.dump(self.athlete_info, f)

    def __repr__(self):
        return f'KudoKid({self.athlete_info.get("firstname", "Unknown")}, {self.athlete_info.get("lastname", "Unknown")})'

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
        with Path("secrets.yaml").open("w") as f:
            yaml.dump(self.secrets, f)

    def get(self, route, params=None):
        headers = {"Authorization": f"Bearer {self.access_token}"}

        if params is not None:
            for key, value in params.copy().items():
                if f"{{{key}}}" in route:
                    route = route.replace(f"{{{key}}}", str(value))
                    del params[key]
        return requests.get(f"{self.base_url}{route}", headers=headers, params=params).json()

    def oauth_if_needed(self, scopes: tuple[str] = Scopes.all):
        if self.expires_in < 0:
            self.oauth(scopes)
        else:
            self.refresh()

    def oauth_loop(self, scopes: tuple[str] = Scopes.all, interval=60):
        while not self.cleanup_oauth_loop.is_set():
            self.oauth(scopes)
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
        print(f"navigating to {link}")
        webbrowser.open(link)
        serve(ows, port=8000, cleanup_event=ce)
        print("received code:", ows.code)


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

    def parse_time_to_epoch(self, t: int | datetime.datetime | str, mode="before"):
        if isinstance(t, int):
            if t > 0:
                return t
            else:
                return time.time() + t
        if isinstance(t, datetime.datetime):
            return int(t.timestamp())
        if isinstance(t, datetime.date):
            return int(time.mktime(t.timetuple()))
        if isinstance(t, str):
            # parse string to datetime
            # patterns = ["%m/%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"]
            if t.count("/") == 1:
                t = f"{t}/{datetime.date.today().year}"
            if " " not in t:
                if mode == "before":
                    t = f"{t} 23:59:59"
                else:
                    t = f"{t} 00:00:00"
            return int(datetime.datetime.strptime(t, "%m/%d/%Y %H:%M:%S").timestamp())
        return None

    def get_authenticated_athlete(self):
        return self.get("/athlete")

    def list_activities(self,
                        before: int | datetime.datetime | str | None = None,
                        after: int | datetime.datetime | str | None = None,
                        page: int = 1,
                        per_page: int = 30):
        """
        Args:
            before (int | datetime.datetime | str | None): A timestamp to use for filtering activities that have taken place before a certain time.
            after (int | datetime.datetime | str | None): A timestamp to use for filtering activities that have taken place after a certain time.
            page (int): Page number. Defaults to 1.
            per_page (int): Number of items per page. Defaults to 30.
        """
        return self.get("/athlete/activities", {
            "before": self.parse_time_to_epoch(before, mode="before"),
            "after": self.parse_time_to_epoch(after, mode="after"),
            "page": page,
            "per_page": per_page
        })

    def get_activity(self, activity_id):
        return self.get("/activities/{id}", {"id": activity_id})

    def get_activity_streams(self, activity_id, keys: list[str] = Streams.basic):
        return self.get(f"/activities/{activity_id}/streams", {"keys": ",".join(keys), "key_by_type": True})


if __name__ == "__main__":
    # import logging
    # logging.basicConfig(level=logging.DEBUG)

    ku = KudoKidAPI()
    activities = ku.list_activities()
    last_activity = ku.get_activity(activities[0]["id"])
    last_activity_streams = ku.get_activity_streams(last_activity["id"], Streams.all)