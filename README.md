# Jira Issue Selector

## Install: 

Just run: `pip3 install <python package or path to git directory of repo>`

## Configuration:

The Issue Selector needs to be configured globally, once; and then again one
time for every project.

To configure it globally type: `git jira config`

To configure it locally type (while in a git repository): `git jira config local`


If these files are not found by default, the program will automatically
generate them and prompt you to edit them. This only happens on first-run.

The program stores all configuration and cache files in `$HOME/.config/issue-selector`. Cache files are updated every time the user invokes the script with the `-u` flag, updates a configuration file, or the time specified in the `Refresh Interval` field from a configuration file changes.

_NB:_ Configuration files are loaded in the following order: `Global -> Local -> Additional config specified by the user`

## Usage: 

### Git Wrapper

```
usage: git jira [config global|local] [help] [commit]

optional arguments: 
  [commit] Run the issue-selector, then pass the selected issue to 'git commit'
  [config] same as the -e flag below
  [help] same as the -h flag below
```

### Original Python Function

```
usage: python -m jira_issue_selector [-h] [-n num_results_to_show] [-c path_to_config_file] [-u]
                                     [-e] [-d] [-nc] [-i issue_file_to_write_to]

A JIRA issue selector for git messages

positional arguments:
  issue_file_to_write_to
                        The selected issue will be written to this file, if
                        passed. Use this to actually receive the output of the
                        program. I recommend using mktemp to generate this
                        file path.

optional arguments:
  -h, --help            show this help message and exit
  -n num_results_to_show, --num-results num_results_to_show
                        The number of results to show on screen (default: 5)
  -c path_to_config_file, --config-path path_to_config_file
                        The relative path to the configuration file. (default:
                        $HOME/.config/jira_issue_appender/jira.conf)
  -u, --update-cache    Update the issue cache. This happens automatically
                        according to the config (usually), but can be manually
                        controlled from here. (default: False)
  -e, --edit-conf       Drops the user into an editor to edit their
                        configuration file. The $EDITOR shell variable must be
                        set for this (default: False)
  -d, --dry-run         Does not save anything to the disk (cache or
                        otherwise) (default: False)
  -nc, --no-cache       Disables reading and writing to the cache (default:
                        False)
```
