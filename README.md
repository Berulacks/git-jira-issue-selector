# Jira Issue Selector
*A little utility for automatically selecting and prepending JIRA Cloud Issue keys to git commit messages.*

## Install: 

Just run: `pip3 install JiraIssueSelector` (or download and use one of the releases from [the GitHub repo](https://github.com/Berulacks/git-jira-issue-selector))

*NB: This program requires Python 3.0 or later, compiled with Curses support.*

## Configuration:

The Issue Selector needs to be configured globally, once; and then again one
time for every project.

* To configure it globally type: `git jira config global`

* To configure it locally type (while in a git repository): `git jira config local`


If these files are not found by default, the program will automatically
generate them and prompt you to edit them. This only happens on first-run. **The _Global_ configuration is applied every time the program is run, whereas the _Local_ configuration is specific to the git repo and branch you're currently in.**

The program stores all configuration and cache files in `$HOME/.config/jira_issue_selector`. Cache files are updated every time the user invokes the script with the `-u` flag, updates a configuration file, or the time specified in the `Refresh Interval` field from a configuration file has passed since the program was last run.

When creating new branches in a project you might not want to fill in the local config every time; in this case use the `git jira config copy` command to enter an interactive selection UI to copy/use an older config from another branch (or even project)

_NB:_ Configuration files are loaded in the following order: `Global -> Local -> Additional config specified by the user`

## Usage: 

### Git Wrapper

```
usage: git jira [config global|local|copy] [help] [commit]

optional arguments:
  [commit] Run the issue-selector, then pass the selected issue to 'git commit'
  [config] same as the -e flag below. Note: Pass 'copy' to initiate the interactive config copying dialogue
  [help] same as the -h flag below
```

### Original Python Function

```
usage: __main__.py [-h] [-n num_results_to_show] [-c path_to_config_file]
                   [-cc] [-u] [-e [global|local]] [-d] [-nc]
                   [-m COMMIT_MESSAGE] [-i issue_file_to_write_to]

A JIRA issue selector for git messages

optional arguments:
  -h, --help            show this help message and exit
  -n num_results_to_show, --num-results num_results_to_show
                        The number of results to show on screen (default:
                        None)
  -c path_to_config_file, --extra-config-path path_to_config_file
                        An extra config file to load. (default: None)
  -cc, --copy-config    Allows you to interactively select a pre-existing
                        config for the current local config. E.g. use this if
                        you want to copy the same config from another branch.
                        This overwrites the current config (default: False)
  -u, --update-cache    Update the issue cache. This happens automatically
                        according to the config (usually), but can be manually
                        controlled from here. (default: False)
  -e [global|local], --edit-conf [global|local]
                        Edit a configuration file. Valid options are global or
                        local. The $EDITOR shell variable must be set for this
                        (default: )
  -d, --dry-run         Does not save anything to the disk (cache or
                        otherwise) (default: False)
  -nc, --no-cache       Disables reading and writing to the cache (default:
                        False)
  -m COMMIT_MESSAGE, --commit-message COMMIT_MESSAGE
                        A message to automatically append to the key. (think
                        `git commit -m`) (default: None)
  -i issue_file_to_write_to, --issue-file issue_file_to_write_to
                        The issue selected by the user will be written to this
                        file, if passed. Use this to actually receive the
                        output of the program. I recommend using mktemp to
                        generate this file path. (default: )
```

#### Troubleshooting

##### I'm getting an `ImportError: No module named '_curses'` error
_Note: This will most likely happen if you're using your own compiled version of Python._

Your version of python wasn't compiled with curses support. This is odd, as most distros tend to ship with it. A solution is to install the curses library and its development headers (`libncurses5-dev` and maybe `libncursesw5-dev` on Ubuntu), then coompile a new version of python.

...or you could try to find a packaged version of Python compiled with curses. Up to you. I'd recommend the former on machines that don't support it.
