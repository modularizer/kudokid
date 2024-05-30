CREATE TABLE IF NOT EXISTS scopes (
  scope VARCHAR(255) PRIMARY KEY
);

INSERT INTO scopes (scope) VALUES ('read');
INSERT INTO scopes (scope) VALUES ('read_all');
INSERT INTO scopes (scope) VALUES ('profile:read_all');
INSERT INTO scopes (scope) VALUES ('profile:write');
INSERT INTO scopes (scope) VALUES ('activity:read');
INSERT INTO scopes (scope) VALUES ('activity:read_all');
INSERT INTO scopes (scope) VALUES ('activity:write');

------------------------------------------- Stream Types ---------------------------------------------------
CREATE TABLE IF NOT EXISTS stream_types (
  stream_type VARCHAR(255) PRIMARY KEY
);

INSERT INTO stream_types (stream_type) VALUES ('time');
INSERT INTO stream_types (stream_type) VALUES ('latlng');
INSERT INTO stream_types (stream_type) VALUES ('distance');
INSERT INTO stream_types (stream_type) VALUES ('altitude');
INSERT INTO stream_types (stream_type) VALUES ('velocity_smooth');
INSERT INTO stream_types (stream_type) VALUES ('heartrate');
INSERT INTO stream_types (stream_type) VALUES ('cadence');
INSERT INTO stream_types (stream_type) VALUES ('watts');
INSERT INTO stream_types (stream_type) VALUES ('temp');
INSERT INTO stream_types (stream_type) VALUES ('moving');
INSERT INTO stream_types (stream_type) VALUES ('grade_smooth');

------------------------------------------- Resource States ---------------------------------------------------
CREATE TABLE resource_states (
  id INTEGER PRIMARY KEY,
  resource_state INTEGER,
  name VARCHAR(255)
);

INSERT INTO resource_state (resource_state, name) VALUES (1, 'meta');
INSERT INTO resource_state (resource_state, name) VALUES (2, 'summary');
INSERT INTO resource_state (resource_state, name) VALUES (3, 'detail');

------------------------------------------- Sport Types ---------------------------------------------------
CREATE TABLE sport_types (
  sport_type VARCHAR(255) PRIMARY KEY
);

INSERT INTO sport_types (sport_type) VALUES ('cycling');
INSERT INTO sport_types (sport_type) VALUES ('running');
INSERT INTO sport_types (sport_type) VALUES ('triathlon');
INSERT INTO sport_types (sport_type) VALUES ('other');

------------------------------------------- Activity Types ---------------------------------------------------
CREATE TABLE activity_types (
  activity_type VARCHAR(255) PRIMARY KEY
);

INSERT INTO activity_types (activity_type) VALUES ('AlpineSki');
INSERT INTO activity_types (activity_type) VALUES ('BackcountrySki');
INSERT INTO activity_types (activity_type) VALUES ('Canoeing');
INSERT INTO activity_types (activity_type) VALUES ('Crossfit');
INSERT INTO activity_types (activity_type) VALUES ('EBikeRide');
INSERT INTO activity_types (activity_type) VALUES ('Elliptical');
INSERT INTO activity_types (activity_type) VALUES ('Golf');
INSERT INTO activity_types (activity_type) VALUES ('Handcycle');
INSERT INTO activity_types (activity_type) VALUES ('Hike');
INSERT INTO activity_types (activity_type) VALUES ('IceSkate');
INSERT INTO activity_types (activity_type) VALUES ('InlineSkate');
INSERT INTO activity_types (activity_type) VALUES ('Kayaking');
INSERT INTO activity_types (activity_type) VALUES ('Kitesurf');
INSERT INTO activity_types (activity_type) VALUES ('NordicSki');
INSERT INTO activity_types (activity_type) VALUES ('Ride');
INSERT INTO activity_types (activity_type) VALUES ('RockClimbing');
INSERT INTO activity_types (activity_type) VALUES ('RollerSki');
INSERT INTO activity_types (activity_type) VALUES ('Rowing');
INSERT INTO activity_types (activity_type) VALUES ('Run');
INSERT INTO activity_types (activity_type) VALUES ('Sail');
INSERT INTO activity_types (activity_type) VALUES ('Skateboard');
INSERT INTO activity_types (activity_type) VALUES ('Snowboard');
INSERT INTO activity_types (activity_type) VALUES ('Snowshoe');
INSERT INTO activity_types (activity_type) VALUES ('Soccer');
INSERT INTO activity_types (activity_type) VALUES ('StairStepper');
INSERT INTO activity_types (activity_type) VALUES ('StandUpPaddling');
INSERT INTO activity_types (activity_type) VALUES ('Surfing');
INSERT INTO activity_types (activity_type) VALUES ('Swim');
INSERT INTO activity_types (activity_type) VALUES ('Velomobile');
INSERT INTO activity_types (activity_type) VALUES ('VirtualRide');
INSERT INTO activity_types (activity_type) VALUES ('VirtualRun');
INSERT INTO activity_types (activity_type) VALUES ('Walk');
INSERT INTO activity_types (activity_type) VALUES ('WeightTraining');
INSERT INTO activity_types (activity_type) VALUES ('Wheelchair');
INSERT INTO activity_types (activity_type) VALUES ('Windsurf');
INSERT INTO activity_types (activity_type) VALUES ('Workout');
INSERT INTO activity_types (activity_type) VALUES ('Yoga');

