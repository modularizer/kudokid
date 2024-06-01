# KudoKid
Playing with the Strava API. There really is no solid purpose or goal to this yet, aside from just seeing what Strava API has to offer.
Think of this repo as a playground, not actually accomplishing any specific task.


# Setup
### Install Requirements
1. Install Python >= 3.10
  * [Install from python.org](https://www.python.org/downloads/)
    * See [help](https://www.digitalocean.com/community/tutorials/install-python-windows-10)
    * Make sure to check the box that says "Add Python to PATH"
    * You can check if you have python installed by running `python --version` in a terminal
    * You can check if you have pip installed by running `pip --version` in a terminal
2. Install git
  * [Install from git-scm.com](https://git-scm.com/downloads)
    * You can check if you have git installed by running `git --version` in a terminal
3. Git clone this repository
  * Open up a command prompt
  * `cd` to the directory you want to clone the repository to, e.g. `cd Documents`
  * you should see `C:\Users\<your username>\Documents>`
  * run `git clone git@github.com:modularizer/kudokid.git`
  * you should see a new directory called `kudokid` in your `Documents` directory
  * `cd kudokid`
  * you should see `C:\Users\<your username>\Documents\kudokid>`
4. Setup a virtual environment
  * run `python -m venv venv`
  * run `venv\Scripts\activate` to activate the virtual environment
  * you should see `(venv)` at the beginning of your command prompt
  * run `pip install -r requirements.txt`

### First Run
With your virtual environment setup and activated, you should be able to run the program.
1. `python -m kudokid` or `python kudokid.py`

2. The first time you run the program, it won't find `secrets.yaml` so it will walk you through setting up your Strava API credentials...
   i. it will have you go to https://www.strava.com/settings/api for you to create your App 
   ii. prompt you to enter your 'Client ID' and 'Client Secret' (which will then get saved to a new file named `secrets.yaml`)
   iii. open a browser window for you to authenticate your app with Strava (which will then save your access token and refresh token to `secrets.yaml`)

# Developing
Once authenticated, you can start playing with the Strava API by modifying `kudokid.py`, extending it, or calling functions.

## NOTE: I highly recommend using `Run in Python Console` in PyCharm to run the program. It is sort of a mix between REPL and debugger functionalities and allows for you to easily inspect your variables and run code snippets in the context of the program.

# Resources From Strava
* [Getting Started](https://developers.strava.com/docs/getting-started/)
* [Authenticating with OAuth 2.0](https://developers.strava.com/docs/authentication/)
* [Strava API Reference](https://developers.strava.com/docs/reference/)

# Data Storage
### Storing Credentials
Right now, api tokens get cached to disk in a file named `secrets.yaml`. This file should get created when you do the initial setup and updated whenever you re-authenticate.

It looks like this (but with your actual tokens):
```yaml
access_token: 4317bdb2430f927663ba6017f6af81b155f19a34 # <your access token (returned by POST to https://www.strava.com/oauth/token)
client_id: 175225 #your client id (found at https://www.strava.com/settings/api)
client_secret: c11db87d96189d36cd7ca9a1291e7f5e065b25e1 # your client secret (found at https://www.strava.com/settings/api)
expires_at: 1717284168 # epoch timestamp integer of when the token expires  (returned by POST to https://www.strava.com/oauth/token)
refresh_token: 1f3f5348ae862ca8dfcfbbb636f2677b446ffb00 # your refresh token (returned by POST to https://www.strava.com/oauth/token)
scope: read,activity:write,activity:read,activity:read_all,profile:write,profile:read_all,read_all # whatever scope you requested
```

### Caching API Responses
Due to [Strava API Rate Limits](https://developers.strava.com/docs/rate-limits/), it is a good idea to store the data you retrieve from Strava locally,
especially because most of the data you will be interested in will be static once the activity is completed.

At first I considered trying to mirror Strava's database structure locally in a super organized way, but that is a pretty big task and would result in a LOT of code.
What I did instead is make a SQLite database with a single table which caches the url's of API calls, the time you call it and the parameters you pass, and the responses you get.

This way, if you call the same API with the same parameters, you can just pull the response from the database instead of making the API call again.
I use a `max_age` parameter to determine if you should make the API call again or just use the cached response (e.g. if there is a record of the same call within the max_age timeframe and it received a status code 200, we use the cached response).

This `requests` table looks like this:

| id | called_at        | called_at_str               | url                                   | headers | params | method | response_code | response_json                        | response_headers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|----|------------------|-----------------------------|---------------------------------------|---------|--------|--------|---------------|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | 1717262808.07453 | 2024-06-01 10:26:48.074527  | https://www.strava.com/api/v3/athlete |         |        | GET    | 200           | {"id": 23032, "username": "modu... } | {"Content-Type": "application/json; charset=utf-8", "Transfer-Encoding": "chunked", "Connection": "keep-alive", "Date": "Sat, 01 Jun 2024 17:26:48 GMT", "X-Content-Type-Options": "nosniff", "X-Permitted-Cross-Domain-Policies": "none", "Via": "1.1 linkerd, 1.1 linkerd, 1.1 8e16c7938d4a57727005da6f93b9da6a.cloudfront.net (CloudFront)", "ETag": "W/\"f37c6b7e34e4570ca4e2\"", "Vary": "Accept, Origin", "Status": "200 OK", "X-Request-Id": "41a0e296-1f34-4d", "Cache-Control": "max-age=0, private, must-revalidate", "Referrer-Policy": "strict-origin-when-cross-origin", "X-Frame-Options": "DENY", "Content-Encoding": "gzip", "X-XSS-Protection": "1; mode=block", "X-RateLimit-Limit": "200,2000", "X-RateLimit-Usage": "1,211", "X-Download-Options": "noopen", "X-ReadRateLimit-Limit": "100,1000", "X-ReadRateLimit-Usage": "1,211", "X-Cache": "Miss from cloudfront", "X-Amz-Cf-Pop": "LAX50-P3", "X-Amz-Cf-Id": "aGamSBHtYYowW_sEm_25r9H=="}  |



# Code Structure
* `api_cache.py` - handles caching API responses in a SQLite database to avoid rate limits
  * not in any way specific to strava, could be used for any API
* `strava_oauth.py` - handles the OAuth2.0 authentication with Strava
  * runs a background thread to refresh the access token when it expires
  * if the refresh token is expired, it will open up a browser window for you to re-authenticate Strava
* `bare_strava_api.py` - combines the API cache and the Strava OAuth to provide an easy way to make API calls
  * enumerates _some_ of the Strava API endpoints and types
  * adds a little bit of ease of use to the Strava API
  * `BareStravaAPI` is a class intended to be generic and useful for anyone to develop and relatively free of my own goals with the Strava API
* `kudokid.py` - this is intended to be my clutter-free playground to start developing features around the Strava API

