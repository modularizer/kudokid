import logging
import time
import datetime
from pathlib import Path
import webbrowser

import yaml

from api_cache import API
from strava_oauth import StravaOauth


class StravaAPIRoutes:
    """Enumerates the Strava API routes which we have used/included in this project.
    For more routes, see https://developers.strava.com/docs/reference/
    """
    athlete = "/athlete"
    athlete_zones = "/athlete/zones"
    athlete_stats = "/athletes/{id}/stats"
    activities = "/activities"
    detailed_activity = "/activities/{id}"
    activity_streams = "/activities/{id}/streams"


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


class Streams:
    """Enumerates the Strava API streams available for activities."""
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

    basic = (time, latlng, distance, altitude, velocity_smooth, heartrate, moving, grade_smooth)
    all = (time, latlng, distance, altitude, velocity_smooth, heartrate, cadence, watts, temp, moving, grade_smooth)


class BareStravaAPI(StravaOauth, API):
    """Meant to be an easy-to-use API Playground for Strava API.

    Does not really extend functionality, analyze data, or do anything fancy, just helps you retrieve data from Strava API
    without needing to worry about authentication, rate limits, or caching, which are handled for you to make the development
    process easier.
    """
    base_url = "https://www.strava.com/api/v3"
    cache_db = "api_cache.db"
    secrets_yaml = Path("secrets.yaml")
    rate_limits = {
        100: 15 * 60,
        1000: 24 * 60 * 60
    }

    def __init__(self):
        API.__init__(self, self.base_url, self.cache_db, self.rate_limits, retry_on_rate_limit=True,
                     loglevel=logging.INFO)
        StravaOauth.__init__(self, self.secrets_yaml)
        self.athlete_info = self.get_athlete()

    def init_secret(self):
        input(
            "You will need to create a Strava API application. Press Enter to continue to the Strava API website, the once complete, return here and follow instructions")
        webbrowser.open("https://www.strava.com/settings/api")
        client_id = input("Enter your client ID: ")
        client_secret = input("Enter your client secret: ")
        with open("secrets.yaml", "w") as f:
            yaml.dump({
                "client_id": client_id,
                "client_secret": client_secret
            }, f)

    def set_access_token(self, access_token):
        # called by StravaOauth when token is refreshed
        # sets the heaeers API object uses
        self.headers = {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def parse_time_to_epoch(t: int | datetime.datetime | str, mode="before"):
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

    def get_athlete(self, max_age=None, cache=True):
        r = self.get(StravaAPIRoutes.athlete, max_age=max_age, cache=cache)
        self.athlete_info = r
        return r

    def get_athlete_zones(self, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.athlete_zones, max_age=max_age, cache=cache)

    def get_athlete_stats(self, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.athlete_stats, {"id": self.athlete_info["id"]}, max_age=max_age, cache=cache)

    def get_activities(self,
                        before: int | datetime.datetime | str | None = None,
                        after: int | datetime.datetime | str | None = None,
                        page: int = 1,
                        per_page: int = 30,
                        max_age: int | None = None,
                        cache: bool = True):
        """
        Args:
            before (int | datetime.datetime | str | None): A timestamp to use for filtering activities that have taken place before a certain time.
            after (int | datetime.datetime | str | None): A timestamp to use for filtering activities that have taken place after a certain time.
            page (int): Page number. Defaults to 1.
            per_page (int): Number of items per page. Defaults to 30. max 200
            max_age (int | None): Maximum age of the cache in seconds. Defaults to None.
            cache (bool): Whether to use the cache. Defaults to True.
        """
        if per_page > 200:
            raise ValueError("per_page must be less than or equal to 200")
        if per_page < 0:
            raise ValueError("per_page must be greater than or equal to 0")
        before = self.parse_time_to_epoch(before, mode="before")
        after = self.parse_time_to_epoch(after, mode="after")
        if after is not None and after >= time.time():
            raise ValueError("after must be in the past")
        if before is not None and before < 1230796800:
            raise ValueError("before must be None or positibe epoch time after 2009")
        if before is not None and after is not None and before <= after:
            raise ValueError("before must be greater than after if both are provided")
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        activities = self.get(StravaAPIRoutes.activities, {
            "before": before,
            "after": after,
            "page": page,
            "per_page": per_page
        },
        max_age=max_age,
        cache=cache)
        return activities

    def get_detailed_activity(self, activity_id, include_all_efforts=True, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.detailed_activity,
                        {"id": activity_id, "include_all_efforts": include_all_efforts},
                        max_age=max_age,
                        cache=cache)

    def get_activity_streams(self, activity_id, keys: list[str] = Streams.all, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.activity_streams,
                        {"id": activity_id, "keys": ",".join(keys), "key_by_type": True},
                        max_age=max_age,
                        cache=cache)


if __name__ == "__main__":
    a = BareStravaAPI()
    print(a.athlete_info)
    print(a.get_athlete_stats())
