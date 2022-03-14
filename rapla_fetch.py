from cgitb import text
from fs.opener import parse
import requests
from bs4 import BeautifulSoup
import re
import json
import datetime

class CalendarEntry:
    title = None
    date = None
    startTime = None
    endTime = None
    weekDay = None
    location = "None"
    def __init__(self) -> None:
        pass
    def build(self, title, dateTime, location):
        self.title = title
        dateTimeArr = dateTime.split(';')
        dayAndDate = dateTimeArr[0]
        time = dateTimeArr[1]
        self.weekDay = dayAndDate.split(' ')[0]
        date = dayAndDate.split(' ')[1]
        times = time.split('-')
        startTime = times[0]
        endTime = times[1]
        self.date = date
        self.startTime = startTime
        self.endTime = endTime
        self.location = location
        if(location == None):
            self.location = "None"
        if(location == "XOnline-Veranstaltung  Virtueller Raum"):
            self.location = "Online"
        return self

class IgnoreCourse():
    def __init__(self, title, weekDay, startTime, endTime) -> None:
        self.title = title
        self.weekDay = weekDay
        self.startTime = startTime
        self.endTime = endTime

class RaplaFetch():
    def __init__(self) -> None:
        self.dayTimePattern = "[A-Z][a-z] [0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]"
        self.dayTimeMatcher = re.compile(self.dayTimePattern)
        self.dayTimeAndDatePattern = "[A-Z][a-z] [0-3][0-9].[0-1][0-9].[0-2][0-4] [0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]"
        self.courseTitlePattern = "Titel: (\S+\s*)*Sprache"
        self.courseTitleMatcher = re.compile(self.courseTitlePattern)
        self.urlYearPattern = "year=\d\d\d\d"
        self.urlYearMatcher = re.compile(self.urlYearPattern)
    def fetch(self, day, month, yearParam, urlBase, ignoredCourses):
        URL = urlBase + str(day) + "&month="+ str(month) +"&year=" + str(yearParam)
        print(URL)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        weekDates = soup.find_all(class_="week_header")
        table = soup.find(class_="week_table").findChildren()
        table.pop(0)
        counter = 0
        weekDatesStrings = []
        for date in weekDates:
            string = date.text
            weekDatesStrings.append(string)
        year = str(self.urlYearMatcher.search(URL).group()).replace("year=","")
        entries = []

        totalHours = 0
        for child in table:
            block = child.findAll(class_="week_block")
            if block is not None:
                for blockChild in block:
                    aTag = blockChild.find('a')
                    if aTag is not None:
                        textArr = aTag.text.replace('\n', " ")
                        try:
                            date = self.findDateAsStringFromATag(textArr)[0]
                            title = self.findCourseTitleFromATag(textArr).strip()
                            resources = blockChild.findAll(class_="resource")
                            location = resources[len(resources) - 1].text
                            if len(date) > 14:
                                date = self.cleanDate(date)
                            entry = CalendarEntry().build(title, self.weekDayToDate(date, weekDatesStrings, year), location)
                            if not self.shouldCourseBeIgnoredByName(entry, ignoredCourses):
                                totalHours += self.getCourseLength(entry)
                                print(entry.__dict__)
                                entries.append(entry)
                        except:
                            pass
                        counter += 1

        print(totalHours/60)

        return entries

    def findDateAsStringFromATag(self, contents):
        standardPatternResults = re.findall(self.dayTimePattern, contents)
        if len(standardPatternResults) == 0:
            standardPatternResults = re.findall(self.dayTimeAndDatePattern, contents)
        return standardPatternResults

    def findCourseTitleFromATag(self, contents):
        title = contents.split('Titel:')[1].split("Sprache:")[0]
        return title

    def cleanDate(self, date):
        result = re.compile("\d\d.\d\d.\d\d").search(date).group()
        arr = date.split(result)
        returnArr = []
        for item in arr:
            returnArr.append(item.strip())
        return " ".join(returnArr)

    def weekDayToDate(self, dayTime, weekDates, year):
        weekDay = re.compile("[A-Z][a-z]").search(dayTime).group()
        dayTime = dayTime.replace(weekDay, '').strip()
        if weekDay == 'Mo':
            return weekDates[0] + year + ";" + dayTime
        if weekDay == 'Di':
            return weekDates[1] + year + ";" + dayTime
        if weekDay == 'Mi':
            return weekDates[2] + year + ";" + dayTime
        if weekDay == 'Do':
            return weekDates[3] + year + ";" + dayTime
        if weekDay == 'Fr':
            return weekDates[4] + year + ";" + dayTime
        if weekDay == 'Sa':
            return weekDates[5] + year + ";" + dayTime

        return "Error"

    def shouldCourseBeIgnored(self, courseObj, ignoredCourses):
        for ignoredCourse in ignoredCourses:
            if courseObj.title == ignoredCourse.title and courseObj.weekDay == ignoredCourse.weekDay and courseObj.startTime == ignoredCourse.startTime and courseObj.endTime == ignoredCourse.endTime:
                return True
        return False
    def shouldCourseBeIgnoredByName(self, courseObj, ignoredCourses):
        for ignoredCourse in ignoredCourses:
            if ignoredCourse.title in courseObj.title:
                return True
        return False

    def weekDayDateToFileString(self, weekDayDate, year):
        return weekDayDate.split(' ')[1].replace('.','_') + year

    def getCourseLength(self, course):
        startTime = course.startTime.split(':')
        endTime = course.endTime.split(':')

        startHour = int(startTime[0])
        startMinutes = int(startTime[1])
        totalStartTimeInSeconds = startHour * 60 * 60 + startMinutes * 60
        
        endHour = int(endTime[0])
        endMinutes = int(endTime[1])
        totalEndTimeInSeconds = endHour * 60 * 60 + endMinutes * 60

        diff = totalEndTimeInSeconds - totalStartTimeInSeconds
        return diff / 60
    def jsonCoursesToIgnoreCourses(jsonCourses):
        for course in jsonCourses:
            pass #Load each course as JSON and turn in IgnoreCourse object