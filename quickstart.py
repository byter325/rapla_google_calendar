from __future__ import print_function
import datetime
from importlib.resources import path
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import fs

from rapla_fetch import RaplaFetch

dir = os.path.dirname(os.path.realpath(__file__))
print(dir)
settingsReader = open(dir + "/settings.json")
settings = json.load(settingsReader)
settingsReader.close()
print(settings)
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
calendarId = settings['calendar_key']
ignoredCourses = settings["ignoredCourses"]


def main():
    today = datetime.date.today()
    
    #Run for the current week
    run(today)

    #Run for the next 2 weeks
    run(today.__add__(datetime.timedelta(days=7)))
    run(today.__add__(datetime.timedelta(days=14)))
   

def run(date):

    todayAsWeekDay = date.weekday()
    startOfWeek = date.__sub__(datetime.timedelta(todayAsWeekDay))
    endOfWeek = date.__add__(datetime.timedelta(days=6 - todayAsWeekDay))


    startDateArr = [startOfWeek.day, startOfWeek.month, startOfWeek.year]
    endDateArr = [endOfWeek.day, endOfWeek.month, endOfWeek.year]

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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

    # Call the Calendar API
    #calendars = service.calendarList().list().execute()
    #print(calendars)

    #Fetch from Rapla
    entries = RaplaFetch().fetch(startDateArr[0], startDateArr[1], startDateArr[2], settings['rapla_url'], ignoredCourses)
    googlifiedEntries = []

    #Googlify entries
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

        googlifiedEntries.append(event)

    startDateWithGoogleFormat = convertDateTimeToGoogleQueryFormat(startDateArr, "00:00")
    endDateWithGoogleFormat = convertDateTimeToGoogleQueryFormat(endDateArr, "00:00")

    print(startDateWithGoogleFormat, endDateWithGoogleFormat)

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

    #insert the new entries
    for googleEvent in googlifiedEntries:
        #print(googleEvent)
        googleEvent = service.events().insert(calendarId=calendarId, body=googleEvent).execute()

def convertDateTimeToGoogleFormat(date, time):
    dateArr = date.split('.')
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return year + "-" + month + "-" + day + "T" + time + ":00.000"

def convertDateTimeArrToGoogleFormat(dateArr, time):
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return str(year) + "-" + str(month) + "-" + str(day) + "T" + str(time) + ":00.000"

def convertDateTimeToGoogleQueryFormat(dateArr, time):
    day = dateArr[0]
    month = dateArr[1]
    year = dateArr[2]
    return str(year) + "-" + str(month) + "-" + str(day) + "T" + str(time) + ":00+01:00"

if __name__ == '__main__':
    main()