------------------------------------------- Membership Statuses ---------------------------------------------------
CREATE TABLE membership_statuses (
  membership VARCHAR(255) PRIMARY KEY
);

INSERT INTO membership_statuses (membership) VALUES ('member');
INSERT INTO membership_statuses (membership) VALUES ('pending');

------------------------------------------- Measurement Preferences ---------------------------------------------------
CREATE TABLE measurement_preferences (
  measurement_preference VARCHAR(8) PRIMARY KEY
);

INSERT INTO measurement_preferences (measurement_preference) VALUES ('feet');
INSERT INTO measurement_preferences (measurement_preference) VALUES ('meters');

------------------------------------------- Sexes ------------------------------------------------
CREATE TABLE sexes (
    sex VARCHAR(1) PRIMARY KEY
);

INSERT INTO sexes(sex) VALUES ('M');
INSERT INTO sexes(sex) VALUES ('F');

------------------------------------------- Workout Types ---------------------------------------------------
CREATE TABLE workout_types (
    workout_type INTEGER PRIMARY KEY,
    name VARCHAR(255)
);

INSERT INTO workout_types (workout_type) VALUES (0);
INSERT INTO workout_types (workout_type) VALUES (1);
INSERT INTO workout_types (workout_type) VALUES (2);
INSERT INTO workout_types (workout_type) VALUES (3);
INSERT INTO workout_types (workout_type) VALUES (4);
INSERT INTO workout_types (workout_type) VALUES (5);
INSERT INTO workout_types (workout_type) VALUES (6);
INSERT INTO workout_types (workout_type) VALUES (7);
INSERT INTO workout_types (workout_type) VALUES (8);
INSERT INTO workout_types (workout_type) VALUES (9);
INSERT INTO workout_types (workout_type) VALUES (10);

--------------------------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY, -- The unique identifier of this athlete
    resource_state INTEGER REFERENCES resource_states(id), -- Resource state, indicates level of detail. Possible values: 1 -> meta, 2 -> summary, 3 -> detail
    firstname VARCHAR(255), -- The athlete's first name.
    lastname VARCHAR(255), -- The athlete's last name.
    profile_medium VARCHAR(255), -- URL to a 60x60 pixel profile picture.
    profile VARCHAR(255), -- URL to a 124x124 pixel profile picture.
    city VARCHAR(255), -- The athlete's city.
    state VARCHAR(255), -- The athlete's state or geographical region.
    country VARCHAR(255), -- The athlete's country.
    sex VARCHAR(255) REFERENCES sexes(sex), -- The athlete's sex. May take one of the following values: 'M', 'F'.
    premium BOOLEAN, -- Deprecated. Use summit field instead. Whether the athlete has any Summit subscription.
    summit BOOLEAN, -- Whether the athlete has any Summit subscription.
    created_at INTEGER, -- The time at which the athlete was created.
    updated_at INTEGER, -- The time at which the athlete was last updated.
    follower_count INTEGER, -- The athlete's follower count.
    friend_count INTEGER, -- The athlete's friend count.
    measurement_preference VARCHAR(8) REFERENCES measurement_preferences(measurement_preference), -- The athlete's default measurement preference. May take one of the following values: 'feet', 'meters'.
    ftp INTEGER, -- The athlete's FTP (Functional Threshold Power).
    weight FLOAT, -- The athlete's weight.
--    clubs INTEGER REFERENCES clubs(id), -- The athlete's clubs.
--    bikes INTEGER REFERENCES gear(id), -- The athlete's bikes.
--    shoes INTEGER REFERENCES shoes(id) -- The athlete's shoes.
);

CREATE TABLE IF NOT EXISTS auth ( -- this table does not mirror a definition in the Strava API
  athlete_id INTEGER REFERENCES athletes(id),
  access_token VARCHAR(255),
  refresh_token VARCHAR(255),
  expires_at INTEGER,
  token_type VARCHAR(255),
  scope VARCHAR(255),
  created_at INTEGER,
  updated_at INTEGER
);

CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY, -- The unique identifier of this club
    resource_state INTEGER REFERENCES resource_states(id), -- Resource state, indicates level of detail. Possible values: 1 -> meta, 2 -> summary, 3 -> detail
    name VARCHAR(255), -- The club's name.
    profile_medium VARCHAR(255), -- URL to a 60x60 pixel profile picture.
    cover_photo VARCHAR(255),  -- URL to a ~1185x580 pixel cover photo.
    cover_photo_small VARCHAR(255), -- URL to a ~360x176  pixel cover photo.
    sport_type VARCHAR(255), -- The club's sport type.
    --activity_types ActivityType,
    city VARCHAR(255), -- The club's city.
    state VARCHAR(255), -- The club's state or geographical region.
    country VARCHAR(255), -- The club's country.
    private BOOLEAN, -- Whether the club is private.
    member_count INTEGER, -- The club's member count.
    featured BOOLEAN, -- Whether the club is featured or not.
    verified BOOLEAN, -- Whether the club is verified or not.
    url VARCHAR(255), -- The club's vanity URL.
    membership VARCHAR(255) REFERENCES membership_statuses(membership), -- The authenticated athlete's membership status of 'member' or 'pending'.
    admin BOOLEAN, -- Whether the authenticated athlete is an administrator of the club.
    owner BOOLEAN, -- Whether the authenticated athlete is the owner of the club.
    following_count INTEGER -- The number of athletes in the club that the authenticated athlete follows.
);

CREATE TABLE club_activity_types (
    club_id INTEGER, -- The unique identifier of the club
    activity_type VARCHAR(255), -- The club's activity type.
    PRIMARY KEY (club_id, activity_type), -- The primary key of the table
    FOREIGN KEY (club_id) REFERENCES clubs(id) -- The foreign key of the club
);

CREATE TABLE IF NOT EXISTS gear (
    id INTEGER PRIMARY KEY, -- The unique identifier of this segment
    resource_state INTEGER, -- Resource state, indicates level of detail. Possible values: 1 -> meta, 2 -> summary, 3 -> detail
    primary BOOLEAN, -- Whether this gear's is the owner's default one.
    name VARCHAR(255), -- The gear's name.
    distance FLOAT, -- The distance logged with this gear.
    brand_name VARCHAR(255), -- The gear's brand name.
    model_name VARCHAR(255), -- The gear's model name.
    frame_type VARCHAR(255), -- The gear's frame type (bike only).
    description VARCHAR(255), -- The gear's description.
    external_id VARCHAR(255), -- The gear's external identifier.

    -- not in the API, but found in responses
    converted_distance FLOAT, -- The distance logged with this gear in the athlete's default measurement preference.
    retired BOOLEAN, -- Whether this gear's is the owner's default one.
);


CREATE TABLE athlete_clubs (
    athlete_id INTEGER, -- The unique identifier of the athlete
    club_id INTEGER, -- The unique identifier of the club
    PRIMARY KEY (athlete_id, club_id),
    FOREIGN KEY (athlete_id) REFERENCES athletes(id),
    FOREIGN KEY (club_id) REFERENCES clubs(id)
);

CREATE TABLE athlete_bikes (
    athlete_id INTEGER, -- The unique identifier of the athlete
    gear_id INTEGER, -- The unique identifier of the gear
    PRIMARY KEY (athlete_id, gear_id),
    FOREIGN KEY (athlete_id) REFERENCES athletes(id),
    FOREIGN KEY (gear_id) REFERENCES gear(id)
);

CREATE TABLE athlete_shoes (
    athlete_id INTEGER, -- The unique identifier of the athlete
    gear_id INTEGER, -- The unique identifier of the gear
    PRIMARY KEY (athlete_id, gear_id),
    FOREIGN KEY (athlete_id) REFERENCES athletes(id),
    FOREIGN KEY (gear_id) REFERENCES gear(id)
);

CREATE TABLE activity_total (
    updated_at INTEGER, -- The time at which the stats were last updated.
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- The unique identifier of the activity.
    count INTEGER, -- The number of activities for the athlete.
    distance FLOAT, -- The total distance for the athlete.
    moving_time INTEGER, -- The total moving time for the athlete.
    elapsed_time INTEGER, -- The total elapsed time for the athlete.
    elevation_gain FLOAT, -- The total elevation gain for the athlete.
    achievement_count INTEGER -- The total number of achievements for the athlete.
);

