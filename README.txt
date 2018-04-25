usage: __main__.py [-h] [-n num_results_to_show] [-c path_to_config_file] [-u]
                   [-e] [-d] [-nc]
                   issue_file_to_write_to

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
                        /Users/derin/.config/jira_issue_appender/jira.conf)
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
