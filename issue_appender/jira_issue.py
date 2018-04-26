import requests
import json
import yaml
import blessed
from blessed import Terminal

class JiraConnector:

    def __init__(self,config):

        self.apply_config(config)
        #self.apply_cli_params(params)

    def apply_config(self,config):
        self.user_name = config["Jira"]["Username"]
        self.api_key = config["Jira"]["Api Key"]
        self.search_url = config["Jira"]["Search URL"]

    # Converts a GET Json response dict to a list of searchable strings
    def build_issues_array(self,response):
        list = []

        if "issues" in response:
            for issue in response["issues"]:
                fields = issue["fields"]
                key = issue["key"]

                list.append(self.build_issue_string(issue))
                #if "fixVersions" in fields and len(fields["fixVersions"]) > 0:
                #    list.append("[{0}] {1} {2} - {3}".format(key,fields["summary"],fields["fixVersions"][0]["name"],fields["assignee"]["displayName"]))
                #else:
                #    list.append("[{0}] {1} - {2}".format(key,fields["summary"],fields["assignee"]["displayName"]))


            return list

        print("[ERROR] Response from server did not contain any issues, dumping then crashing.\nResponse:\n{}".format(response))
        exit(1)
        
    def build_issue_string(self,issue):

            fields = issue["fields"]
            key = issue["key"]

            to_return = "[{0}] ".format(key)

            if "summary" in fields:
                to_return += "{} ".format(fields["summary"])
            if "fixVersions" in fields and len(fields["fixVersions"]) > 0:
                to_return += "{} ".format(fields["fixVersions"][0]["name"])
            if "assignee" in fields and fields["assignee"] is not None:
                to_return += "- {}".format(fields["assignee"]["displayName"])

            return to_return

    #Wrapper around make_request to search for an issue and filter according to user
    def search_issues(self,project,assignee=None,resolution=None,fields=None):

        if fields is not None:
            fields = ["summary","status","fixVersions","assignee"]

        jql = "project = {0}".format(project)

        if assignee is not None:
            jql += " AND assignee = '{0}'".format(assignee)

        if resolution is not None:
            jql += " AND resolution = {0}".format(resolution)

        headers = {"Accept":"application/json"}

        url = self.search_url

        payload = { "jql":jql, "fields":fields }

        return self.make_request(url, headers, payload)


    def make_request(self,url,headers=None,payload=None):

        #TODO just use **kwargs instead of headers and payload?
        response = requests.get(url, auth=(self.user_name,self.api_key), params=payload)
        try:
            json_data = json.loads(response.text)
        except:
            print("[ERROR] Could not process response as json, something went wrong. Dumping...\nResponse: {}".format(response.text))
            exit(1)

        #print( "Raw data: {0}\n".format(json_data["issues"]) )

        return json_data
