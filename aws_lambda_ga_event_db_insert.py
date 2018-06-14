"""
Analytics Reporting API V4 to retrieve event click data and write to a postgreSQL database.
"""
import datetime
import psycopg2
import argparse
import logging

import credentials

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2


def lambda_handler(event, context):
    # Analytics credential config
    SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
    KEY_FILE_LOCATION = 'key_file_location.json'
    VIEW_ID = credentials.analytics['view_id']
    print('Loaded credentials')

    # Postgres connection config
    HOST = credentials.db['host']
    PORT = credentials.db['port']
    DB_NAME = credentials.db['db_name']
    USER_NAME = credentials.db['user_name']
    PASSWORD = credentials.db['password']
    print('Loaded db credentials')

    # Connection to Postgres db
    conn_string = f"host={HOST} port={PORT} dbname={DB_NAME} user={USER_NAME} password={PASSWORD}"
    print('connection string built')
    conn = psycopg2.connect(conn_string)
    print('connected to postgres')

    # Open a cursor
    cursor = conn.cursor()
    print('opened a cursor')

    def initialize_analyticsreporting():
      """Initializes an analyticsreporting service object.

      Returns:
        analytics an authorized analytics reporting service object.
      """
      print("Intializing analytics")

      credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)

      logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

      # Build the service object.
      analytics = build('analyticsreporting', 'v4', credentials=credentials)
      print("Analytics initialized")
      return analytics


    def get_analytics(analytics):
      print("Getting analytics data")
      # Use the Analytics Service Object to query the Analytics Reporting API V4.
      return analytics.reports().batchGet(
      body = {
          'reportRequests': [{
            'viewId': VIEW_ID,
            'dateRanges': [{
                'startDate':  '10daysAgo', #'10daysAgo',  #'2017-01-01'
                'endDate': 'yesterday'  #'today'
            }],
            'metrics': [{
                'expression': 'ga:totalEvents'
            }],
            'dimensions': [{
                'name': 'ga:date'
            }, {
                'name': 'ga:pageTitle'
            }, {
                'name': 'ga:medium'
            }, {
                'name': 'ga:source'
            }, {
                'name': 'ga:pagePath'
            }],

            "dimensionFilterClauses": [{

                "operator": "AND",
                "filters": [{
                    "dimensionName": "ga:pagePath",
                    "operator": "PARTIAL",
                    "expressions": [
                        "test/test"
                    ]
                }, {
                    "dimensionName": "ga:eventAction",
                    "operator": "EXACT",
                    "expressions": [
                        "eventAction"
                    ]
                }]
            }],
        }]
    }
      ).execute()

    def write_to_db(response):
        print("Writing to db")
        if response.get('reports', []):
            cursor.execute("""DELETE from public.event_reg_clicks
                              WHERE date > current_date - interval '11 day'""")

            for report in response.get('reports', []):
                rows = report.get('data', {}).get('rows', [])

                for row in rows:
                    dimensions = row.get('dimensions', [])
                    dimensions[0] = datetime.datetime.strptime(dimensions[0], '%Y%m%d')
                    dimensions[1] = dimensions[1].split(' - ')[0]

                    if len(dimensions[4]) > 100:
                        dimensions[4] = dimensions[4].split('#')[0]

                    else:
                        dimensions[4] = dimensions[4].replace('/test/test/', '')

                    metrics = row.get('metrics', [])

                    for metric in metrics:
                        metrics = dimensions + metric.get('values', [])

                        cursor.execute("""INSERT INTO public.event_reg_clicks (date, event, medium, source, page, click)
                                          VALUES(%s, %s, %s, %s, %s, %s)""", (metrics[0], metrics[1], metrics[2], metrics[3],
                                          metrics[4], metrics[5]))


    def close_db():
        # Close cursor and db connection
        cursor.close()
        conn.close()


    def main():
        analytics = initialize_analyticsreporting()
        response = get_analytics(analytics)
        write_to_db(response)
        conn.commit() # commit to db
        close_db()

    main()
