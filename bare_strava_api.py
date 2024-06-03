import json
import logging
import time
import datetime
from pathlib import Path
import webbrowser
from typing import Literal

import requests
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
    list_activities = "/athlete/activities"
    detailed_activity = "/activities/{id}"
    list_activity_comments = "/activities/{id}/comments"
    list_activity_kudos = "/activities/{id}/kudos"
    list_activity_laps = "/activities/{id}/laps"
    activity_streams = "/activities/{id}/streams"
    upload_activity = "/uploads"
    export_gpx = "/routes/{id}/export_gpx"
    export_tcx = "/routes/{id}/export_tcx"
    get_route = "/routes/{id}"


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


SportType = Literal["AlpineSki", "BackcountrySki", "Badminton", "Canoeing", "Crossfit", "EBikeRide", "Elliptical",
    "EMountainBikeRide", "Golf", "GravelRide", "Handcycle", "HighIntensityIntervalTraining", "Hike",
    "IceSkate", "InlineSkate", "Kayaking", "Kitesurf", "MountainBikeRide", "NordicSki", "Pickleball", "Pilates",
"Racquetball", "Ride", "RockClimbing", "RollerSki", "Rowing", "Run", "Sail", "Skateboard", "Snowboard", "Snowshoe",
"Soccer", "Squash", "StairStepper", "StandUpPaddling", "Surfing", "Swim", "TableTennis", "Tennis", "TrailRun",
"Velomobile", "VirtualRide", "VirtualRow", "VirtualRun", "Walk", "WeightTraining", "Wheelchair", "Windsurf", "Workout", "Yoga"]
sport_types = SportType.__args__

