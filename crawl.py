from github import *
import datetime
import dotenv
import json
import os
from tqdm import tqdm

import pytz
utc = pytz.UTC

try:
    with open('token.txt', 'r') as f:
        token = f.read().strip()
except FileNotFoundError:
    token = dotenv.get_key(".env", "GITHUB_TOKEN")
auth = Auth.Token(token)
g = Github(auth=auth)

with open('repoList.txt', 'r') as f:
    repoList = f.read().strip().split('\n')


since = datetime.datetime(2024, 1, 20, tzinfo=utc)
until = datetime.datetime(2024, 5, 27, tzinfo=utc)

base_output_dir = './commit_data'

# don't save repeated commits
sha_set = set()
keyorder = ['owner', 'reponame', 'branch', 'sha',
            'total_commits', 'since', 'until', 'commits']

for repoName in repoList:
    if '/' not in repoName:
        print(f"Invalid repository name: {repoName}")
        continue
    if repoName.startswith('#') or repoName.startswith('//'):
        print(f"Skipping repository: {repoName}")
        continue

    repoInfo = repoName.split('/')
    repoBranch = 'all'
    if len(repoInfo) == 2:
        [owner, repoName] = repoInfo
    elif len(repoInfo) == 3:
        [owner, repoName, repoBranch] = repoInfo
    repo_data = {
        "owner": owner,
        "reponame": repoName,
    }
    json_file_path = os.path.join(base_output_dir, owner, repoName)
    if repoBranch != 'all':
        branchfile = os.path.join(json_file_path, f'{repoBranch}.json')
        try:
            with open(branchfile, 'r') as json_file:
                print(f"Data already exists for {repoName}/{repoBranch}")
                # load the data
                repo_data = json.load(json_file)
                # update the sha_set
                for commit in repo_data["commits"]:
                    sha_set.add(commit["sha"])
        except FileNotFoundError:
            pass
    repo = g.get_repo(f'{owner}/{repoName}')
    branches = repo.get_branches()
    print(f"Repository: {repoName.replace('/', '_')}")
    print("Branches:")
    for branch in branches:
        if repoBranch != 'all' and branch.name != repoBranch:
            continue
        print('--------------------------------------------------')
        print(f"Branch: {branch.name}, SHA: {branch.commit.sha}")
        branch_store_file = os.path.join(json_file_path, f'{branch.name}.json')
        # test if the branch is already in the repo_data
        if os.path.exists(branch_store_file):
            print('--------------------------------------------------')
            print(f"Branch {branch.name} already exists in the data")
            with open(branch_store_file, 'r') as json_file:
                repo_data = json.load(json_file)
            try:
                # latest commit timestamp
                if repo_data.get("since") is not None:
                    fsince = datetime.datetime.fromisoformat(
                        repo_data["since"])
                else:
                    fsince = datetime.datetime.fromisoformat(
                        repo_data["commits"][-1]["timestamp"]) + datetime.timedelta(seconds=1)
                if repo_data.get("until") is not None:
                    funtil = datetime.datetime.fromisoformat(
                        repo_data["until"])
                else:
                    funtil = datetime.datetime.fromisoformat(
                        repo_data["commits"][0]["timestamp"]) + datetime.timedelta(seconds=1)
                assert fsince < funtil
                print(f"First commit timestamp: {fsince}")
                print(f"Last commit timestamp: {funtil}")
                print(f"Request range {since} - {until}")
                print('--------------------------------------------------')
                if since < fsince and until <= funtil:
                    # print('Case 1')
                    until = fsince
                    fsince = since
                elif since >= funtil:
                    # print('Case 2')
                    since = funtil
                    funtil = until
                elif until > funtil:
                    # print('Case 3')
                    since = funtil
                    funtil = until
                else:
                    print(f"Branch {branch.name} is already up to date!")
                    continue
            except Exception as e:
                print(f"Error processing existing data: {e}")
                pass
        else:
            repo_data.update({"commits": [], "total_commits": 0})
        print(f"Search range: {since} - {until}")
        repo_data['sha'] = branch.commit.sha
        repo_data["branch"] = branch.name
        print("Commits:")
        commits = repo.get_commits(
            since=since, until=until, sha=branch.commit.sha)
        repo_data["total_commits"] += commits.totalCount
        processed_commits = []
        if commits.totalCount == 0:
            print("No new commits found")
            continue
        for commit in tqdm(commits, desc='Commits', total=commits.totalCount):
            if commit.sha in sha_set:
                break
            commit_data = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "timestamp": commit.commit.author.date.isoformat(),
                "author": commit.commit.author.name,
                "files": []
            }
            print('--------------------------------------------------')
            print(f"Commit: {commit.sha}")
            message = commit.commit.message
            print(f"Message: {message}")
            files = commit.files
            for file in files:
                file_data = {
                    "filename": file.filename,
                    "patch": file.patch
                }
                commit_data["files"].append(file_data)
                print(f"Filename: {file.filename}")
                print(f"Patch:\n{file.patch}")
                print()
            # repo_data["branches"][branch.name]["commits"].append(commit_data)
            processed_commits.append(commit_data)
            print('--------------------------------------------------')
            sha_set.add(commit.sha)
        repo_data["commits"] = processed_commits + repo_data["commits"]
        repo_data["commits"] = sorted(
            repo_data["commits"], key=lambda x: x["timestamp"], reverse=True)
        repo_data['since'] = repo_data["commits"][-1]["timestamp"]
        repo_data['until'] = repo_data["commits"][0]["timestamp"]
        os.makedirs(json_file_path, exist_ok=True)
        sorted_repo_data = {k: repo_data[k] for k in keyorder}
        try:
            with open(branch_store_file, 'w+') as json_file:
                json.dump(sorted_repo_data, json_file, indent=4)
            print(f"Data successfully written to {branch_store_file}")
        except Exception as e:
            print(f"Error writing to JSON file: {e}")
