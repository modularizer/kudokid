import datetime
from bare_strava_api import BareStravaAPI


class KudoKidAPI(BareStravaAPI):
    def __init__(self,
                 get_athlete=True,
                 list_all_activities=True,
                 get_athlete_zones=True,
                 get_athlete_stats=True):
        super().__init__(get_athlete=get_athlete,
                         list_all_activities=list_all_activities,
                         get_athlete_zones=get_athlete_zones,
                         get_athlete_stats=get_athlete_stats)

    def __repr__(self):
        return f'KudoKid({self.athlete_info.get("firstname", "Unknown")}, {self.athlete_info.get("lastname", "Unknown")})'

    def get_all_detailed_activities(self, max_age=None, cache=True):
        activities = self.list_all_activities(max_age=max_age, cache=cache)
        non_detailed_activities = [activity for activity in activities if not activity.get("detailed")]
        number_of_activities = len(non_detailed_activities)
        time_needed = ((15 * 60) / 200) * number_of_activities
        print(f"Estimated time needed: {(time_needed/60):.2f} minutes")

        detailed_activities = []
        for activity in activities:
            detailed_activity = self.get_activity(activity["id"], max_age=max_age, cache=cache)
            detailed_activities.append(detailed_activity)
        return detailed_activities


if __name__ == "__main__":
    ku = KudoKidAPI()
    activities = ku.get_all_detailed_activities()
