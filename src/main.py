from connection import make_connection
import json
from report import (
    create_issue_summary, create_issue_table, clean,
    create_developer_table
)
import sys


def main():
    clean()
    settings = {}
    with open('conf/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)

    jira = make_connection()

    active = settings.get('active_projects', [])
    active_string = "', '".join(active)
    issues = jira.search_issues(f"project in ('{active_string}') and updated >= -7d", maxResults=1000)
    open_tasks, wip, testing, closed = create_issue_table(issues)
    create_issue_summary(open_tasks, "open")
    create_issue_summary(wip, "wip")
    create_issue_summary(testing, "testing")
    create_issue_summary(closed, "closed")


def get_dev_tickets():
    print(sys.argv)
    if len(sys.argv) < 3:
        raise Exception("You need to specify a developer to proceed")
    
    developer = sys.argv[2]
    settings = {}
    with open('conf/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)

    active = settings.get('active_projects', [])
    active_string = "', '".join(active)
    jira = make_connection()
    issues = jira.search_issues(f"project in ('{active_string}') and assignee = '{developer}' and status not in (Closed, 'In QAT', 'Pending QAT', 'In UAT', 'Pending UAT', 'Pending Deployment') ", maxResults=1000)
    print(issues)
    create_developer_table(issues, developer)


if __name__ == "__main__":
    if "dev" in sys.argv:
        get_dev_tickets()
    else:
        main()
