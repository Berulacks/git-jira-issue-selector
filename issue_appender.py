from jira_issue import JiraConnector
import yaml
import blessed

class IssueAppender:

    QUERY_TEXT = "Search for issue: "

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
        for i in range(self.NUM_RESULTS+2):
            print("")

        query = ""

        self.update_search_query(term,query)
        self.update_results(term,query)

        print(term.move(term.height - self.NUM_RESULTS - 3,len(self.QUERY_TEXT+query))+"",end='',flush=True)

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
                    exit()

                if key == "KEY_DELETE":
                    query = query[:-1]

                print(term.move(term.height - self.NUM_RESULTS - 3,len(self.QUERY_TEXT+query)),end='',flush=True)

                self.update_search_query(term,query)
                self.update_results(term,query)


    def update_search_query(self,term,query=""):
        # Have to do -2 here since this starts at 1
        with term.location(x=0,y=term.height - self.NUM_RESULTS - 3):
            print(term.clear_eol() + self.QUERY_TEXT + query, end='')

    def update_results(self,term,query=""):
        with term.location(x=0,y=term.height - self.NUM_RESULTS - 1):
            for query in self.issues[:-1]:
                term.clear_eol()
                print(term.clear_eol()+query)

            term.clear_eol()
            print(term.clear_eol+query, end='')

    def get_responses(self):
        response = self.connector.search_issues("PNAME","<YOUR_NAME_HERE>")
        issues = self.connector.build_issues_array(response)

        #print(issues)

        return issues

    def apply_config(self,config):
        self.NUM_RESULTS = 7

    def load_config(self,path):

        fd = open(path, 'r')
        global_config = yaml.load( fd )
        fd.close()

        return global_config



if __name__ == '__main__':
    ins = IssueAppender()
