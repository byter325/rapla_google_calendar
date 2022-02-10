import json
import os

def createSettingsIfNotExisting(dir):
    if not os.path.exists(dir + "/settings.json"):
        with open(dir + "/settings.json", "w") as f:
            x = '{ "calendar_key":"None", "rapla_url":"None", "ignoredCourses":[{"name":"Name"}]}'
            f.write(x)

def loadSettings(dir):
    with open(dir + "/settings.json") as settingsReader:
        settings = json.load(settingsReader)
    if settings is None:
        settings = json.load('{"unavailable":"an error occured while loading"}')
    return settings

def safeRetrieve(settings, attribute):
    try:
        return settings[attribute]
    except KeyError:
        return None