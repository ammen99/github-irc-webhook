import irccolors
import subprocess
import requests
import config

def fmt_repo(data):
    repo = '[' + data['repository']['full_name'] + ']'
    return irccolors.colorize(repo, 'royal')

# Use git.io to get a shortened link for commit names, etc. which are too long
def short_gh_link(link):
    conn = requests.post('https://git.io', data={'url':link})
    return conn.headers['Location']

MAX_COMMIT_LOG_LEN = 5
MAX_COMMIT_LEN = 70

def fmt_commit(cmt):
    hsh = irccolors.colorize(cmt['id'][:10], 'teal')
    author = irccolors.colorize(cmt['author']['name'], 'bold-green')
    message = cmt['message']
    message = message[:MAX_COMMIT_LEN] \
            + ('..' if len(message) > MAX_COMMIT_LEN else '')

    return '{} {}: {}'.format(hsh, author, message)

def fmt_last_commits(data):
    commits = list(map(fmt_commit, data['commits']))

    # make sure the commit list isn't too long
    if len(commits) <= MAX_COMMIT_LOG_LEN:
        return commits
    else:
        ellipsized_num = len(commits) - MAX_COMMIT_LOG_LEN + 1
        ellipsized = str(ellipsized_num) + ' more'
        last_shown = MAX_COMMIT_LOG_LEN - 1

        last_line = '... and {} commit' \
            .format(irccolors.colorize(ellipsized, 'royal'))
        if ellipsized_num > 1: # add s to commitS
            last_line += 's'

        return commits[slice(0, last_shown)] + [last_line]

def get_branch_name_from_push_event(data):
    return data['ref'].split('/')[-1]

def handle_force_push(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')

    before = irccolors.colorize(data['before'][:10], 'bold-red')
    after = irccolors.colorize(data['after'][:10], 'bold-red')

    branch = get_branch_name_from_push_event(data)
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} force-pushed {} from {} to {} ({}):"
            .format(fmt_repo(data), author, branch, before, after, short_gh_link(data['compare'])))

    commits = fmt_last_commits(data)
    for commit in commits:
        irc.schedule_message(commit)

    print("Force push event")

def handle_forward_push(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')

    num_commits = len(data['commits'])
    num_commits = str(num_commits) + " commit" + ('s' if num_commits > 1 else '')

    num_commits = irccolors.colorize(num_commits, 'bold-teal')

    branch = get_branch_name_from_push_event(data)
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} pushed {} to {} ({}):"
            .format(fmt_repo(data), author, num_commits, branch, short_gh_link(data['compare'])))

    commits = fmt_last_commits(data)
    for commit in commits:
        irc.schedule_message(commit)

    print("Push event")

def handle_delete_branch(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')
    action = irccolors.colorize('deleted', 'red')

    branch = get_branch_name_from_push_event(data)
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} {} {}"
            .format(fmt_repo(data), author, action, branch))

def handle_create_branch(irc, data):
    author = irccolors.colorize(data['pusher']['name'], 'bold')
    action = irccolors.colorize('created', 'green')

    branch = get_branch_name_from_push_event(data)
    branch = irccolors.colorize(branch, 'bold-blue')

    irc.schedule_message("{} {} {} {}"
            .format(fmt_repo(data), author, action, branch))

def handle_push_event(irc, data):
    if config.GH_PUSH_ENABLED_BRANCHES:
        branch = get_branch_name_from_push_event(data)
        repo = data['repository']['full_name']
        repobranch = repo + ':' + branch
        if not branch in config.GH_PUSH_ENABLED_BRANCHES:
            if not repobranch in config.GH_PUSH_ENABLED_BRANCHES:
                return

    if data['forced'] and 'force-push' in config.GH_PUSH_ENABLED_EVENTS:
        handle_force_push(irc, data)
    elif data['deleted'] and 'delete' in config.GH_PUSH_ENABLED_EVENTS:
        handle_delete_branch(irc, data)
    elif data['created'] and 'create' in config.GH_PUSH_ENABLED_EVENTS:
        handle_create_branch(irc, data)
    elif 'push' in config.GH_PUSH_ENABLED_EVENTS:
        handle_forward_push(irc, data)

def fmt_pr_action(action, merged):
    if action == 'opened' or action == 'reopened':
        action = irccolors.colorize(action, 'green')
    elif action == 'closed':
        if merged:
            action = irccolors.colorize('merged', 'purple')
        else:
            action = irccolors.colorize(action, 'red')
    else:
        action = irccolors.colorize(action, 'brown')

    return action

def handle_pull_request(irc, data):
    repo = fmt_repo(data)
    author = irccolors.colorize(data['sender']['login'], 'bold')
    if not data['action'] in config.GH_PR_ENABLED_EVENTS:
        return

    action = fmt_pr_action(data['action'], data['pull_request']['merged'])
    pr_num = irccolors.colorize('#' + str(data['number']), 'bold-blue')
    title = data['pull_request']['title']
    link = short_gh_link(data['pull_request']['html_url'])

    irc.schedule_message('{} {} {} pull request {}: {} ({})'
            .format(repo, author, action, pr_num, title, link))


def handle_issue(irc, data):
    repo = fmt_repo(data)
    user = irccolors.colorize(data['sender']['login'], 'bold')

    action = data['action']
    if not action in ['opened', 'closed']:
        return
    action_color = 'red' if action == 'opened' else 'green'
    action = irccolors.colorize(action, action_color)

    issue_num = irccolors.colorize('#' + str(data['issue']['number']), 'bold-blue')
    title = data['issue']['title']
    link = short_gh_link(data['issue']['html_url'])

    irc.schedule_message('{} {} {} issue {}: {} ({})'
            .format(repo, user, action, issue_num, title, link))


def handle_ping_event(irc, data):
    print("Ping event")

def handle_event(irc, event, data):
    if event == 'ping':
        handle_ping_event(irc, data)
    elif event == 'push':
        handle_push_event(irc, data)
    elif event == 'pull_request':
        handle_pull_request(irc, data)
    elif event == 'issues':
        handle_issue(irc, data)
    else:
        print("Unknown event type: " + event)
