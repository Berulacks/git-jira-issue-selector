import requests
import json
import yaml
import blessed
from blessed import Terminal

class JiraConnector:

    API_URL = "https://<COMPANY_NAME>.atlassian.net"
    SEARCH_URL = "https://<COMPANY_NAME>.atlassian.net/rest/api/2/search"

    def __init__(self,config):

        self.apply_config(config)
        #self.apply_cli_params(params)

    def apply_config(self,config):
        self.api_key = config["Jira"]["Api Key"]

    # Converts a GET Json response dict to a list of searchable strings
    def build_issues_array(self,response):
        list = []

        for issue in response["issues"]:
            fields = issue["fields"]
            key = issue["key"]
            list.append("[{0}] {1} {2} - {3}".format(key,fields["summary"],fields["fixVersions"][0]["name"],fields["assignee"]["displayName"]))

        return list
        
    #Wrapper around make_request to search for an issue and filter according to user
    def search_issues(self,project,assignee=None,fields=None):

        if fields is not None:
            fields = ["summary","status","fixVersions","assignee"]

        jql = "project = {0}".format(project)

        if assignee is not None:
            jql += " AND assignee = '{0}'".format(assignee)

        jql += " AND resolution = unresolved"

        headers = {"Accept":"application/json"}

        url = self.SEARCH_URL

        payload = { "jql":jql, "fields":fields }

        return self.make_request(url, headers, payload)


    def make_request(self,url,headers=None,payload=None):

        #TODO just use **kwargs instead of headers and payload?
        response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key), params=payload)
        json_data = json.loads(response.text)

        #print( "Raw data: {0}\n".format(json_data["issues"]) )

        return json_data
