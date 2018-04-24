import requests
import json
import yaml
import blessed
from blessed import Terminal

class JiraConnector:

    API_URL = "https://<COMPANY_NAME>.atlassian.net"
    SEARCH_URL = "https://<COMPANY_NAME>.atlassian.net/rest/api/2/search"

    def __init__(self,config="jira.conf"):

        config = self.load_config(config)
        self.apply_config(config)
        #self.apply_cli_params(params)


    def apply_config(self,config):
        self.api_key = config["Jira"]["Api Key"]

    def load_config(self,path):

        fd = open(path, 'r')
        global_config = yaml.load( fd )
        fd.close()

        return global_config

    def search_issues(self,project,assignee=None,fields=None):
        if fields is not None:
            fields = ["summary","status","fixVersions","assignee"]

        jql = "project = {0}".format(project)

        if assignee is not None:
            jql += " AND assignee = '{0}'".format(assignee)

        headers = {"Accept":"application/json"}

        url = self.SEARCH_URL

        payload = { "jql":jql, "fields":fields }

        return self.make_request(url, headers, payload)


    def make_request(self,url,headers=None,payload=None):
        #if payload is None:
        #    response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key))
        #else:
        #    response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key), params=payload)

        #TODO just use **kwargs instead of headers and payload?
        response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key), params=payload)
        json_data = json.loads(response.text)

        #print( "Raw data: {0}\n".format(json_data["issues"]) )

        return json_data

jc = JiraConnector()
response = jc.search_issues("PNAME","<YOUR_NAME_HERE>")

for issue in response["issues"]:
    fields = issue["fields"]
    key = issue["key"]
    print("[{0}] {1} {2} - {3}".format(key,fields["summary"],fields["fixVersions"][0]["name"],fields["assignee"]["displayName"]))

#print(jc.make_request(jc.SEARCH_URL,{"Accept":"application/json"},{"jql":"project = PNAME AND assignee = '<YOUR_NAME_HERE>'", "fields":["*all"]}))
for x in range(5):
    print("")


term = Terminal()
with term.location(0, term.height - 1):
        print('This is' + term.underline('underlined') + '!')

key = term.inkey()
print("You typed: {0}".format(key))
