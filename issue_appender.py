from jira_issue import JiraConnector
from fuzzywuzzy import process
import yaml
import blessed
import operator


class IssueAppender:

    QUERY_TEXT = "Search for issue: "
    # By default print 5 issues at a time
    NUM_RESULTS = 7

    def __init__(self,config="jira.conf"):

        config = self.load_config(config)

        #Configure UI and JiraConnector
        self.apply_config(config)
        self.connector = JiraConnector(config)

        self.issues = self.get_responses()

        self.start_ui()
        

    def start_ui(self):
        #I FEEL BLESSED

        term = blessed.Terminal()

        #start_row, start_col = term.get_location()
        #print("Row: {0}, Col: {0}".format(start_row,start_col))

        # Space out the terminal (important)
        for i in range(self.results_to_show() +2):
            print("")

        query = ""

        self.update_search_query(term,query)
        self.update_results(term,query)

        # Move the cursor to the start (after the query text)
        print(term.move(term.height - self.results_to_show() - 3,len(self.QUERY_TEXT+query))+"",end='',flush=True)

        while True:
            with term.cbreak():
                key = term.inkey()
                if key.is_sequence:
                    # Are we a special like KEY_UP?
                    key = key.name
                else:
                    # ...or just a normal letter?
                    query += key

                if key == "KEY_ENTER":
                    break

                if key == "KEY_DELETE":
                    query = query[:-1]

                # Update the cursory position, query results, and query text
                print(term.move(term.height - self.results_to_show() - 3,len(self.QUERY_TEXT+query)),end='',flush=True)
                self.update_search_query(term,query)
                self.update_results(term,query)


    def update_search_query(self,term,query=""):
        # Have to do -3 here since the rows start at 1, and because we're appending a whitespace
        with term.location(x=0,y=term.height - self.results_to_show() - 3):
            print(term.clear_eol() + self.QUERY_TEXT + query, end='')

    def update_results(self,term,query=""):

        issues = self.issues

        if len(query) > 0:
            # Perform the sort
            scored_results = process.extract(query,issues,limit=self.results_to_show() )
            #print(scored_results)
            #term.inkey()

            # Sort the results!
            scored_results = sorted(scored_results, key=operator.itemgetter(1), reverse=True)
            # Copy the first part of the tuple into issues (scored_results is in [(value,score),(...)] form
            issues = [ result[0] for result in scored_results ]
            

        # Print the issues
        with term.location(x=0,y=term.height - self.results_to_show() - 1):
            for query in issues[:-1]:
                term.clear_eol()
                print(term.clear_eol()+query)

            # Print the LAST item of the list without the trailing newline, important to preserve our UI
            term.clear_eol()
            print(term.clear_eol+issues[-1], end='')

        # Update the global list?
        self.issues = issues

    def get_responses(self):
        response = self.connector.search_issues(self.project_key,self.assignee_name)
        issues = self.connector.build_issues_array(response)

        #print(issues)

        return issues

    def apply_config(self,config):

        self.NUM_RESULTS = 7

        if "Main" in config and "Max Responses" in config["Main"]:
            self.NUM_RESULTS = config["Main"]["Max Responses"]

        self.assignee_name = config["Jira"]["Assignee"]
        self.project_key = config["Jira"]["Project"]

    def load_config(self,path):

        fd = open(path, 'r')
        global_config = yaml.load( fd )
        fd.close()

        return global_config
    def results_to_show(self):
        return min(self.NUM_RESULTS, len(self.issues))



if __name__ == '__main__':
    ins = IssueAppender()
