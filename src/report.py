import openpyxl
import csv
import json
import os

ISSUE_TYPE_MAP = {
    "Open": ["Open"],
    "Closed": ["Closed", "Pending Deployment"],
    "WIP": ["In Code Review","In Progress","In QAT","IN UAT","Pending Code Review","Pending QAT","Pending UAT"],
}


def create_issue_table(issues):
    issue = issues[0]
    open_tasks = []
    wip = []
    closed = []
    open_issues = []
    wip_issues = []
    closed_issues = []

    for issue in issues:
        if str(issue.fields.status) in ISSUE_TYPE_MAP['Open']:
            open_issues.append(issue)
            open_tasks.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee, issue.fields.reporter
                ]
            )
        elif str(issue.fields.status) in ISSUE_TYPE_MAP['Closed']:
            closed_issues.append(issue)
            closed.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee
                ]
            )
        else: # WIP
            wip_issues.append(issue)
            wip.append(
                [
                    issue.fields.summary, issue.fields.issuetype, issue.fields.status.name, issue.fields.project.name,
                    issue.fields.priority, issue.fields.assignee, (issue.fields.duedate or "")
                ]
            )

    issue_table = [
        ["Summary", "Issue Type", "Project Name", "Priority", "Assignee"],
        *closed,
        [],
        ["Summary", "Issue Type", "Status", "Project Name", "Priority","Assignee", "Due Date"],
        *wip,
        [],
        ["Summary", "Issue Type", "Project Name", "Priority","Assignee", "Reporter"],
        *open_tasks
    ]

    write_to_excel_file(issue_table)
    return open_issues, wip_issues, closed_issues


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
