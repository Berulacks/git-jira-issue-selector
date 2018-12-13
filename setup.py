#from distutils.core import setup
from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()
setup(
    # Application name:
    name="JiraIssueSelector",

    # Version number (initial):
    version="1.3.2",

    # Application author details:
    author="Derin Yarsuvat",
    author_email="derin@ml1.net",

    license='GPLv3',

    # Packages
    packages=['jira_issue_selector', 'jira_issue_selector.ui'],

    package_data={
        'jira_issue_selector': ['data/*']
        },

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://github.com/berulacks/git-jira-issue-selector",
    download_url="https://github.com/Berulacks/git-jira-issue-selector/releases/download/v1.3.2/JiraIssueSelector-1.3.2-py3-none-any.whl",

    #
    # license="LICENSE.txt",
    description="Allows you to quickly select and prepend JIRA issues to git commit messages",

    long_description=readme(),
    long_description_content_type='text/markdown',

    scripts=[
        'bin/git-jira'
        ],

    # Dependent packages (distributions)
    install_requires=[
        'blessed>=1.15',
        'certifi==2018.4.16',
        'chardet==3.0.4',
        'fuzzywuzzy>=0.16.0',
        'gitdb2==2.0.3',
        'GitPython==2.1.9',
        'idna==2.6',
        'python-Levenshtein==0.12.0',
        'PyYAML>=4.2b4',
        'requests==2.18.4',
        'six==1.11.0',
        'smmap2==2.0.3',
        'urllib3==1.23',
        'wcwidth==0.1.7'
    ],
    python_requires='>=3',
    zip_safe=False
)

