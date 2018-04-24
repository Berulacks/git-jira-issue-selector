from jira_issue import JiraConnector
import yaml
import blessed

class IssueAppender:

    def __init__(self,config="jira.conf"):

        config = self.load_config(config)
        self.connector = JiraConnector(config)

        self.issues = self.get_responses()

        self.start_ui()
        

    def start_ui(self):
        #I FEEL BLESSED
        NUM_RESULTS = 7

        term = blessed.Terminal()
        term.move_y(50)

        #with term.location(0, term.height - 1):
         #       print('This is ' + term.underline('underlined') + '!')

        while True:
            with term.cbreak():
                key = term.inkey()
                if key.is_sequence:
                    print("You typed: {0}".format(key.name))
                else:

                    print("You typed: {0}".format(key))

                if key == "a":
                    exit()

    def get_responses(self):
        response = self.connector.search_issues("PNAME","<YOUR_NAME_HERE>")
        issues = self.connector.build_issues_array(response)

        print(issues)

        return issues

    def load_config(self,path):

        fd = open(path, 'r')
        global_config = yaml.load( fd )
        fd.close()

        return global_config



if __name__ == '__main__':
    ins = IssueAppender()
