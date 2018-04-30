from distutils.core import setup

def readme():
    with open('README.md') as f:
        return f.read()
setup(
    # Application name:
    name="JiraIssueSelector",

    # Version number (initial):
    version="1.0.1",

    # Application author details:
    author="Derin Yarsuvat",
    author_email="derin@ml1.net",

    license='GPLv3',

    # Packages
    packages=['jira_issue_selector'],

    package_data={
        'jira_issue_selector': ['data/*']
        },

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="http://http://github.com/berulacks",

    #
    # license="LICENSE.txt",
    description="Allows you to quickly select and prepend JIRA issues to git commit messages",

    long_description=readme(),

    scripts=[
        'bin/git-jira'
        ],

    # Dependent packages (distributions)
    install_requires=[
        'blessed==1.14.2',
        'certifi==2018.4.16',
        'chardet==3.0.4',
        'fuzzywuzzy==0.16.0',
        'gitdb2==2.0.3',
        'GitPython==2.1.9',
        'idna==2.6',
        'python-Levenshtein==0.12.0',
        'PyYAML==3.12',
        'requests==2.18.4',
        'six==1.11.0',
        'smmap2==2.0.3',
        'urllib3==1.22',
        'wcwidth==0.1.7'
    ],
    zip_safe=False
)