data_types = ["fit", "fit.gz", "tcx", "tcx.gz", "gpx", "gpx.gz"]


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

    @staticmethod
    def parse_time_to_epoch(t: str,  # int | datetime.datetime | str,
                            mode: Literal["before", "after"] = "before"):
        """Parses a time to epoch time."""
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

    def __init__(self,
                 get_athlete=True,
                 list_all_activities=True,
                 get_athlete_zones=False,
                 get_athlete_stats=False
                 ):
        """Initializes the API object and makes a few useful requests to get you started.

        Args:
            get_athlete (bool): Whether to get the athlete info. Defaults to True.
                The athlete ID is needed for most other requests, so this is recommended.
            list_all_activities (bool): Whether to list all activities. Defaults to True.
                This is necessary to get the activity IDs for other requests related to getting more detailed activity info.
                Will use multiple requests to get all activities if there are more than 200 activities.
            get_athlete_zones (bool): Whether to get the athlete zones. Defaults to False.
                This is useful if you want to get the athlete's heart rate zones, power zones, etc.
            get_athlete_stats (bool): Whether to get the athlete stats. Defaults to False.
                This is useful if you want to get the athlete's stats like total distance, total time, etc.
            """
        API.__init__(self, self.base_url, self.cache_db,
                     rate_limits=self.rate_limits,
                     retry_on_rate_limit=True,
                     loglevel=logging.INFO,

                     )
        StravaOauth.__init__(self, secrets_yaml=self.secrets_yaml)
        if get_athlete:
            self.athlete_info = self.get_athlete()
            self.athlete_id = self.athlete_info["id"]
        if list_all_activities:
            self.all_activities = self.list_all_activities()
            self.activity_ids = list(self.all_activities.keys())
        if get_athlete_zones:
            self.get_athlete_zones()
        if get_athlete_stats:
            self.get_athlete_stats()

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

    def open_docs(self):
        webbrowser.open("https://developers.strava.com/docs/reference/")

    def get_athlete(self, max_age=None, cache=True):
        """First and foremost, get the athlete info, you will need the athlete ID for most other requests."""
        r = self.get(StravaAPIRoutes.athlete, max_age=max_age, cache=cache)
        self.athlete_info = r
        self.athlete_id = r["id"]
        return r

    def list_all_activities(self, after="last_cached", max_age=None, cache=True):
        """List all activities for the authenticated athlete.

        By default it will use the cache to get the last time the list was retrieved, and only get activities after that time.
        If you want to get all activities from the beginning, set max_age=0

        Args:
            after (str | datetime.datetime | int): A timestamp to use for filtering activities that have taken place after a certain time.
                Defaults to "last_cached", which will use the last time the list was retrieved from the cache.
                If you want to get all activities from the beginning, set after=0
            max_age (int | None): Maximum age of the cache in seconds. Defaults to None.
            cache (bool): Whether to use the cache. Defaults to True.
        """
        if after == "last_cached" and max_age != 0:
            cached_responses = self.cache.retrieve_cached_get(
                self.base_url + StravaAPIRoutes.list_activities,
                limit=None,
                order_by="called_at ASC",
                response_code=200,
                max_age=max_age,
            )
            all_cached_activities = {}
            for response in cached_responses:
                for activity in response:
                    all_cached_activities[activity["id"]] = activity
            after = max([datetime.datetime.strptime(activity["start_date"], "%Y-%m-%dT%H:%M:%SZ") for activity in all_cached_activities.values()]) if all_cached_activities else None
        else:
            all_cached_activities = {}

        page = 1
        activities = True
        all_activities = []
        while activities:
            activities = self.list_athlete_activities(per_page=200, page=page, after=after, max_age=max_age, cache=cache)
            page += 1
            all_activities.extend(activities)
        all_activities.sort(key=lambda x: datetime.datetime.strptime(x["start_date"], "%Y-%m-%dT%H:%M:%SZ"), reverse=True)
        self.all_activities = {
            **all_cached_activities,
            **{activity["id"]: activity for activity in all_activities}
        }
        self.activity_ids = list(self.all_activities.keys())
        return self.all_activities

    def list_athlete_activities(self,
                                before: int | datetime.datetime | str | None = None,
                                after: int | datetime.datetime | str | None = None,
                                page: int = 1,
                                per_page: int = 30,
                                max_age: int | None = None,
                                cache: bool = True,
                                filter=None,
                                **filters):
        """List activities for the authenticated athlete.

        This is necessary to get the activity IDs for other requests.
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

        activities = self.get(StravaAPIRoutes.list_activities, {
            "before": before,
            "after": after,
            "page": page,
            "per_page": per_page
        },
        max_age=max_age,
        cache=cache)
        filtered_activities = self.filter_activities(filter, **filters)
        return filtered_activities

    def filter_activities(self, filter = None, activities=None, **filters):
        """Searches the cache for activities that match the conditions.

        Args:
            filter (function): A function that takes an activity and returns True if it should be included, False otherwise.
            activities (dict): A dictionary of activities to filter. Defaults to None, which will use all_activities.
            filters (dict): A dictionary of key-value pairs to filter the activities by. The key is the field to filter by, and the value is the condition to filter by.
                The condition can be...
                * a value,
                * a list of values, a range, a set,
                * a dictionary with keys "min", "max", or "equals",
                * a string that starts with "~" to search for a substring, or
                * a function that takes a value and returns True if it matches the condition.
        """
        if not activities:
            activities = self.all_activities
        filtered_activities = {k: v for k, v in activities.items() if not filter or filter(v)}
        for activity_id, activity in filtered_activities.items():
            for key, condition in filters.items():
                value = activity.get(key)
                if value == condition:
                    filtered_activities[activity_id] = activity
                    break
                if isinstance(condition, (tuple, list, range, set)) and value in condition:
                    filtered_activities[activity_id] = activity
                    break
                if isinstance(condition, dict):
                    if condition.get("min") and value < condition["min"]:
                        break
                    if condition.get("max") and value > condition["max"]:
                        break
                    if condition.get("equals") and value != condition["equals"]:
                        break
                    filtered_activities[activity_id] = activity
                    break
                if isinstance(condition, str) and isinstance(value, str) and condition.startswith('~') and condition[1:] in value:
                    filtered_activities[activity_id] = activity
                    break
                if callable(condition) and condition(value):
                    filtered_activities[activity_id] = activity
                    break
        return filtered_activities

    def create_activity(self, name: str, sport_type: SportType, start_date_local: str, elapsed_time: int,
                       description: str = None, distance: float = None, trainer: bool = None, commute: bool = None,
                        **kwargs):
        """
        Args:
            name (str): The name of the activity.
            sport_type (str): An instance of SportType.
            start_date_local (str): ISO 8601 formatted date time.
            elapsed_time (int): In seconds.
            description (str): The description of the activity.
            distance (float): In meters.
            trainer (bool): Whether this activity was recorded on a training machine.
            commute (bool): Whether this activity is a commute.
        """
        data = {
            "name": name,
            "type": sport_type,
            "start_date_local": start_date_local,
            "elapsed_time": elapsed_time,
            **kwargs
        }
        if description is not None:
            data["description"] = description
        if distance is not None:
            data["distance"] = distance
        if trainer is not None:
            data["trainer"] = trainer
        if commute is not None:
            data["commute"] = commute
        return requests.post(StravaAPIRoutes.list_activities, data)

    def upload_activity(self, file_path: str, name: str, description: str = None,
                        trainer: bool = None, commute: bool = None, external_id: str = None,
                        data_type: str = None):
        """
        Args:
            file_path (str): The path to the file to upload.
            name (str): The name of the activity.
            description (str): The description of the activity.
            trainer (bool): Whether the activity was recorded on a trainer.
            commute (bool): Whether the activity is a commute.
            external_id (str): The external identifier of the activity.
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data_type = file_path.split(".")[-1] if data_type is None else data_type
            if data_type not in data_types:
                raise ValueError(f"data_type must be one of {data_types}")
            data = {
                "name": name,
                "description": description,
                "trainer": trainer,
                "commute": commute,
                "external_id": external_id,
                "data_type": data_type
            }
            return requests.post(StravaAPIRoutes.upload_activity, data=data, files=files)

    def update_activity(self,
                        activity_id: int,
                        commute: bool = None,
                        trainer: bool = None,
                        hide_from_home: bool = None,
                        description: str = None,
                        name: str = None,
                        sport_type: SportType = None,
                        gear_id: str = None,
                        **kwargs
                        ):
        """

        Args:
            activity_id (int): The identifier of the activity.
            commute (bool): Whether this activity is a commute.
            trainer (bool): Whether this activity was recorded on a training machine.
            hide_from_home (bool): Whether this activity is muted.
            description (str): The description of the activity.
            name (str): The name of the activity.
            sport_type (str): An instance of SportType.
            gear_id (str): Identifier for the gear associated with the activity. ‘none’ clears gear from activity.
        """
        data = {}
        if commute is not None:
            data["commute"] = commute
        if trainer is not None:
            data["trainer"] = trainer
        if hide_from_home is not None:
            data["hide_from_home"] = hide_from_home
        if description is not None:
            data["description"] = description
        if name is not None:
            data["name"] = name
        if type is not None:
            data["type"] = type
        if sport_type is not None:
            data["sport_type"] = sport_type
        if gear_id is not None:
            data["gear_id"] = gear_id
        return requests.put(StravaAPIRoutes.detailed_activity,
                        {"id": activity_id, **data, **kwargs})

    def update_athlete(self, weight: float = None, **kwargs):
        """
        Args:
            weight (float): The weight of the athlete in kilograms.
        """
        data = kwargs
        if weight is not None:
            data["weight"] = weight
        return requests.put(StravaAPIRoutes.athlete, data)

    def get_activity(self, activity_id: int, include_all_efforts: bool = True, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.detailed_activity,
                        {"id": activity_id, "include_all_efforts": include_all_efforts},
                        max_age=max_age,
                        cache=cache)

    def list_activity_comments(self, activity_id: int, page_size: int = 30, after_cursor: str = None, max_age=None, cache=True):
        """
        Args:
            activity_id (int) The identifier of the activity.
            page_size (int) Number of items per page. Defaults to 30.
            after_cursor (str) Cursor of the last item in the previous page of results, used to request the subsequent page of results. When omitted, the first page of results is fetched.
        """
        return self.get(StravaAPIRoutes.list_activity_comments,
                        {"id": activity_id, "page_size": page_size, "after_cursor": after_cursor},
                        max_age=max_age,
                        cache=cache)

    def add_activity_comment(self, activity_id: int, text: str):
        return requests.post(StravaAPIRoutes.list_activity_comments,
                        {"id": activity_id, "text": text})

    def list_activity_kudos(self, activity_id: int, page: int = 1, per_page: int = 30, max_age=None, cache=True):
        """
        Args:
            activity_id (int) The identifier of the activity.
            page (int) Page number. Defaults to 1.
            per_page (int) Number of items per page. Defaults to 30.
        """
        return self.get(StravaAPIRoutes.list_activity_kudos,
                        {"id": activity_id, "page": page, "per_page": per_page},
                        max_age=max_age,
                        cache=cache)

    def list_activity_laps(self, activity_id: int, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.list_activity_laps,
                        {"id": activity_id},
                        max_age=max_age,
                        cache=cache)

    def get_athlete_zones(self, max_age=None, cache=True):
        zones = self.get(StravaAPIRoutes.athlete_zones, max_age=max_age, cache=cache)
        if zones and self.athlete_info:
            self.athlete_info["zones"] = zones
        return zones

    def get_athlete_stats(self, max_age=None, cache=True):
        stats = self.get(StravaAPIRoutes.athlete_stats, {"id": self.athlete_info["id"]}, max_age=max_age, cache=cache)
        if stats and self.athlete_info:
            self.athlete_info["stats"] = stats
        return stats

    def export_route_gpx_bytes(self, activity_id, max_age=None, cache=True):
        # / routes / {id} / export_gpx
        return self.get(StravaAPIRoutes.export_route_gpx,
                        {"id": activity_id},
                        max_age=max_age,
                        cache=cache).encode()

    def export_route_gpx_file(self, activity_id, filename=None, max_age=None, cache=True):
        if filename is None:
            if activity_id in self.all_activities:
                name = self.all_activities[activity_id]["name"].replace(" ", "_")
                disallowed = "<>:\"/\\|?*"
                name = "".join(c if c not in disallowed else "_" for c in name)
                start_date = self.all_activities[activity_id]["start_date_local"]
                start_date = start_date.replace(":", "_")
                filename = f"{start_date}_{name}_{activity_id}.gpx"
            else:
                filename = f"{activity_id}.gpx"
        b = self.export_route_gpx_bytes(activity_id, max_age=max_age, cache=cache)
        with open(filename, "wb") as f:
            f.write(b)
        return filename

    def export_route_tcx_bytes(self, activity_id, max_age=None, cache=True):
        # / routes / {id} / export_tcx
        return self.get(StravaAPIRoutes.export_route_tcx,
                        {"id": activity_id},
                        max_age=max_age,
                        cache=cache).encode()

    def export_route_tcx_file(self, activity_id, filename=None, max_age=None, cache=True):
        if filename is None:
            if activity_id in self.all_activities:
                name = self.all_activities[activity_id]["name"].replace(" ", "_")
                disallowed = "<>:\"/\\|?*"
                name = "".join(c if c not in disallowed else "_" for c in name)
                start_date = self.all_activities[activity_id]["start_date_local"]
                start_date = start_date.replace(":", "_")
                filename = f"{start_date}_{name}_{activity_id}.tcx"
            else:
                filename = f"{activity_id}.tcx"
        b = self.export_route_tcx_bytes(activity_id, max_age=max_age, cache=cache)
        with open(filename, "wb") as f:
            f.write(b)
        return b

    def get_route(self, route_id, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.get_route,
                        {"id": route_id},
                        max_age=max_age,
                        cache=cache)

    def list_athlete_routes(self, athlete_id=None, page: int = 1, per_page: int = 30, max_age=None, cache=True):
        if athlete_id is None:
            athlete_id = self.athlete_id
        return self.get("/athletes/{id}/routes",
                        {"id": athlete_id, "page": page, "per_page": per_page},
                        max_age=max_age,
                        cache=cache)

    def list_segment_efforts(self, segment_id, page: int = 1, per_page: int = 30, max_age=None, cache=True):
        """Requires subscription"""
        return self.get("/segments/{id}/all_efforts",
                        {"id": segment_id, "page": page, "per_page": per_page},
                        max_age=max_age,
                        cache=cache)

    def get_segment_effort(self, effort_id, max_age=None, cache=True):
        """Requires subscription"""
        return self.get("/segment_efforts/{id}",
                        {"id": effort_id},
                        max_age=max_age,
                        cache=cache)

    def explore_segments(self, bounds: list[float], activity_type: SportType,
                         min_cat: int, max_cat: int, max_age=None, cache=True, **kwargs):
        """Returns the top 10 segments matching a specified query.

        Args:
            bounds (list[float]): The latitude and longitude for two points describing a rectangular boundary for the search: [southwest corner latitutde, southwest corner longitude, northeast corner latitude, northeast corner longitude]
            activity_type (SportType): Desired activity type. May take one of the following values: running, riding
            min_cat (int): The minimum climbing category.
            max_cat (int): The maximum climbing category.
        """
        return self.get("/segments/explore",
                        {"bounds": ",".join(map(str, bounds)), "activity_type": activity_type, "min_cat": min_cat, "max_cat": max_cat, **kwargs},
                        max_age=max_age,
                        cache=cache)

    def list_starred_segments(self, athlete_id, page: int = 1, per_page: int = 30, max_age=None, cache=True):
        return self.get("/athletes/{id}/segments/starred",
                        {"id": athlete_id, "page": page, "per_page": per_page},
                        max_age=max_age,
                        cache=cache)

    def get_segment(self, segment_id, max_age=None, cache=True):
        return self.get("/segments/{id}",
                        {"id": segment_id},
                        max_age=max_age,
                        cache=cache)

    def star_segment(self, segment_id, starred: bool = True):
        return requests.put("/segments/{id}/star",
                            {"id": segment_id, "starred": starred})

    def get_activity_streams(self, activity_id, keys: list[str] = Streams.all, max_age=None, cache=True):
        return self.get(StravaAPIRoutes.activity_streams,
                        {"id": activity_id, "keys": ",".join(keys), "key_by_type": True},
                        max_age=max_age,
                        cache=cache)

    def get_route_streams(self, route_id, keys: list[str] = Streams.all, max_age=None, cache=True):
        return self.get("/routes/{id}/streams",
                        {"id": route_id, "keys": ",".join(keys), "key_by_type": True},
                        max_age=max_age,
                        cache=cache)

    def get_segment_effort_streams(self, effort_id, keys: list[str] = Streams.all, max_age=None, cache=True):
        return self.get("/segment_efforts/{id}/streams",
                        {"id": effort_id, "keys": ",".join(keys), "key_by_type": True},
                        max_age=max_age,
                        cache=cache)

    def get_segment_streams(self, segment_id, keys: list[str] = Streams.all, max_age=None, cache=True):
        return self.get("/segments/{id}/streams",
                        {"id": segment_id, "keys": ",".join(keys), "key_by_type": True},
                        max_age=max_age,
                        cache=cache)

    def get_upload(self, upload_id, max_age=None, cache=True):
        return self.get("/uploads/{id}",
                        {"id": upload_id},
                        max_age=max_age,
                        cache=cache)

    



if __name__ == "__main__":
    a = BareStravaAPI()
    print(a.athlete_info)
    print(a.get_athlete_stats())
    # a.open_docs()
