from openai import OpenAI
from functools import partial
from src.utils import chat_auto_complete, MAX_API_RETRY, LLM_MIN_RETRY_SLEEP, LLM_MAX_TOKENS, LLM_TEMPERATURE
from src.prompts.analyst import Analyst
from src.prompts.security import Security
from src.prompts.tester import Tester

import sys
import datetime
import dotenv
import os
import json
import markdown
import argparse
import tqdm

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    @staticmethod
    def warning(text):
        return Colors.WARNING + text + Colors.ENDC
    @staticmethod
    def fail(text):
        return Colors.FAIL + text + Colors.ENDC
    @staticmethod
    def okgreen(text):
        return Colors.OKGREEN + text + Colors.ENDC
    @staticmethod
    def okblue(text):
        return Colors.OKBLUE + text + Colors.ENDC
    @staticmethod
    def okcyan(text):
        return Colors.OKCYAN + text + Colors.ENDC
    @staticmethod
    def header(text):
        return Colors.HEADER + text + Colors.ENDC
    @staticmethod
    def bold(text):
        return Colors.BOLD + text + Colors.ENDC
    @staticmethod
    def underline(text):
        return Colors.UNDERLINE + text + Colors.ENDC

def print_wrapper(title: str, *text):
    split_len = 50
    left = right = (split_len - len(title))//2
    print('='*left, title , '='*right)
    for t in text:
        print(t)
        print('='*split_len)
def store_report(filepath:str, name:str ,data:dict, info:dict, md_type: str = 'txt'):
    with open(os.path.join(filepath, 'raw', f'{name}.json'), 'w') as f:
        json.dump([data, info], f)
    with open(os.path.join(filepath, f'config.json'), 'w') as f:
        json.dump(config, f)
    with open(os.path.join(filepath, 'report', f'{name}_report.md'), 'w') as f:
        txt = data['messages'][-1]['content']
        if md_type == 'txt':
            f.write(txt)
        else:
            html = markdown.markdown(txt)
            f.write(html)
def debate(commit_message:str, diff: list, with_example: bool = False, storepath: str = './data'):
    analyst = Analyst(commit_message=commit_message, diffs=diff, with_example=with_example)
    analyst_comment, info = chat(item={"system": analyst.system_setting, "prompts": [analyst.prompts]})
    store_report(storepath, 'analyst', analyst_comment, info)
    print('Analyst Done', file=sys.stderr)
    
    security = Security(previous=analyst.prompts, comments=analyst_comment['messages'][-1]['content'], with_example=with_example)
    security_comment, info = chat(item={"system": security.system_setting, "prompts": [security.prompts]})
    store_report(storepath, 'security', security_comment, info)
    print('Security Done', file=sys.stderr)
    
    tester = Tester(previous=security.prompts, analysis=security_comment['messages'][-1]['content'], with_example=with_example)
    tester_comment, info = chat(item={"system": tester.system_setting, "prompts": [tester.prompts]})
    if 'no security issue found' in tester_comment['messages'][-1]['content'].lower():
        print(Colors.okgreen('No security issue found'), file=sys.stderr)
    elif 'security issue found' in tester_comment['messages'][-1]['content'].lower():
        print(Colors.fail('Security Issue Found'), file=sys.stderr)
    store_report(storepath, 'tester', tester_comment, info)
    print('Tester Done', file=sys.stderr)
    print(f'Please check the report in {storepath}', file=sys.stderr)

def preprocess(commit: dict):
    diff = []
    commit_message = commit["message"]
    diff_raw = commit["files"]
    for d in diff_raw:
        if d['patch'] in [' ', '', None]:
            filetype = d["filename"].split('.')[-1]
            if filetype in ['png', 'jpg', 'jpeg', 'gif', 'svg']:
                d['patch'] = f'Add/Modify/Delete image file {d["filename"]}'
            elif filetype in ['pdf', 'doc', 'docx']:
                d['patch'] = f'Add/Modify/Delete document file {d["filename"]}'
            elif filetype in ['zip', 'rar', '7z']:
                d['patch'] = f'Add/Modify/Delete compressed file {d["filename"]}'
            elif filetype in ['json', 'csv', 'xls', 'xlsx']:
                d['patch'] = f'Add/Modify/Delete data file {d["filename"]}'
            else:
                d['patch'] = f'Add/Modify/Delete file {d["filename"]}'
        diff.append(f'diff --git {d["filename"]}\n{d["patch"]}')
    return commit_message, diff


