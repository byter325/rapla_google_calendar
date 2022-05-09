from __future__ import print_function
import datetime
from importlib.resources import path
import pickle
import os
from time import sleep
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import settings_manager

from rapla_fetch import RaplaFetch

def main():
    today = datetime.date.today()

    runningDate = today
    firstMondayInSemester = datetime.date(2022, 5, 9)
    if runningDate < firstMondayInSemester:
        runningDate = firstMondayInSemester
    lastMondayInSemester = datetime.date(2022, 8, 1)

    i = 0
    while runningDate.__add__(datetime.timedelta(days=7*i)) <= lastMondayInSemester:
        run(runningDate.__add__(datetime.timedelta(days=7*i)))
        i += 1
        sleep(5)
   

def run(date):

    dir = os.path.dirname(os.path.realpath(__file__))

    settings_manager.createSettingsIfNotExisting(dir)
    settings = settings_manager.loadSettings(dir)
    
    raplaURL = settings_manager.safeRetrieve(settings, 'rapla_url')
    calendarId = settings_manager.safeRetrieve(settings, 'calendar_key')
    ignoredCourses = settings_manager.readIgnoreCourses(dir)

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    #Date calculations
    todayAsWeekDay = date.weekday()
    startOfWeek = date.__sub__(datetime.timedelta(todayAsWeekDay))
    endOfWeek = date.__add__(datetime.timedelta(days=6 - todayAsWeekDay))

    startDateArr = [startOfWeek.day, startOfWeek.month, startOfWeek.year]
    endDateArr = [endOfWeek.day, endOfWeek.month, endOfWeek.year]

    service = authHandling(dir, SCOPES)

    #Fetch from Rapla
    entries = RaplaFetch().fetch(startDateArr[0], startDateArr[1], startDateArr[2], raplaURL, ignoredCourses)
    googlifiedEntries = googlifyEntries(entries)  

    startDateWithGoogleFormat = convertDateTimeToGoogleQueryFormat(startDateArr, "00:00")
    endDateWithGoogleFormat = convertDateTimeToGoogleQueryFormat(endDateArr, "00:00")
    
    #Call Calendar API
    readAndRemoveEntries(calendarId, service, startDateWithGoogleFormat, endDateWithGoogleFormat)

    insertEntries(calendarId, service, googlifiedEntries)

def insertEntries(calendarId, service, googlifiedEntries):
        for googleEvent in googlifiedEntries:
            googleEvent = service.events().insert(calendarId=calendarId, body=googleEvent).execute()

def readAndRemoveEntries(calendarId, service, startDateWithGoogleFormat, endDateWithGoogleFormat):
    #Read entries for week from calendar
    events_result = service.events().list(calendarId=calendarId, timeMin=startDateWithGoogleFormat, timeMax=endDateWithGoogleFormat,
                                        timeZone="Europe/Berlin").execute()
    readEvents = events_result.get('items', [])
    #clear entries
    for readEvent in readEvents:
        print(readEvent)
        if("(!)" in readEvent['summary']):
            continue
        service.events().delete(calendarId=calendarId, eventId = readEvent['id']).execute()

def googlifyEntries(entries):
    googlifiedEntries = []
    for entry in entries:
        event = {
            'summary': entry.title,
            'location': entry.location,
            'start' : {
                'dateTime':convertDateTimeToGoogleFormat(entry.date, entry.startTime),
                'timeZone':'GMT+01:00'
            },
            'end': {
                'dateTime':convertDateTimeToGoogleFormat(entry.date, entry.endTime),
                'timeZone':'GMT+01:00'
            }
        }
        if 'Klausur' in entry.title:
            event['colorId'] = 11
        dateArr = entry.date.split('.')
        dayMonthCombo = int(dateArr[1] + "" + dateArr[0])
        if dayMonthCombo >= 327 and dayMonthCombo <= 1030:
            event['start']['timeZone'] = 'GMT+02:00'
            event['end']['timeZone'] = 'GMT+02:00'
        

        googlifiedEntries.append(event)
    return googlifiedEntries

def authHandling(dir, SCOPES):
    creds = None
    if os.path.exists(dir + '/token.pickle'):
        with open(dir + '/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                dir + '/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(dir + '/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def convertDateTimeToGoogleFormat(date, time):
    dateArr = date.split('.')
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return f"{str(year)}-{str(month)}-{str(day)}T{str(time)}:00.000"

def convertDateTimeArrToGoogleFormat(dateArr, time):
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return f"{str(year)}-{str(month)}-{str(day)}T{str(time)}:00.000"

def convertDateTimeToGoogleQueryFormat(dateArr, time):
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return f"{str(year)}-{str(month)}-{str(day)}T{str(time)}:00+01:00"

if __name__ == '__main__':
    main()