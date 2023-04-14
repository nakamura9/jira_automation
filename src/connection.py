from jira import JIRA
import json


def make_connection():
    settings = {}
    with open('conf/settings.json', 'r') as f:
        settings = json.load(f)

    conn = JIRA(
        server=settings['server'],
        basic_auth=(settings['user'], settings['token'])
        )

    return conn
