# CRITICAL
This is the source code for CRITICAL(Collaborative Review Involving Thoughtful Intelligent Code Analysis using LLM), at the same time also CNS (Cannot Sleep) final project for CNS (CSIE 7190) at NTU, in the spring of 2024.
# Installation
Using python==3.12.3
```sh
pip install -r requirements.txt
```

# Usage
## crawl a repo
1. add repo in `repoList.txt`
   1. 'lhy1019/cns-commit-dataset/main' to download only commits from 'main'
   2. 'NTUEELightDance/LightDance-Editor' for unspecified branch
2. run `crawl.py`
```sh
python crawl.py
```

## analyze
1. run `main.py`
```sh
# using sha
python main.py -f NTUEELightDance/LightDance-Editor -b main -t c13b5e700c8db51d22d1be61d1452d90d1f3b9ad
# using the index of commit
python main.py -f NTUEELightDance/LightDance-Editor -b main -t 0
```
2. `python main.py -h` for more information