def parse_args():
    parser = argparse.ArgumentParser(description='Analyze a commit')
    parser.add_argument('--model', '-m', type=str, default='gpt-4o', help='The model to use')
    parser.add_argument('--basepath', '-p', type=str, default='./commit_data', help='The base path of the commit data')
    parser.add_argument('--filepath', '-f', type=str, default='NTUEELightDance/LightDance-Editor', help='The filepath of repository data')
    parser.add_argument('--branch', '-b', type=str, default='main', help='The branch of the repository')
    parser.add_argument('--with_example', type=bool, default=False, help='Whether to use example')
    parser.add_argument('--target_commit', '-t',  type=str, default='5c5702f8ef3c6a8577ba63b4154ca13b327dbde5', help='The target commit')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    model= args.model
    basepath = args.basepath
    filepath = args.filepath
    branch = args.branch
    with_example = args.with_example
    
    target_commit = args.target_commit.strip()
    if target_commit.isnumeric():
        target_commit = int(target_commit)
    filename = os.path.join(basepath, filepath, f'{branch}.json')
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")
    client = OpenAI(api_key=dotenv.get_key(".env","OPENAI_API_KEY"))
    chat = partial(chat_auto_complete, model=model, client=client)
    
    commits = None
    with open(filename, 'r') as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"File {Colors.fail(filename)} is not a json file")
        if 'commits' not in data:
            raise ValueError(f"File {Colors.fail(filename)} does not have commits")
        if target_commit == 'all':
            commits = data['commits']
        elif isinstance(target_commit, int):
            if target_commit >= len(data['commits']):
                raise ValueError(f"Commit index {Colors.fail(target_commit)} is out of range")
            else:
                commits = [data['commits'][target_commit]]
                target_commit = commits[0]['sha']
        elif isinstance(target_commit, str):
            target_commit = target_commit.lower()
            all_commits: list[str]
            all_commits = [c['sha'] for c in data['commits']]
            assert len(target_commit) > 6, f"{target_commit} is too short"
            valid_commit = [c for c in all_commits if c.startswith(target_commit[:6])]
            if len(valid_commit) == 0:
                raise ValueError(f"Commit {Colors.fail(target_commit)} is not in the commits")
            elif len(valid_commit) > 1:
                raise ValueError(f"Commit {Colors.fail(target_commit)} is too short, please provide more characters")
            else:
                commits = [data['commits'][all_commits.index(valid_commit[0])]]
    if commits is None:
        raise ValueError(f"Commit {Colors.fail(target_commit)} not found")
    
    for commit in tqdm.tqdm(commits):
        print(f"Analyzing commit {commit['sha']} in {filepath} branch {branch}")
        target_commit = commit['sha']
        config = {
            "model": model,
            "filename": filename,
            "with_example": with_example,
            "target_commit": target_commit,
            "max_retry": MAX_API_RETRY,
            "min_retry_sleep": LLM_MIN_RETRY_SLEEP,
            "max_tokens": LLM_MAX_TOKENS,
            "temperature": LLM_TEMPERATURE
        }
        date = datetime.datetime.now().strftime("%m%d%H%M")
        storepath = os.path.join('./data', filepath, branch,  f"{target_commit[:6]}-{model}-{date}")
        os.makedirs(os.path.join(storepath, 'raw'), exist_ok=True)
        os.makedirs(os.path.join(storepath, 'report'), exist_ok=True)

        print('Data Preprocessing...', end='')
        commit_message, diff = preprocess(commit)
        print('\rData Preprocessing Done')
        print('Debating...')
        debate(commit_message, diff, with_example, storepath)
        print('-'*40)
        