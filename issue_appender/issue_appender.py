from issue_appender.jira_issue import JiraConnector

from fuzzywuzzy import process
import yaml
import blessed
import operator
import argparse, code
import time

import sys,os,pathlib,shutil

# For saving cache info on a per-repo basis
import git


class IssueAppender:

    # Default names for configuration
    CONFIG_DIR_NAME = "jira_issue_appender"
    CONFIG_FILE_NAME = "jira.conf"

    QUERY_TEXT = "Search for issue: "
    # By default print 5 issues at a time
    NUM_RESULTS = 7
    # By default refresh the issues every n minutes
    refresh_interval = 1440

    def __init__(self):

        # Parse command line arguments
        # (also loads the configuration file)
        self.parse_args()

        self.connector = JiraConnector(self.config)

        self.issues = self.get_responses()
        self.sorted_issues = self.issues.copy()

        selected_issue = self.select_issue()

        if selected_issue is not None:
            self.save_issue(selected_issue)
            self.write_to_cache(self.cache_file_path)
            self.selected_issue = selected_issue

        term = blessed.Terminal()
        print(term.clear_eos()+"")

    def save_issue(self,issue_to_save):

        if self.dry_run:
            return

        file_path = self.ISSUE_FILE
        issue_key = issue_to_save.split(" ")[0]

        with open(file_path,"w+") as issue_file:
            issue_file.write(issue_key)

    def select_issue(self):
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
                    return self.sorted_issues[0]

                if key == "KEY_ESCAPE":
                    return None

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
        num_issues = self.results_to_show()

        max_index = -1 if num_issues > len(issues) else num_issues

        if len(query) > 0:
            # Perform the sort
            scored_results = process.extract(query,issues,limit=len(issues) )
            #print(scored_results)
            #term.inkey()

            # Sort the results!
            scored_results = sorted(scored_results, key=operator.itemgetter(1), reverse=True)
            # Copy the first part of the tuple into issues (scored_results is in [(value,score),(...)] form
            issues = [ result[0] for result in scored_results ]
            

        # Print the issues
        with term.location(x=0,y=term.height - num_issues - 1):
            for query in issues[:max_index-1]:
                term.clear_eol()
                print(term.clear_eol()+query)

            # Print the LAST item of the list without the trailing newline, important to preserve our UI
            term.clear_eol()
            print(term.clear_eol+issues[max_index-1], end='')

        # Update the global sorted list
        self.sorted_issues = issues.copy()

    def is_cache_expired(self):
        if self.time_stamp is not None:
            current_time = time.time()
            # The time, in seconds, between now and when the cache was updated
            diff = current_time-self.time_stamp

            # Convert to minutes
            diff /= 60

            #print("Diff: {}".format(diff))
            #exit()

            return diff > self.refresh_interval

        return False

    def refresh_responses_from_net(self):
            print("Refreshing responses from network...",end="",flush=True)
            response = self.connector.search_issues(self.project_key,self.assignee_name,self.issue_resolution)
            issues = self.connector.build_issues_array(response)
            return issues

    def get_responses(self):

        if self.update_on_start or self.no_cache:
            issues = self.refresh_responses_from_net()
            #print(issues)
        else:
            issues = self.read_from_cache(self.cache_file_path)
            if issues == None or self.is_cache_expired():
                issues = self.refresh_responses_from_net()
                # Shitty to do this here, but write to cache does need it
                self.sorted_issues = issues
                # Hey, our cache exists at this point, might as well keep it up to date
                self.write_to_cache(self.cache_file_path)
            
        return issues

    def apply_config(self,config):

        self.NUM_RESULTS = 7

        if "Main" in config and "Max Responses" in config["Main"]:
            if "Max Responses" in config["Main"]:
                self.NUM_RESULTS = config["Main"]["Max Responses"]
            if "Cache File" in config["Main"]:
                self.cache_file_path = config["Main"]["Cache File"]
            if "Refresh Interval" in config["Main"]:
                self.refresh_interval = config["Main"]["Refresh Interval"]

        if "Filter" in config["Jira"]:
            self.assignee_name = config["Jira"]["Filter"].get("Assignee")
            self.project_key = config["Jira"]["Filter"].get("Project")
            self.issue_resolution = config["Jira"]["Filter"].get("Issue Resolution")

    def write_to_cache(self,path):

        if self.dry_run or self.no_cache:
            return
        
        # In case we don't have the requisite folder structure for our cache
        if not os.path.exists( pathlib.Path( path ).parent ):
            os.makedirs( pathlib.Path(path).parent )

        with open(path,"w+") as cache_file :
            cache_file.write( "{}\n".format( time.time() ) )
            cache_file.writelines('\n'.join(self.sorted_issues.copy()))

    def read_from_cache(self,path):

        issues = []

        if os.path.exists(path):
            with open(path,'r') as cache_file :
                issues = cache_file.readlines()
                #The first line is always the timestamp
                self.time_stamp = int( round( float( issues[0].strip() ) ) )
                # Strip the timestamp from the array
                issues = issues[1:]
                # Strip any newlines
                issues = [ line.strip() for line in issues ]

                return issues
        
        # If we're here something went wrong reading from the cache
        return None

    def load_config(self,path):

        if os.path.exists(path):
            with open(path, 'r') as config_file:
                global_config = yaml.load( config_file )

            return global_config

        # uh oh, no config could be found
        if pathlib.Path(path).parent == self.config_dir():

            # If this is the default config that isn't there, lets create it
            self.init_sys()
            # Ask the user to configure the program
            print("First time setup complete, configuration required. Press any key to continue.".format(path))
            blessed.Terminal().inkey()
            self.edit_file(self.config_dir().joinpath(self.CONFIG_FILE_NAME))

            return self.load_config(self.config_dir().joinpath(self.CONFIG_FILE_NAME))

        print("[ERROR] Could not load config from path {}".format(path))
        exit(1)

    def results_to_show(self):
        return min(self.NUM_RESULTS, len(self.issues))

    def script_dir(self):
        return os.path.dirname(os.path.realpath(__file__))

    def config_dir(self):
        return pathlib.Path.home().joinpath(".config/{}".format(self.CONFIG_DIR_NAME))
    
    def edit_file(self,path,exit=False):
        os.system("$EDITOR {0}".format(path))
        if exit:
            exit(0)

    def get_git_root_dir(self):
        path = os.getcwd()
        
        git_repo = git.Repo(path, search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")

        return os.path.basename(git_root)


    def get_git_branch(self):
        path = os.getcwd()
        
        git_repo = git.Repo(path, search_parent_directories=True)
        git_branch = git_repo.git.branch()

        if "* " in git_branch:
            git_branch = git_branch.split(" ")
            return git_branch[1]

        return git_branch

    def init_sys(self):

        config_path = self.config_dir()

        if not os.path.exists(config_path):
            os.makedirs(config_path)

        config_file_path = config_path.joinpath(self.CONFIG_FILE_NAME)

        if not os.path.exists(config_file_path):
            shutil.copyfile(self.script_dir()+"/../config/{}.example".format(self.CONFIG_FILE_NAME),config_file_path)

    def parse_args(self):

        home = pathlib.Path.home()

        parser = argparse.ArgumentParser(description="A JIRA issue selector for git messages",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-n', '--num-results', type=int, default=5, help='The number of results to show on screen', metavar='num_results_to_show')
        parser.add_argument('-c', '--config-path', default=self.config_dir().joinpath("jira.conf"), help='The relative path to the configuration file.', metavar='path_to_config_file')

        parser.add_argument('-u', '--update-cache', action='store_true', help='Update the issue cache. This happens automatically according to the config (usually), but can be manually controlled from here.')

        parser.add_argument('-e', '--edit-conf', action='store_true', help='Drops the user into an editor to edit their configuration file. The $EDITOR shell variable must be set for this')
        parser.add_argument('-d', '--dry-run', action='store_true', help='Does not save anything to the disk (cache or otherwise)')
        parser.add_argument('-nc', '--no-cache', action='store_true', help='Disables reading and writing to the cache')


        parser.add_argument(dest="issue_file", type=str, help='The selected issue will be written to this file, if passed. Use this to actually receive the output of the program. I recommend using mktemp to generate this file path.', metavar='issue_file_to_write_to')

        args = parser.parse_args()

        config_path = args.config_path
        # TODO: Change this to use the config path, and append the current git branch and repo name to it
        self.cache_file_path = self.config_dir().joinpath( "issues/{0}.{1}.cache".format(self.get_git_root_dir(), self.get_git_branch()) )
        self.ISSUE_FILE = args.issue_file

        self.config = self.load_config(config_path)
        #Configure UI
        self.apply_config(self.config)

        self.update_on_start = args.update_cache
        #DEBUG
        #self.update_on_start = True

        self.dry_run = args.dry_run
        if args.dry_run:
            print("[DRY RUN]")

        self.NUM_RESULTS = args.num_results
        self.no_cache = args.no_cache

        if args.edit_conf:
            self.edit_file(config_path,True)

if __name__ == '__main__':


    ins = IssueAppender()
    print(ins.selected_issue)
