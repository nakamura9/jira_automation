from connection import make_connection
import json
from report import create_issue_summary, create_issue_table, clean


def main():
    clean()
    settings = {}
    with open('conf/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)

    jira = make_connection()

    active = settings.get('active_projects', [])
    active_string = "', '".join(active)
    issues = jira.search_issues(f"project in ('{active_string}') and updated >= -7d", maxResults=1000)
    open_tasks, wip, closed = create_issue_table(issues)
    create_issue_summary(open_tasks, "open")
    create_issue_summary(wip, "wip")
    create_issue_summary(closed, "closed")


if __name__ == "__main__":
    main()
