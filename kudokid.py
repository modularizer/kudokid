import datetime
from bare_strava_api import BareStravaAPI


class KudoKidAPI(BareStravaAPI):
    def __init__(self):
        super().__init__()
        self.get_athlete_info(zones=True, stats=True)

    def __repr__(self):
        return f'KudoKid({self.athlete_info.get("firstname", "Unknown")}, {self.athlete_info.get("lastname", "Unknown")})'

    def get_athlete_info(self, zones=False, stats=False, max_age=None, cache=True):
        self.athlete_info = self.get_athlete(max_age=max_age, cache=cache)
        if zones:
            self.athlete_info["zones"] = self.get_athlete_zones(max_age=max_age, cache=cache)
        if stats:
            self.athlete_info["stats"] = self.get_athlete_stats(max_age=max_age, cache=cache)

    def list_all_activities(self, after=None, max_age=None, cache=True):
        page = 1
        activities = True
        all_activities = []
        while activities:
            activities = self.get_activities(per_page=200, page=page, after=after, max_age=max_age, cache=cache)
            page += 1
            all_activities.extend(activities)
        all_activities.sort(key=lambda x: datetime.datetime.strptime(x["start_date"], "%Y-%m-%dT%H:%M:%SZ"), reverse=True)
        return all_activities

    def get_all_detailed_activities(self, max_age=None, cache=True):
        activities = self.list_all_activities(max_age=max_age, cache=cache)
        non_detailed_activities = [activity for activity in activities if not activity.get("detailed")]
        number_of_activities = len(non_detailed_activities)
        time_needed = ((15 * 60) / 200) * number_of_activities
        print(f"Estimated time needed: {(time_needed/60):.2f} minutes")

        detailed_activities = []
        for activity in activities:
            detailed_activity = self.get_detailed_activity(activity["id"], max_age=max_age, cache=cache)
            detailed_activities.append(detailed_activity)
        return detailed_activities


if __name__ == "__main__":
    ku = KudoKidAPI()
    activities = ku.get_all_detailed_activities()
