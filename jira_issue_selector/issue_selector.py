from jira_issue_selector.jira_issue import JiraConnector
from jira_issue_selector.ui.selector import Selector

from fuzzywuzzy import process
from pathlib import Path
import yaml
import blessed
import operator
import argparse, code
import time
import collections

import sys,os,shutil

# For saving cache info on a per-repo basis
import git


class IssueSelector:

    # We're going to pass this when we leave, unless someone changes it
    normal_exit_code = 0

    # We're exiting because the user edited their config
    EXIT_CODE_CONFIG = 78
    # We're exiting because the user canceled!
    EXIT_CODE_CANCEL = 75
    # We're exiting normally, but the user wants
    # to use `git commit -m` (a.k.a. no interactive commit
    # message prompt)
    EXIT_CODE_WITH_MESSAGE = 60

    # Default names for configuration
    CONFIG_DIR_NAME = "jira_issue_selector"
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

        result_tuple = Selector.select_item(self.sorted_issues,self.NUM_RESULTS,self.QUERY_TEXT)

        term = blessed.Terminal()
        # User cancelled the select
        if result_tuple is None:
            print(term.clear_eos()+"")
            exit(self.EXIT_CODE_CANCEL)

        selected_issue = result_tuple[0]
        self.sorted_issues = result_tuple[1]


        if selected_issue is not None:
            self.save_issue(selected_issue)
            self.write_to_cache(self.cache_file_path)
            self.selected_issue = selected_issue

        print(term.clear_eos()+"")
        exit(self.normal_exit_code)

    def save_issue(self,issue_to_save):

        if self.dry_run or len(self.issue_file) < 1:
            return

        file_path = self.issue_file
        issue_key = issue_to_save.split(" ")[0]

        with open(file_path,"w+") as issue_file:
            if self.append_message is None:
                issue_file.write("{} ".format(issue_key))
            else:
                issue_file.write("{0} {1}".format(issue_key,self.append_message))
                # We have to do this so the git-jira script knows to use the -m
                # `git commit` format
                self.normal_exit_code = self.EXIT_CODE_WITH_MESSAGE

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

            if not getattr(self,"project_key",False):
                print("\n[ERROR] Cannot fetch issues without a project key. Please add a 'Project' field to your Jira configuration.")
                exit(self.EXIT_CODE_CANCEL)

            response = self.connector.search_issues(self.project_key,self.assignee_name,self.issue_resolution,self.issue_status)
            issues = self.connector.build_issues_array(response)
            return issues

    def get_responses(self):

        if self.update_on_start or self.no_cache:
            issues = self.refresh_responses_from_net()
            #print(issues)
        else:
            issues = None

            if self.cache_file_path is not None:
                issues = self.read_from_cache(self.cache_file_path)

            if issues == None or self.is_cache_expired() or self.is_config_different():
                issues = self.refresh_responses_from_net()
                # Shitty to do this here, but write to cache does need it
                self.sorted_issues = issues
                # Hey, our cache exists at this point, might as well keep it up to date
                self.write_to_cache(self.cache_file_path)

        return issues

    def apply_config(self,config):

        if "Main" in config and "Max Responses" in config["Main"]:
            if "Max Responses" in config["Main"]:
                self.NUM_RESULTS = config["Main"]["Max Responses"]
            if "Cache File" in config["Main"]:
                self.cache_file_path = config["Main"]["Cache File"]
            if "Refresh Interval" in config["Main"]:
                self.refresh_interval = config["Main"]["Refresh Interval"]

        # Have to add the "is not None" check just in case the Filter area is there, but empty
        if "Filter" in config["Jira"] and config["Jira"]["Filter"] is not None:
            self.assignee_name = config["Jira"]["Filter"].get("Assignee")
            self.project_key = config["Jira"]["Filter"].get("Project")
            self.issue_resolution = config["Jira"]["Filter"].get("Issue Resolution")
            self.issue_status = config["Jira"]["Filter"].get("Status")

    def write_to_cache(self,path):

        if self.dry_run or self.no_cache:
            return

        current_local_ts = self.current_local_config_ts()
        current_global_ts = self.current_global_config_ts()

        # In case we don't have the requisite folder structure for our cache
        if not os.path.exists( str( Path( path ).parent ) ):
            os.makedirs( str( Path(path).parent ) )

        with open(str(path),"w+") as cache_file :
            # CACHE TIMESTAMP
            cache_file.write( "{}\n".format( time.time() ) )
            # LOCAL TIMESTAMP
            cache_file.write( "{}\n".format( current_local_ts ) )
            # GLOBAL TIMESTAMP
            cache_file.write( "{}\n".format( current_global_ts ) )

            cache_file.writelines('\n'.join(self.sorted_issues.copy()))

    def read_from_cache(self,path):

        issues = []

        if os.path.exists(str(path)):
            with open(str(path),'r') as cache_file :
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

        if os.path.exists(str(path)):
            with open(str(path), 'r') as config_file:
                global_config = yaml.load( config_file )

            return global_config
        return None

    def add_title_to_file(self,path, line_to_write, drop_original_title=True):
        with open(str(path), "r") as sources:
            lines = sources.readlines()
        with open(str(path), "w") as sources:
            sources.write(line_to_write)
            if drop_original_title:
                sources.writelines(lines[1:])
            else:
                sources.writelines(lines)

    def interactive_config_bootstrap(self,path,config_title,source_config="",edit_message="",post_message=""):
        # Initialize the config system (copy any example configs to their final directories)
        self.init_config_system(path,source_config)
        # Strip the original title and replace it with the one we're being fed
        self.add_title_to_file(path, config_title)

        # Ask the user to configure the program
        if len(edit_message) > 0:
            print(edit_message)
            # Wait for them to press a key
            blessed.Terminal().inkey()

        # Drop them into editing
        self.edit_file(path,False)

        if len(post_message) > 0:
            print(post_message)
            blessed.Terminal().inkey()

        print(blessed.Terminal().clear_eos()+"")
        exit(self.EXIT_CODE_CONFIG)

    def configure(self,extra_config_path=None):

        global_config_path = self.global_config_path()

        # In case another function needs these
        self.global_config_path = global_config_path

        # Set these up as empty, for now
        self.local_config_path = None
        self.cache_file_path = None

        final_conf = {}

        # Load Global config
        global_conf = self.load_config(global_config_path)
        if global_conf is None:
            title = "# -- Global Configuration File --\n"
            pre = "First time setup complete, configuration required. Press any key to continue."
            post = "Config generated. Please try again. Remember, you can always call `git jira-config global` to edit the global config" if not self.edit_mode else ""
            source = self.script_dir()+"/data/{}.example".format(self.GLOBAL_CONFIG_FILE_NAME)
            # This quits the program execution, so we don't need to worry about global_conf being none - this is the end of the program!
            self.interactive_config_bootstrap(global_config_path,title,source,pre,post)

        final_conf = global_conf

        # Load Local config
        try:

            git_root = self.get_git_root_dir()
            git_branch = self.get_git_branch()

            local_config_path = self.local_configuration_path(git_root,git_branch)
            self.local_config_path = local_config_path

            self.cache_file_path = self.config_dir().joinpath( "{2}/{0}.{1}.cache".format(git_root, git_branch,self.ISSUES_FOLDER_NAME) )

            local_conf = self.load_config(local_config_path)
            if local_conf is None:

                title = "# -- Local Configuration file for Project: {0}, Branch: {1} --\n".format(git_root,git_branch)
                pre = "First time local setup complete, configuration required. Press any key to continue."
                post = "Config generated. Please try again. Remember, you can always call `git jira config local` to edit the local config" if not self.edit_mode else ""
                source = self.script_dir()+"/data/{}.example".format(self.LOCAL_CONFIGS_PREFIX)
                self.interactive_config_bootstrap(local_config_path,title,source,pre,post)

            # Load the local conf onto the global
            #print("global conf before local added: {}".format(global_conf))
            final_conf = self.dict_merge(final_conf,local_conf)
            #print ("final conf after merge: {}".format(final_conf))
        except git.exc.InvalidGitRepositoryError:
            # If we have no git repo, we have no local config, which means no local cache
            self.no_cache = True
            print("[WARNING] No GIT repo detected, running without local configuration.")

        if extra_config_path is not None:
            extra_conf = self.load_config(extra_config_path)
            final_conf = self.dict_merge(final_conf,extra_conf)

        self.config = final_conf

        #Configure UI
        self.apply_config(final_conf)

        return final_conf

    def init_config_system(self,path,example_config=None):

        # Make the parent directory (if necessary)
        if not os.path.exists( str(path.parent) ):
            os.makedirs(str( path.parent ))

        # Now the file itself
        if not os.path.exists( str(path) ):
            if example_config is None:
                # Try to guess where the example file lives...
                shutil.copyfile(self.script_dir()+"/data/{}.example".format(path.name),path)
            else:
                shutil.copyfile(example_config,path)

    def script_dir(self):
        return os.path.dirname(os.path.realpath(__file__))

    def local_configs_dir(self):
        return Path.home().joinpath(".config/{0}/{1}".format(self.CONFIG_DIR_NAME,self.LOCAL_CONFIGS_FOLDER_NAME))

    def current_local_config_ts(self):
        local_config_path = self.local_config_path

        return round( os.path.getmtime(str(local_config_path)) )

    def current_global_config_ts(self):
        global_config_path = self.global_config_path

        return round( os.path.getmtime(str(global_config_path)) )


    def local_configuration_path(self,git_root=None,git_branch=None):

        if git_root is None:
            git_root = self.get_git_root_dir()
        if git_branch is None:
            git_branch = self.get_git_branch()

        local_config_path = self.config_dir().joinpath( "{2}/{0}.{1}.{3}".format(git_root, git_branch,self.LOCAL_CONFIGS_FOLDER_NAME,self.LOCAL_CONFIGS_PREFIX) )
        return local_config_path

    def global_config_path(self):
        return Path.home().joinpath(".config/{0}/{1}".format(self.CONFIG_DIR_NAME,self.GLOBAL_CONFIG_FILE_NAME))

    def config_dir(self):
        return Path.home().joinpath(".config/{0}".format(self.CONFIG_DIR_NAME))


    def edit_file(self,path,exit_after_edit=False):
        editor=os.environ["EDITOR"]

        if editor == "":
            editor = "vi"

        os.system("{0} {1}".format(editor,path))

        if exit_after_edit:
            exit(self.EXIT_CODE_CONFIG)

    def get_git_root_dir(self):
        path = os.getcwd()

        git_repo = git.Repo(path, search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")

        return os.path.basename(git_root).rstrip()


    def get_git_branch(self):
        path = os.getcwd()

        git_repo = git.Repo(path, search_parent_directories=True)

        # Get branches
        git_branches = git_repo.git.branch()
        git_branches = git_branches.split("\n")

        current_branch = [ branch.split(" ")[1].rstrip() for branch in git_branches if "* " in branch ]

        if len(current_branch) > 0:
            return current_branch[0]

        return "UNKNOWN_BRANCH"

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

        home = Path.home()

        parser = argparse.ArgumentParser(prog="git-jira", description="A JIRA issue selector for git messages",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-n', '--num-results', type=int, default=None, help='The number of results to show on screen', metavar='num_results_to_show')
        parser.add_argument('-c', '--extra-config-path', help='An extra config file to load.', metavar='path_to_config_file')
        parser.add_argument('-cc', '--copy-config', action='store_true', help='Allows you to interactively select a pre-existing config for the current local config. E.g. use this if you want to copy the same config from another branch. This overwrites the current config')

        parser.add_argument('-u', '--update-cache', action='store_true', help='Update the issue cache. This happens automatically according to the config (usually), but can be manually controlled from here.')

        parser.add_argument('-e', '--edit-conf', type=str, default="", help='Edit a configuration file. Valid options are global or local. The $EDITOR shell variable must be set for this', metavar='[global|local]')
        parser.add_argument('-d', '--dry-run', action='store_true', help='Does not save anything to the disk (cache or otherwise)')
        parser.add_argument('-nc', '--no-cache', action='store_true', help='Disables reading and writing to the cache')
        parser.add_argument('-m', '--commit-message',type=str,help='A message to automatically append to the key. (think `git commit -m`)')


        parser.add_argument('-i', '--issue-file', default="", type=str, help='The issue selected by the user will be written to this file, if passed. Use this to actually receive the output of the program. I recommend using mktemp to generate this file path.', metavar='issue_file_to_write_to')

        args = parser.parse_args()

        self.dry_run = args.dry_run
        if args.dry_run:
            print("[DRY RUN]")

        if args.copy_config:
            self.start_config_copy()

        self.edit_mode = len(args.edit_conf) > 1

        extra_config_path = None
        if args.extra_config_path is not None:
            extra_config_path = args.extra_config_path

        self.issue_file = args.issue_file
        self.no_cache = args.no_cache

        #Load the configuration system
        if extra_config_path is not None:
            self.configure(extra_config_path)
        else:
            self.configure()

        self.update_on_start = args.update_cache
        #DEBUG
        #self.update_on_start = True

        if args.num_results is not None:
            self.NUM_RESULTS = args.num_results

        if self.edit_mode:
            if args.edit_conf == "global":
                self.edit_file(self.global_config_path,True)
            elif args.edit_conf == "local":
                self.edit_file(self.local_config_path,True)
            else:
                print("[ERROR] Could not find config file for {}, please use global or local".format(args.edit_conf))
                exit(self.EXIT_CODE_CONFIG)

        # Optional message to append
        self.append_message = None
        if args.commit_message is not None:
            self.append_message = args.commit_message

    def get_directory_contents(self,directory_path):
        """ Recursively returns the contents of a given directory (all Path objects)
        :type directory_path: Path
        :param directory_path: The Path object representing the directory to recurse into."""

        contents = []

        for content in directory_path.iterdir():
            # if it's a directory, recurse
            if content.is_dir():
                subdir_contents = self.get_directory_contents(content)
                contents.extend(subdir_contents)
            else:
                # if it's a file add its full representation
                contents.append(directory_path.joinpath(content))

        return contents


    def start_config_copy(self):

        print("Starting interactive copy dialogue for local configuration...")

        try:
            git_root = self.get_git_root_dir()
            git_branch = self.get_git_branch()

            current_local_config_path = self.local_configuration_path(git_root,git_branch)
        except git.exc.InvalidGitRepositoryError:
            # If we have no git repo, we have no local config, which means what the hell are we doing in this function
            print("[WARNING] No GIT repo detected, can't edit local configurations.")
            exit(1)

        local_configs_root = self.local_configs_dir()
        paths = [ path for path in self.get_directory_contents(local_configs_root) if path != current_local_config_path ]
        items = [ path.relative_to(local_configs_root) for path in paths ]

        selected_item_tuple = Selector.select_item(items,15,"Search for local config: ")

        if selected_item_tuple is not None:

            selected_item = selected_item_tuple[0]

            print("Replace current local config for {1}{2} with config from: {0}? (y/n) ".format(selected_item,git_root,git_branch),end="",flush=True)
            term = blessed.Terminal()
            key=term.inkey()

            if key == "y":
                match = [path for path in paths if path.match(str(selected_item))]
                selected_path=match[0]

                print("Replacing {0} with {1}...".format(current_local_config_path, selected_path))
                if not self.dry_run:
                    shutil.copyfile(str(selected_path),str(current_local_config_path))

        exit( self.normal_exit_code )
