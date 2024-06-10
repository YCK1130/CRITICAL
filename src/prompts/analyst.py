
from src.prompts.description import team_description
analyst_prompt = { "system":
"""
You are now a modification analyst. Your task is to identify and summarize the modifications made in the commit. You will receive the following information:

1. **Git Commit Message**: A brief message summarizing the changes made in the commit.
2. **Diff of the Commit**: The actual code changes, wrapped within [Diff # Start] and [Diff # End] tags, where # indicates the section number.

**Your tasks are**:

1. **Summarize Changes**: Summarize the changes made in each diff section and provide a brief description of the changes.
2. **Provide a Final Summary**: After all the diff sections are given, provide a final summary of the changes made in the commit.
3. **Identify Discrepancies**: Compare the git commit message with your summary, identify any discrepancies, and provide a brief explanation of the differences.
4. **Report Absence of Discrepancies**: If there are no discrepancies, respond with "No discrepancies found."

**Instructions**:
- Think step-by-step and carefully. Missing any potential security issues could result in significant financial loss for the company.
- Each section of the diff will be wrapped with [Diff # Start] and [Diff # End], where # is the number of the diff section.
- After all the diff sections are given, you will see [EOF], after which you should provide your final summary and any identified discrepancies.
""", 'example':
"""
**Example**:

User:
Commit Message: Changed "Hello, World!" to "Hello, OpenAI!"

[Diff 1 Start]
diff --git a/file1.py b/file1.py
index 1a2b3c..4d5e6f 100644
--- a/file1.py
+++ b/file1.py
@@ -1,5 +1,5 @@
 def function():
-    print("Hello, World!")
+    print("Hello, OpenAI!")
[Diff 1 End]
[EOF]

Your response:
[Diff 1] Changed "Hello, World!" to "Hello, OpenAI!" in file1.py.
[Summary] Changed "Hello, World!" to "Hello, OpenAI!" in file1.py.
[Discrepancy] No discrepancies found.
"""
, 
"init": "Commit Message: {commit_message}\n\n",
"prompts": ["[Diff {num} Start]\n{diff}\n[Diff {num} End]\n", "[EOF]"],
}

class Analyst:
    def __init__(self, commit_message: str, diffs: list, with_example=False):
        self.setting = analyst_prompt
        self.commit_message = self.setting["init"].format(commit_message=commit_message)
        self.diffs = diffs
        self.system_setting = team_description["system"].replace("\n", " ").strip() + "\n# Roles and Responsibilities:\n" + self.setting["system"]
        if with_example:
            self.system_setting += "\n" + self.setting["example"]
    @property
    def prompts(self):
        prompt = self.commit_message
        for i, diff in enumerate(self.diffs):
            prompt += self.setting["prompts"][0].format(num=i+1, diff=diff)
        prompt += self.setting["prompts"][1]
        return prompt

if __name__ == "__main__":
    analyst = Analyst("Changed \"Hello, World!\" to \"Hello, OpenAI!\"", ["diff --git a/file1.py b/file1.py\nindex 1a2b3c..4d5e6f 100644\n--- a/file1.py\n+++ b/file1.py\n@@ -1,5 +1,5 @@\n def function():\n-    print(\"Hello, World!\")\n+    print(\"Hello, OpenAI!\")"])
    print(analyst.prompts)