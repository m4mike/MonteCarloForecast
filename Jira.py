import re
import requests
import json
import aiohttp
import asyncio
import yaml


class Jira:
    STORYPOINTS = "customfield_10014"
    STORYPOINT_ESTIMATE = "customfield_10029"
    
    def __init__(self):
        with open('secrets.yaml', 'r') as file:
            secrets = yaml.safe_load(file)
        self.API_URL = secrets['API_URL']
        self.TOKEN = secrets['TOKEN']

    def init(self, API_URL, TOKEN):
        self.API_URL = API_URL
        self.TOKEN = TOKEN

    async def getFromAPI(self, path, query_params=None):
        url = self.API_URL + path
        headers = {
            "Authorization": "Basic " + self.TOKEN,
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=query_params) as resp:
                    if resp.status != 200:
                        print(f"Error retrieving data for url {url}: {await resp.text()}")
                        return ""
                    else:
                        return await resp.text()
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return ""



    async def getJQL(self, jql, fields) :
        issues = []
        startAt = 0
        maxResults = 50
        total = None

        while total is None or startAt < total:
            query_params = {
                "jql": jql,
                "fields": fields,
                "startAt": startAt,
                "maxResults": maxResults
            }
            response = await self.getFromAPI("/rest/api/2/search", query_params)
            if response == "":
                break
            data = json.loads(response)
            if total is None:
                total = data["total"]
            issues.extend(data["issues"])
            startAt += maxResults

        return issues