CREATE TABLE activity_stats (
    athlete_id INTEGER, -- The unique identifier of the athlete
    updated_at INTEGER, -- The time at which the stats were last updated.
    biggest_ride_distance FLOAT, -- The longest distance ridden by the athlete.
    biggest_climb_elevation_gain FLOAT, -- The highest climb ridden by the athlete.
    recent_ride_totals INTEGER REFERENCES activity_total(id), -- The recent (last 4 weeks) ride statistics for the athlete.
    recent_run_totals INTEGER REFERENCES activity_total(id), -- The recent (last 4 weeks) run statistics for the athlete.
    recent_swim_totals INTEGER REFERENCES activity_total(id), -- The recent (last 4 weeks) swim statistics for the athlete.
    ytd_ride_totals INTEGER REFERENCES activity_total(id), -- The year to date ride statistics for the athlete.
    ytd_run_totals INTEGER REFERENCES activity_total(id), -- The year to date run statistics for the athlete.
    ytd_swim_totals INTEGER REFERENCES activity_total(id), -- The year to date swim statistics for the athlete.
    all_ride_totals INTEGER REFERENCES activity_total(id), -- The all time ride statistics for the athlete.
    all_run_totals INTEGER REFERENCES activity_total(id), -- The all time run statistics for the athlete.
    all_swim_totals INTEGER REFERENCES activity_total(id), -- The all time swim statistics for the athlete.
);


CREATE TABLE photo_urls (
    id INTEGER PRIMARY KEY, -- The unique identifier of the photo
    name VARCHAR(255), -- The photo's name
    url VARCHAR(255) -- The photo's URL
);

CREATE TABLE photos (
    id INTEGER PRIMARY KEY, -- The unique identifier of the photo
    source INTEGER, -- The source of the photo. Possible values: 1 -> Strava, 2 -> Instagram
    unique_id VARCHAR(255), -- The unique identifier of the photo on Instagram
);

CREATE TABLE splits (
    average_speed FLOAT, -- The split's average speed, in meters per second
    distance FLOAT, -- The split's distance, in meters
    elapsed_time INTEGER, -- The split's elapsed time, in seconds
    elevation_difference FLOAT, -- The split's elevation difference, in meters
    pace_zone INTEGER -- The split's pace zone
    moving_time INTEGER, -- The split's moving time, in seconds
    split INTEGER, -- The split's number
);

CREATE TABLE laps (
    id INTEGER PRIMARY KEY, -- The unique identifier of the lap
    activity INTEGER REFERENCES activities(id), -- The unique identifier of the activity
    athlete INTEGER REFERENCES athletes(id), -- The unique identifier of the athlete
    average_cadence FLOAT, -- The lap's average cadence
    average_speed FLOAT, -- The lap's average speed
    distance FLOAT, -- The lap's distance
    elapsed_time INTEGER, -- The lap's elapsed time
    start_index INTEGER, -- The index of the start of this lap in the list of activities
    end_index INTEGER, -- The index of the end of this lap in the list of activities
    lap_index INTEGER, -- The lap's index
    max_speed FLOAT, -- The lap's max speed
    moving_time INTEGER, -- The lap's moving time
    name VARCHAR(255), -- The lap's name
    pace_zone INTEGER, -- The lap's pace zone
    split INTEGER, -- The lap's split
    start_date TIMESTAMP, -- The time at which the lap was started
    start_date_local TIMESTAMP, -- The time at which the lap was started in the local timezone
    total_elevation_gain FLOAT -- The lap's total elevation gain
);

CREATE TABLE latlng (
    id INTEGER PRIMARY KEY, -- The unique identifier of the latlng
    lat FLOAT, -- The latitude of the point
    lng FLOAT -- The longitude of the point
);

CREATE TABLE polyline_maps (
    id INTEGER PRIMARY KEY, -- The unique identifier of the polyline map
    polyline TEXT, --The polyline of the map, only returned on detailed representation of an object
    summary_polyline TEXT -- The summary polyline of the route
);

