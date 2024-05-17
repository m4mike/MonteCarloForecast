import re
import json
from datetime import datetime
import pandas as pd

import numpy as np
import aiohttp
import asyncio
import Jira

#######################################################
# Find all Stories, Tasks , Bugs that were closed in the last x days and lookup up the cycle time for them. (Difference between Done and in Progress)
# To Do : For bugs Lead time is a better metric ( Duration between Done and Created)
# Results are written to issue-duration.csv


JQLProduct = 'status changed to (Done, Closed) DURING (-30d, now()) and project = "Product Group Development" and issuetype in ( Story, Task, Bug,Improvement )'
JQL = "status changed to (Done, Closed) DURING (-60d, now()) and project in (PSLM0036, TDL4044, TH4035, ST4102, RS4103, BPS4105, VLAIOSG)  and issuetype in ( Story, Task, Bug,Improvement )"



#################### MAIN ###################################
async def main():
    print("_______________________________________________________________________________________")
    print("Getting last closed items and updating issue_duration csv, it will opnly add new issues")
    print("_______________________________________________________________________________________")

    rv_jira = Jira.Jira()
    issues = await rv_jira.getJQL(JQL, fields=f"issuetype,key,summary,resolved,{rv_jira.STORYPOINTS}")
    try:
        df = pd.read_csv("issue_duration.csv", sep=";")
        df.set_index('Issue Key', inplace=True)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Done Date", "Issue Key", "Issue Type", "Story Points", "Duration", "Start", "Done", "Summary"])
        df.set_index('Issue Key', inplace=True)
    new_ones=0
    count:int = len(issues)
    i:int = 0
    for issue in issues:
        i+=1
        print(f'Processing {i}/{count} issues...', end='\r')
        issue_key = issue['key']
        if issue_key not in df.index:
            
            issue_type = issue['fields']['issuetype']['name']
            changelog_url = f'/rest/api/2/issue/{issue_key}?expand=changelog'
            changelog_response = json.loads(await rv_jira.getFromAPI(changelog_url))
            changelog = changelog_response['changelog']['histories']

            foundDone = False
            foundStart = False

            # Parse changelog for transitions
            for history in changelog:
                for item in history['items']:
                    if item['field'] == 'status':
                        to_status = item['toString']
                        if to_status == 'Done' or to_status == 'Closed':
                            to_Done = datetime.strptime(history['created'], '%Y-%m-%dT%H:%M:%S.%f%z')
                            foundDone = True
                        if to_status == 'In Progress':
                            to_Start = datetime.strptime(history['created'], '%Y-%m-%dT%H:%M:%S.%f%z')
                            foundStart = True
                            if foundDone:
                                break
                if foundDone and foundStart:
                    break

            # Calculate duration only if both start and done are found
            if foundDone and foundStart:
                new_ones += 1
                duration = (to_Done - to_Start).total_seconds() / 3600 / 24  # Convert duration to days with decimal hours

                points = 0 if issue["fields"][rv_jira.STORYPOINTS] is None else issue["fields"][rv_jira.STORYPOINTS]
                # Append issue data to the DataFrame
                df.loc[issue_key] = {
                    "Done Date": to_Done.strftime('%Y-%m-%d'),
                    "Issue Type": issue_type,
                    "Story Points": points,
                    "Duration": round(duration, 3),
                    "Start": to_Start.strftime('%Y-%m-%dT%H:%M:%S'),
                    "Done": to_Done.strftime('%Y-%m-%dT%H:%M:%S'),
                    "Summary": issue["fields"]["summary"]
                }
                print(f'{to_Done.strftime('%Y-%m-%d')}: {issue_type} - {issue_key} - {points} - {round(duration, 3)} - {issue["fields"]["summary"]}')

    # possibly you want to remove some rows that are outliers
    to_remove = ["PSLM0036-200", "	PSLM0036-22", "TDL4044-200","BPS4105-126"]
    df.drop(index=to_remove, inplace=True, errors='ignore')

    
    # Save the updated DataFrame to a CSV file with specified date format
    df.sort_values(by='Done Date', inplace=True)
    df.reset_index().to_csv("issue_duration.csv", index=False, sep=";")
    print(f"Added {new_ones} new issues to issue_duration.csv")
    # Saving the issues to excel 
    # Calculate mean duration for Bug, Task, and Story items
    mean_bug_duration = df[df['Issue Type'] == 'Bug']['Duration'].mean()
    mean_task_duration = df[df['Issue Type'] == 'Task']['Duration'].mean()
    mean_story_duration = df[df['Issue Type'] == 'Story']['Duration'].mean()

    print(f"Mean Bug Duration: {mean_bug_duration:.3f} days" )
    print(f"Mean Task Duration: {mean_task_duration:.3f} days" )
    print(f"Mean Story Duration: {mean_story_duration:.3f} days" )
   
   
    pivot_table = df.pivot_table(index='Done Date', columns='Issue Type', values='Story Points', aggfunc='sum', fill_value=0)
    pivot_table2 = df.pivot_table(index='Done Date', columns='Issue Type', values='Story Points', aggfunc='count', fill_value=0)
    try:
        pivot_table.drop(columns=['Bug'], inplace=True)
    except KeyError:
        pass
    pivot_table['Total Points'] = pivot_table['Story'] + pivot_table['Task']
    columns_to_sum = [col for col in ['Story', 'Task', 'Improvement'] if col in pivot_table2.columns]
    pivot_table['Tickets'] = pivot_table2[columns_to_sum].sum(axis=1)
    pivot_table.rename(columns={'Story': 'Story Points', 'Task': 'Task Points','Improvement': 'Improvement Points'}, inplace=True)
    
    pivot_table = pivot_table.join(pivot_table2)
    
    pivot_table.to_csv("issues_by_date_count.csv", sep=";")

    
    last_record_date = pd.to_datetime(pivot_table.index[-1]) 
    historycounts=[30,60,90]
    for daysago in historycounts: # Get the last record's Done Date
        days_ago = last_record_date - pd.Timedelta(days=daysago)  # Calculate 30 days before the last record's Done Date
        recent_df = pivot_table.loc[pivot_table.index > days_ago.strftime('%Y-%m-%d')]  # Select rows within the last 30 days
        print(f"Selected {len(recent_df)} records from the last {daysago} days until {days_ago.strftime('%Y-%m-%d')}.")
        recent_df = recent_df[['Total Points','Tickets']]
        recent_df.rename(columns={'Total Points': 'Points'},inplace=True)
        recent_df.to_csv(f"issue_throughput_{daysago}d.csv", sep=";")
    

    
    # Resample pivot_table to count all columns based on a weekly/monthly sampling of the "Done Date"
    pivot_table['Done Date'] = pd.to_datetime(pivot_table.index)
    resampled = pivot_table.resample('W', on='Done Date').sum()
    resampled.to_csv("issues_by_date_weekly.csv", sep=";")
    resampled = pivot_table.resample('2W', on='Done Date').sum()
    resampled.to_csv("issues_by_date_biweekly.csv", sep=";")
    resampled = pivot_table.resample('ME', on='Done Date').sum()
    resampled.to_csv("issues_by_date_monthly.csv", sep=";")
   

if __name__ == "__main__":
    asyncio.run(main())
