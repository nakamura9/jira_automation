# Jira Automation for Goprime
This project is designed to automate the collection of data for the weekly dev report

## Installation

1. Make a virtual environment and activate it
2. Clone the project from https://github.com/nakamura9a/
3. Install the dependencies using 
```
pip install -r requirements.txt 
```
4. Setup the directory structure by creating the folders docs/ and conf/
5. Create a configuration file, settings.json in the conf_directory
6. Populate it with the following keys:
    - server - the url of the jira server
    - token - the api token for the user
    - user - the email used to sign in to jira
    - active_projects - an array of project keys that are valid for the application

## Running the App
```
python src/main.py
```
The output of the application can be found in the docs/ folder.
It consists of an excel file with all the tasks grouped by closed, wip and open as well as three summarizing text files each named closed, open and wip
