from connection import make_connection
import json
from report import (
    create_issue_summary, create_issue_table, clean,
    create_developer_table, write_to_excel_file, human_readable_time
)
import sys
import datetime


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


def developer_productivity():
    # measure
    # the total number of tickets by developer
    # total number of tickets by project, by developer
    # time spent per project per developer
    # cumulative time logged per developer
    # mean time between creation and completion of tickets, per project

    settings = {}
    with open('conf/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)

    active = settings.get('active_projects', [])
    active_string = "', '".join(active)
    print(active_string)
    jira = make_connection()
    issues = []
    start = 0
    while start  < 5000:
        issues_page = jira.search_issues(f"project in ('{active_string}')", startAt=start) 
        print(len(issues_page))
        if len(issues_page) == 0:
            break
        else:
            issues.extend(issues_page)
        start += 50

    print(len(issues))
    assignee_map = {}
    project_map = {}

    content = []

    def get_total_tickets_per_dev():
        content.append(["Total Tickets Per Developer"])
        content.append(["Developer", "# of Tickets"])
        for k, v in assignee_map.items():
            content.append([k, len(v)])

        content.append([])

    def get_total_time_per_dev():
        content.append(["Total Time Per Developer"])
        content.append(["Developer", "# of Tickets"])
        for k, v in assignee_map.items():
            content.append([k, human_readable_time(sum(i.fields.timespent or 0 for i in v))])

        content.append([])

    def get_total_tickets_per_dev_per_project():
        content.append(["Total Tickets Per Project Per Developer"])
        content.append(["Project", "Developer", "# of Tickets"])
        for k, tickets in project_map.items():
            content.append([k])
            project_assignee_map = {}
            for ticket in tickets:
                project_assignee_map[ticket.fields.assignee] = project_assignee_map.get(ticket.fields.assignee, 0) + 1

            for assignee, count in project_assignee_map.items():
                content.append(["", assignee, count])

        content.append([])

    def get_time_per_project_per_dev():
        content.append(["Time Spent Per Project Per Dev"])
        content.append(["Project", "Developer", "Time Spent"])
        for k, tickets in project_map.items():
            content.append([k])
            project_assignee_map = {}
            for ticket in tickets:
                project_assignee_map[ticket.fields.assignee] = project_assignee_map.get(ticket.fields.assignee, 0) + (ticket.fields.timespent or 0)

            for assignee, timespent in project_assignee_map.items():
                content.append(["", assignee, human_readable_time(timespent)])

        content.append([])

    def get_ticket_time_to_complete(iss):
        def get_date(val):
            return datetime.datetime.strptime(val.split("T")[0], '%Y-%m-%d')
        total_time = get_date(iss.fields.updated) - get_date(iss.fields.created)
        
        return total_time

    def mean_time_to_complete():
        content.append(["Developer Mean Time To Completion"])
        content.append(["Developer", "Mean Time To Complete"])
        cumulative_time_map = {}
        count_map = {}
        for iss in issues:
            if str(iss.fields.status) != "Closed":
                continue
            assignee = str(iss.fields.assignee)
            cumulative_time_map[assignee] = cumulative_time_map.get(assignee, 0) + get_ticket_time_to_complete(iss).total_seconds()
            count_map[assignee] = count_map.get(assignee, 0) + 1

        for assignee, total_time in cumulative_time_map.items():
            content.append([assignee, human_readable_time(total_time / count_map[assignee])])

        content.append([])

    for issue in issues:
        assignee_map.setdefault(issue.fields.assignee, []).append(issue)
        project_map.setdefault(issue.fields.project, []).append(issue)

    get_total_tickets_per_dev()
    get_total_time_per_dev()
    get_total_tickets_per_dev_per_project()
    get_time_per_project_per_dev()
    mean_time_to_complete()

    write_to_excel_file(content, "all_developers")


if __name__ == "__main__":
    if "prod" in sys.argv:
        developer_productivity()
    elif "dev" in sys.argv:
        get_dev_tickets()
    else:
        main()
