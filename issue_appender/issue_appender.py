from issue_appender.jira_issue import JiraConnector

from fuzzywuzzy import process
import yaml
import blessed
import operator
import argparse, code
import time
import collections

import sys,os,pathlib,shutil

# For saving cache info on a per-repo basis
import git


class IssueAppender:

    # Default names for configuration
    CONFIG_DIR_NAME = "jira_issue_appender"
    GLOBAL_CONFIG_FILE_NAME = "global.conf"

    ISSUES_FOLDER_NAME = "issues"
    LOCAL_CONFIGS_FOLDER_NAME = "configs"
    LOCAL_CONFIGS_PREFIX = "local.conf"

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

        if self.dry_run or len(self.issue_file) < 1:
            return

        file_path = self.issue_file
        issue_key = issue_to_save.split(" ")[0]

        with open(file_path,"w+") as issue_file:
            issue_file.write("{} ".format(issue_key))

    def select_issue(self):
        #I FEEL BLESSED
        term = blessed.Terminal()

        #start_row, start_col = term.get_location()
        #print("Row: {0}, Col: {0}".format(start_row,start_col))

        # Space out the terminal (important)
        for i in range(self.results_to_show() +2):
            print("")

        # Where to start drawing our cursor
        row, col = term.get_location() 
        self.start_location = ( row + -1*(self.results_to_show()+3)  , col )

        query = ""

        self.update_search_query(term,query)
        self.update_results(term,query)

        # Move the cursor to the start (after the query text)
        print(term.move(self.start_location[0],len(self.QUERY_TEXT+query))+"",end='',flush=True)

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
                print(term.move(self.start_location[0],len(self.QUERY_TEXT+query)),end='',flush=True)
                self.update_search_query(term,query)
                self.update_results(term,query)

    def update_search_query(self,term,query=""):
        # Have to do -3 here since the rows start at 1, and because we're appending a whitespace
        with term.location(x=0,y=self.start_location[0]):
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
            

        selected = 0
        issue_number = 0

        # Print the issues
        with term.location(x=0,y=self.start_location[0]+2):
            for query in issues[:max_index-1]:
                term.clear_eol()
                # Print the selected issue as colorized
                if issue_number == selected:
                    print( term.black_on_white(term.clear_eol()+query), end='',flush=True )
                    # Clear the remaining background color after the line is finished printing
                    print( term.clear_eol() + '')
                else:
                    print(term.clear_eol()+query)

                issue_number += 1

            # Print the LAST item of the list without the trailing newline, important to preserve our UI
            term.clear_eol()
            print(term.clear_eol+issues[max_index-1], end='')

        # Update the global sorted list
        self.sorted_issues = issues.copy()

    # TODO: Compare config timestamps to determine if a refresh is needed
    def is_config_different(self):

        current_local_ts = self.current_local_config_ts()
        current_global_ts = self.current_global_config_ts()

        return  current_local_ts != self.local_conf_ts or current_global_ts != self.global_conf_ts

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
            if issues == None or self.is_cache_expired() or self.is_config_different():
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

        current_local_ts = self.current_local_config_ts()
        current_global_ts = self.current_global_config_ts()
        
        # In case we don't have the requisite folder structure for our cache
        if not os.path.exists( pathlib.Path( path ).parent ):
            os.makedirs( pathlib.Path(path).parent )

        with open(path,"w+") as cache_file :
            # CACHE TIMESTAMP
            cache_file.write( "{}\n".format( time.time() ) )
            # LOCAL TIMESTAMP
            cache_file.write( "{}\n".format( current_local_ts ) )
            # GLOBAL TIMESTAMP
            cache_file.write( "{}\n".format( current_global_ts ) )

            cache_file.writelines('\n'.join(self.sorted_issues.copy()))

    def read_from_cache(self,path):

        issues = []

        if os.path.exists(path):
            with open(path,'r') as cache_file :
                issues = cache_file.readlines()

                #The first line is always the timestamp
                self.time_stamp = int( round( float( issues[0].strip() ) ) )
                #The second line is always the local config last modified timestamp
                self.local_conf_ts = int( round( float( issues[1].strip() ) ) )
                #The third line is always the global config last modified timestamp
                self.global_conf_ts = int( round( float( issues[2].strip() ) ) )

                # Strip the timestamp from the array
                issues = issues[3:]
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
        return None

    def add_title_to_file(self,path, line_to_write, drop_original_title=True):
        with open(path, "r") as sources:
            lines = sources.readlines()
        with open(path, "w") as sources:
            sources.write(line_to_write)
            if drop_original_title:
                sources.writelines(lines[1:])
            else:
                sources.writelines(lines)
        

    def configure(self):
        git_root = self.get_git_root_dir()
        git_branch = self.get_git_branch()

        global_config_path = self.config_dir().joinpath(self.GLOBAL_CONFIG_FILE_NAME)
        local_config_path = self.config_dir().joinpath( "{2}/{0}.{1}.{3}".format(git_root, git_branch,self.LOCAL_CONFIGS_FOLDER_NAME,self.LOCAL_CONFIGS_PREFIX) )

        # In case another function needs these
        self.global_config_path = global_config_path
        self.local_config_path = local_config_path

        final_conf = {}

        # Load Global config
        global_conf = self.load_config(global_config_path)
        if global_conf is None:
            # uh oh, no config could be found

            # If this is the default config that isn't there, lets create it
            #self.init_sys()
            self.init_config_system(global_config_path)
            self.add_title_to_file(global_config_path, "# -- Global Configuration File --\n")
            # Ask the user to configure the program
            print("First time setup complete, configuration required. Press any key to continue.")
            blessed.Terminal().inkey()
            self.edit_file(global_config_path,False)
            
            print("Config generated. Please try again. Remember, you can always call `issue_appender -e global` to edit the global config")
            blessed.Terminal().inkey()
            exit(0)

        # Load Local config (copying pasting the same code so that I can print the unique message)
        local_conf = self.load_config(local_config_path)
        if local_conf is None:
            print("First time local setup complete, configuration required. Press any key to continue.")
            #print("Copying from {1} to {0}".format(local_config_path,self.script_dir()+"/../config/{}.example".format(self.LOCAL_CONFIGS_PREFIX)))
            self.init_config_system(local_config_path,self.script_dir()+"/../config/{}.example".format(self.LOCAL_CONFIGS_PREFIX))
            self.add_title_to_file(local_config_path, "# -- Local Configuration file for Project: {0}, Branch: {1} --\n".format(git_root,git_branch))

            blessed.Terminal().inkey()
            self.edit_file(local_config_path,False)

            print("Config generated. Continuing... Remember, you can always call `issue_appender -e local` to edit the local config")
            blessed.Terminal().inkey()

        final_conf = global_conf 
        
        # Load the local conf onto the global
        #print("global conf before local added: {}".format(global_conf))
        final_conf = self.dict_merge(final_conf,local_conf)
        #print ("final conf after merge: {}".format(final_conf))

        self.config = final_conf

        #Configure UI
        self.apply_config(final_conf)

        return final_conf

    def init_config_system(self,path,example_config=None):

        # Make the parent directory (if necessary)
        if not os.path.exists( str(path.parent) ):
            os.makedirs(path.parent)

        # Now the file itself
        if not os.path.exists( str(path) ):
            if example_config is None:
                # Try to guess where the example file lives...
                shutil.copyfile(self.script_dir()+"/../config/{}.example".format(path.name),path)
            else:
                shutil.copyfile(example_config,path)

    def results_to_show(self):
        return min(self.NUM_RESULTS, len(self.issues))

    def script_dir(self):
        return os.path.dirname(os.path.realpath(__file__))

    def local_configs_dir(self):
        return pathlib.Path.home().joinpath(".config/{0}/{1}".format(self.CONFIG_DIR_NAME,self.LOCAL_CONFIGS_FOLDER_NAME))

    def current_local_config_ts(self):
        local_config_path = self.local_config_path

        return os.path.getmtime(local_config_path)

    def current_global_config_ts(self):
        global_config_path = self.global_config_path

        return os.path.getmtime(global_config_path)


    def global_config_path(self):
        return pathlib.Path.home().joinpath(".config/{0}/{1}".format(self.CONFIG_DIR_NAME,self.GLOBAL_CONFIG_FILE_NAME))

    def config_dir(self):
        return pathlib.Path.home().joinpath(".config/{0}".format(self.CONFIG_DIR_NAME))

    
    def edit_file(self,path,exit_after_edit=False):
        os.system("$EDITOR {0}".format(path))
        if exit_after_edit:
            exit(0)

    def get_git_root_dir(self):
        path = os.getcwd()
        
        git_repo = git.Repo(path, search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")

        return os.path.basename(git_root).rstrip()


    def get_git_branch(self):
        path = os.getcwd()
        
        git_repo = git.Repo(path, search_parent_directories=True)
        git_branch = git_repo.git.branch()

        if "* " in git_branch:
            git_branch = git_branch.split(" ")
            return git_branch[1].rstrip()

        return git_branch.rstrip()

    def dict_merge(self,merge_onto, merge_from):
        """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
        updating only top-level keys, dict_merge recurses down into dicts nested
        to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
        ``dct``.

        :param dct: dict onto which the merge is executed
        :param merge_dct: dct merged into dct
        :return: None
        """
        #If either of the values is none, go for the non-null one
        if merge_onto is None:
            return merge_from

        if merge_from is None:
            return merge_onto

        dct = merge_onto
        merge_dct = merge_from

        for k, v in merge_dct.items():
            if ( (k in dct and (isinstance(dct[k], dict) or dct[k] is None))
                    and (isinstance(merge_dct[k], collections.Mapping) or merge_dct[k] is None ) ):
                #print("Performing recurisve merge for key {}".format(k))
                dct[k] = self.dict_merge(dct[k], merge_dct[k])
            else:
                #print("Non recursive merge for key: {}".format(k))
                dct[k] = merge_dct[k]

        return dct

    def parse_args(self):

        home = pathlib.Path.home()

        parser = argparse.ArgumentParser(description="A JIRA issue selector for git messages",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-n', '--num-results', type=int, default=5, help='The number of results to show on screen', metavar='num_results_to_show')
        parser.add_argument('-c', '--extra-config-path', help='An extra config file to load.', metavar='path_to_config_file')

        parser.add_argument('-u', '--update-cache', action='store_true', help='Update the issue cache. This happens automatically according to the config (usually), but can be manually controlled from here.')

        parser.add_argument('-e', '--edit-conf', type=str, default="", help='Edit a configuration file. Valid options are global or local. The $EDITOR shell variable must be set for this', metavar='[global|local]')
        parser.add_argument('-d', '--dry-run', action='store_true', help='Does not save anything to the disk (cache or otherwise)')
        parser.add_argument('-nc', '--no-cache', action='store_true', help='Disables reading and writing to the cache')


        parser.add_argument('-i', '--issue-file', default="", type=str, help='The issue selected by the user will be written to this file, if passed. Use this to actually receive the output of the program. I recommend using mktemp to generate this file path.', metavar='issue_file_to_write_to')

        args = parser.parse_args()

        extra_config_path = None
        if args.extra_config_path is not None:
            extra_config_path = args.extra_config_path

        self.cache_file_path = self.config_dir().joinpath( "{2}/{0}.{1}.cache".format(self.get_git_root_dir(), self.get_git_branch(),self.ISSUES_FOLDER_NAME) )

        self.issue_file = args.issue_file

        #Load the configuration system
        if extra_config_path is not None:
            self.configure(extra_config_path)
        else:
            self.configure()

        self.update_on_start = args.update_cache
        #DEBUG
        #self.update_on_start = True

        self.dry_run = args.dry_run
        if args.dry_run:
            print("[DRY RUN]")

        self.NUM_RESULTS = args.num_results
        self.no_cache = args.no_cache

        if len(args.edit_conf) > 1:
            if args.edit_conf == "global":
                self.edit_file(self.global_config_path,True)
            elif args.edit_conf == "local":
                self.edit_file(self.local_config_path,True)
            else:
                print("[ERROR] Could not find config file for {}, please use global or local".format(args.edit_conf))
                exit(1)

if __name__ == '__main__':


    ins = IssueAppender()
    print(ins.selected_issue)
