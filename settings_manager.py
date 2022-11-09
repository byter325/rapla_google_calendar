import json
import os

from rapla_fetch import IgnoreCourse


def readSettingsFromEnv():
    value = os.environ.get("settings")
    settings = json.load(value)
    if settings is None:
        raise("An error occured while loading settings via the env")
    return settings


def readIgnoredCoursesFromEnv():
    coursesToIgnore = readSettingsFromEnv["ignoredCourses"]
    ignoreCoursesArr = []
    for course in coursesToIgnore:
        ignoreCoursesArr.append(IgnoreCourse(course["title"], "", "", ""))
    return ignoreCoursesArr


def createSettingsIfNotExisting(dir):
    if not os.path.exists(dir + "/settings.json"):
        with open(dir + "/settings.json", "w") as f:
            x = '{ "calendar_key":"None", "rapla_url":"None", "ignoredCourses":[{"name":"Name"}]}'
            f.write(x)


def loadSettings(dir):
    with open(dir + "/settings.json") as settingsReader:
        settings = json.load(settingsReader)
    if settings is None:
        settings = json.load(
            '{"unavailable":"an error occured while loading"}')
    return settings


def safeRetrieve(settings, attribute):
    try:
        return settings[attribute]
    except KeyError:
        return None


def readIgnoreCourses(dir):
    with open(dir + "/settings.json") as settingsReader:
        settings = json.load(settingsReader)
        coursesToIgnore = settings["ignoredCourses"]

        ignoreCoursesArr = []
        for course in coursesToIgnore:
            ignoreCoursesArr.append(IgnoreCourse(course["title"], "", "", ""))

    return ignoreCoursesArr