CREATE TABLE activities (
    id INTEGER PRIMARY KEY, -- The unique identifier of the activity
    resource_state INTEGER REFERENCES resource_states(id), -- Resource state, indicates level of detail. Possible values: 1 -> meta, 2 -> summary, 3 -> detail
    external_id VARCHAR(255), -- The identifier provided at upload time.
    upload_id INTEGER, -- The identifier of the upload that resulted in this activity.
    athlete_id INTEGER REFERENCES athletes(id), -- The unique identifier of the athlete who performed the activity.
    name VARCHAR(255), -- The name of the activity.
    distance FLOAT, -- The activity's distance, in meters.
    moving_time INTEGER, -- The activity's moving time, in seconds.
    elapsed_time INTEGER, -- The activity's elapsed time, in seconds.
    total_elevation_gain FLOAT, -- The activity's total elevation gain.
    elev_high FLOAT, -- The activity's highest elevation, in meters.
    elev_low FLOAT, -- The activity's lowest elevation, in meters.
    type VARCHAR(255) REFERENCES activity_types(activity_type), -- The activity's type.
    start_date TIMESTAMP, -- The time at which the activity was started.
    start_date_local TIMESTAMP, -- The time at which the activity was started in the local timezone.
    timezone VARCHAR(255), -- The timezone of the activity.
    start_latlng INTEGER REFERENCES latlng(id), -- The start latitude and longitude of the activity.
    end_latlng INTEGER REFERENCES latlng(id), -- The end latitude and longitude of the activity.
    achievement_count INTEGER, -- The number of achievements by the authenticated athlete during this activity.
    kudos_count INTEGER, -- The number of kudos given for this activity.
    comment_count INTEGER, -- The number of comments for this activity.
    athlete_count INTEGER, -- The number of athletes for taking part in a group activity.
    photo_count INTEGER, -- The number of Instagram photos for this activity.
    total_photo_count INTEGER, -- The number of Instagram and Strava photos for this activity.
    map INTEGER REFERENCES polyline_maps(id), -- The activity's map summary.
    trainer BOOLEAN, -- Whether the activity was recorded on a training machine.
    commute BOOLEAN, -- Whether the activity is a commute.
    manual BOOLEAN, -- Whether the activity was created manually.
    private BOOLEAN, -- Whether the activity is private.
    flagged BOOLEAN, -- Whether the activity is flagged.
    workout_type INTEGER REFERENCES workout_types(id), -- The activity's workout type.
    upload_id_str VARCHAR(255), -- The identifier of the upload that resulted in this activity.
    average_speed FLOAT, -- The activity's average speed, in meters per second.
    max_speed FLOAT, -- The activity's max speed, in meters per second.
    has_kudoed BOOLEAN, -- Whether the authenticated athlete has kudoed this activity.
    hide_from_home BOOLEAN, -- Whether this activity should be hidden when viewed within a segment effort.
    gear_id INTEGER REFERENCES gear(id), -- The identifier of the gear associated with the activity. 'none' should be used if no gear is associated with the activity.
    kilojoules FLOAT, -- The activity's kilojoules.
    average_watts FLOAT, -- The activity's average power, in watts.
    device_watts BOOLEAN, -- Whether the watts are from a power meter, false if estimated.
    max_watts FLOAT, -- The activity's max power, in watts.
    weighted_average_watts FLOAT, -- The weighted average power of the activity.
    description VARCHAR(255), -- The description of the activity.
    --photos
    --gear
    calories FLOAT, -- The number of kilocalories consumed during this activity.
--    segment_efforts INTEGER, -- The activity's segment efforts.
    device_name VARCHAR(255), -- The name of the device used to record the activity.
    embed_token VARCHAR(255), -- The token used to embed a Strava activity.
--    splits_metric INTEGER, -- The splits of this activity in metric units.
--    splits_standard INTEGER, -- The splits of this activity in imperial units.
--    laps INTEGER, -- The laps of this activity.
    --best_efforts
 );

 CREATE TABLE activity_splits_metric (
    activity_id INTEGER, -- The unique identifier of the activity
    split_id INTEGER, -- The unique identifier of the split
    PRIMARY KEY (activity_id, split_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (split_id) REFERENCES splits(id)
);


CREATE TABLE activity_splits_standard (
    activity_id INTEGER, -- The unique identifier of the activity
    split_id INTEGER, -- The unique identifier of the split
    PRIMARY KEY (activity_id, split_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (split_id) REFERENCES splits(id)
);

CREATE TABLE activity_laps (
    activity_id INTEGER, -- The unique identifier of the activity
    lap_id INTEGER, -- The unique identifier of the lap
    PRIMARY KEY (activity_id, lap_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (lap_id) REFERENCES laps(id)
);

 CREATE TABLE activity_photos (
    activity_id INTEGER, -- The unique identifier of the activity
    photo_id INTEGER, -- The unique identifier of the photo
    PRIMARY KEY (activity_id, photo_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (photo_id) REFERENCES photos(id)
);

CREATE TABLE activity_gear (
    activity_id INTEGER, -- The unique identifier of the activity
    gear_id INTEGER, -- The unique identifier of the gear
    PRIMARY KEY (activity_id, gear_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (gear_id) REFERENCES gear(id)
);


