import irccolors
import subprocess
import requests

def fmt_repo(data):
    repo = '[' + data['repository']['full_name'] + ']'
    return irccolors.colorize(repo, 'royal')

# Use git.io to get a shortened link for commit names, etc. which are too long
def short_gh_link(link):
    conn = requests.post('https://git.io', data={'url':link})
    return conn.headers['Location']

MAX_COMMIT_LOG_LEN = 5
MAX_COMMIT_LEN = 70

def fmt_last_commits(data):
    # extract data
    commits = map(lambda x: (x['id'][:10], x['author']['name'], x['message']), data['commits'])
    # Merge them into one colored string
    commits = map(lambda (hsh, name, message): \
            irccolors.colorize(hsh, 'teal') \
            + ' ' + irccolors.colorize(name, 'bold-green') + ': ' \
            + message[:MAX_COMMIT_LEN] \
            + ('..' if len(message) > MAX_COMMIT_LEN else ''), \
            commits)

    # make sure the commit list isn't too long
    if len(commits) <= MAX_COMMIT_LOG_LEN:
        return commits
    else:
        ellipsized = str(len(commits) - MAX_COMMIT_LOG_LEN + 1) + ' more'
        last_shown = MAX_COMMIT_LOG_LEN - 1

        return commits[slice(0, last_shown)] + \
                ['... and ' + irccolors.colorize(ellipsized, 'royal') + ' commits']

def handle_force_push(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')

    before = irccolors.colorize(data['before'][:10], 'bold-red')
    after = irccolors.colorize(data['after'][:10], 'bold-red')

    branch = data['ref'].split('/')[-1]
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} force-pushed {} from {} to {} ({}):"
            .format(fmt_repo(data), author, branch, before, after, short_gh_link(data['compare'])))

    commits = fmt_last_commits(data)
    for commit in commits:
        irc.schedule_message(commit)

    print "Force push event"

def handle_forward_push(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')

    num_commits = len(data['commits'])
    num_commits = str(num_commits) + " commit"
    if num_commits > 1:
        num_commits += 's' # make it "commits"

    num_commits = irccolors.colorize(num_commits, 'bold-teal')

    branch = data['ref'].split('/')[-1]
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} pushed {} to {} ({}):"
            .format(fmt_repo(data), author, num_commits, branch, short_gh_link(data['compare'])))

    commits = fmt_last_commits(data)
    for commit in commits:
        irc.schedule_message(commit)

    print "Push event"

def handle_push_event(irc, data):
    if data['forced']:
        handle_force_push(irc, data)
    else:
        handle_forward_push(irc, data)

def handle_ping_event(irc, data):
    print "Ping event"

def handle_event(irc, event, data):
    if event == 'ping':
        handle_ping_event(irc, data)
    elif event == 'push':
        handle_push_event(irc, data)
    else:
        print "Unknown event type: " + event
