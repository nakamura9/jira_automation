import openpyxl
import csv
import json
import os
import datetime


ISSUE_TYPE_MAP = {
    "Open": ["Open"],
    "Closed": ["Closed", "Pending Deployment"],
    "Testing": ["In QAT","IN UAT","Pending QAT","Pending UAT"],
    "WIP": ["In Code Review","In Progress","Pending Code Review",],
}


def create_issue_table(issues):
    issue = issues[0]
    open_tasks = []
    wip = []
    testing = []
    closed = []
    open_issues = []
    wip_issues = []
    testing_issues = []
    closed_issues = []

    for issue in issues:
        if str(issue.fields.status) in ISSUE_TYPE_MAP['Open']:
            open_issues.append(issue)
            open_tasks.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee, issue.fields.reporter,
                    issue.fields.created.split("T")[0], get_rag_status(issue)
                ]
            )
        elif str(issue.fields.status) in ISSUE_TYPE_MAP['Closed']:
            closed_issues.append(issue)
            closed.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee, human_readable_time(issue.fields.timeoriginalestimate),
                    human_readable_time(issue.fields.timespent), issue.fields.created.split("T")[0], issue.fields.duedate,
                    get_rag_status(issue)
                ]
            )
        elif str(issue.fields.status) in ISSUE_TYPE_MAP['WIP']:
            wip_issues.append(issue)
            wip.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.status.name, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee,
                    human_readable_time(issue.fields.timeoriginalestimate), human_readable_time(issue.fields.timespent),
                    issue.fields.created.split("T")[0], (issue.fields.duedate or ""), get_rag_status(issue)
                ]
            )
        elif str(issue.fields.status) in ISSUE_TYPE_MAP['Testing']:
            testing_issues.append(issue)
            testing.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.status.name, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee,
                    human_readable_time(issue.fields.timeoriginalestimate), human_readable_time(issue.fields.timespent),
                    issue.fields.created.split("T")[0], (issue.fields.duedate or ""), get_rag_status(issue)
                ]
            )

    issue_table = [
        ["Summary", "Issue Type", "Project Name", "Priority", "Assignee", "Estimated Time", "Time Spent", "Created", "Due Date", "RAG Status"],
        *closed,
        [],
        ["Summary", "Issue Type", "Status", "Project Name", "Priority","Assignee", "Estimated Time", "Time Spent", "Created", "Due Date", "RAG Status"],
        *wip,
        [],
        ["Summary", "Issue Type", "Status", "Project Name", "Priority","Assignee", "Estimated Time", "Time Spent", "Created", "Due Date", "RAG Status"],
        *testing,
        [],
        ["Summary", "Issue Type", "Project Name", "Priority","Assignee", "Reporter", "Created", "RAG Status"],
        *open_tasks
    ]

    write_to_excel_file(issue_table)
    return open_issues, wip_issues, testing_issues, closed_issues


def write_to_excel_file(contents):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row_id, row in enumerate(contents, start=1):
        for col_id, col in enumerate(row, start=1):
            ws.cell(row=row_id, column=col_id).value = str(col)

    wb.save('docs/out.xlsx')

def create_issue_summary(issues, name):
    '''
    groups tasks by projects, 
    makes a sentence of all summaries, 
    and returns a count of the tasks and saves to a text file
    '''
    output = ""
    issue_count = len(issues)
    output += f"Total Issues: {issue_count}\n"
    project_map = {}
    for issue in issues:
        project_name = str(issue.fields.project)
        issue_list = project_map.get(project_name, [])
        issue_list.append(issue)
        project_map[project_name] = issue_list

    for project, issues in project_map.items():
        project_issue_count = len(issues)
        output += f"{project} {project_issue_count} Tasks:\n"
        output += "=============\n"
        for issue in issues:
            output += issue.fields.summary[:80] + "\n"

    with open(f"docs/{name}.txt", "w") as f:
        f.writelines(output)


def clean():
    for dirname, _, files in os.walk('docs/'):
        for filename in files:
            os.remove(f"{dirname}/{filename}")


def get_rag_status(issue):
    '''
    Red amber green classification
    Determined by:
    1. Client importance
    2. Time spent in excess of estimate
    3. Age of ticket in days
    4. Days overdue

    Each score from 1 - 10
    Take the scores on each item and add them
    Classifications:
    0-15 Green
    16-30 Amber
    31-40 Red
    '''

    if issue.fields.status in ["Closed", "Pending Deployment"]:
        return "Green"

    if issue.fields.priority in ["Low", "Very Low"]:
        return "Green"

    client_importance = {
        "Polaris Farming": 10,
        "ERP-JMANN": 10,
        "Alpha Packaging": 10,
        "Earthen Fire": 7,
        "Kurima Machinery and Tools": 3,
        "TMS-ZERODEGREE": 3,
        "MMS": 5,
        "WeProcure": 7
    }
    client_score = client_importance.get(issue.fields.project.name, 0)
    created = datetime.datetime.strptime(issue.fields.created.split("T")[0], '%Y-%m-%d')
    due = datetime.datetime.strptime(issue.fields.duedate, '%Y-%m-%d') if issue.fields.duedate else None
    today = datetime.datetime.now()
    overdue_score = 0
    if due:
        overdue = (due - today).days
        overdue_score = overdue if overdue < 10 else 10

    age_of_ticket = (today - created).days

    age_score = (age_of_ticket // 3) if age_of_ticket < 30 else 10
    # increase weight of score
    age_score *= 2

    # time overspent that exceeds the estimated time.
    time_spent_score = 0 
    if issue.fields.timeoriginalestimate and issue.fields.timespent:
        time_spent_score = ((issue.fields.timespent / issue.fields.timeoriginalestimate) - 1) * 10
        if time_spent_score > 10:
            time_spent_score = 10

    total_score = client_score + overdue_score + age_score + time_spent_score

    if total_score < 10:
        return "Green"
    if total_score < 21:
        return "Amber"
    return "Red"


def human_readable_time(seconds):
    if not seconds:
        return ""
    days = seconds // (3600 * 24)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"
