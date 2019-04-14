# Attributes of the server this bot will run on
SERVER_HOST = ''
SERVER_PORT = 8888

# Attributes of the IRC connection
IRC_SERVER = 'chat.freenode.net'
IRC_CHANNEL = '#wfbottest'
IRC_NICK = 'WfTestBot'

# Set the password for your registered empty, leave empty if not applicable
# Note: freenode(and potentially other servers) want password to be of the form
# "nick:pass", so for ex. IRC_PASS = 'WfTestBot:mypass123'
IRC_PASS = ''

IRC_PORT = 6667

# a dictionary of branches push-related events should be enabled for, or empty if all are enabled
GH_PUSH_ENABLED_BRANCHES = [] # for example, ['master', 'testing', 'author/repo:branch']

# a list of push-related events the bot should post notifications for
GH_PUSH_ENABLED_EVENTS = ['push', 'force-push', 'delete'] # no others supported for now

# a list of PR-related events the bot should post notifications for
# notice 'merged' is just a special case of 'closed'
GH_PR_ENABLED_EVENTS = ['opened', 'closed', 'reopened'] # could also add 'synchronized', 'labeled', etc.
