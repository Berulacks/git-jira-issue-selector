import requests
import json
import curses
import blessed
from blessed import Terminal

class JiraConnector:

    API_URL = "https://<COMPANY_NAME>.atlassian.net"
    SEARCH_URL = "https://<COMPANY_NAME>.atlassian.net/rest/api/2/search"

    def __init__(self,api_key):
        self.api_key = api_key

    def make_request(self,url,headers=None,payload=None):
        #if payload is None:
        #    response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key))
        #else:
        #    response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key), params=payload)

        #TODO just use **kwargs instead of headers and payload?
        response = requests.get(url, auth=("<YOUR_ATLASSIAN_EMAIL>",self.api_key), params=payload)
        json_data = json.loads(response.text)

        #print( "Raw data: {0}\n".format(json_data["issues"]) )

        for issue in json_data["issues"]:
            fields = issue["fields"]
            key = issue["key"]
            print("[{0}] {1} {2} - {3}\n".format(key,fields["summary"],fields["fixVersions"][0]["name"],fields["assignee"]["displayName"]))

        return json_data


jc = JiraConnector("<YOUR_API_KEY_HERE>")
response = jc.make_request(jc.SEARCH_URL,{"Accept":"application/json"},{"jql":"project = PNAME AND assignee = '<YOUR_NAME_HERE>'", "fields":["summary","status","fixVersions","assignee"]})
#print(jc.make_request(jc.SEARCH_URL,{"Accept":"application/json"},{"jql":"project = PNAME AND assignee = '<YOUR_NAME_HERE>'", "fields":["*all"]}))
for x in range(5):
    print("")


term = Terminal()
with term.location(0, term.height - 1):
        print('This is' + term.underline('underlined') + '!')

key = term.inkey()
print("You typed: {0}".format(key))
