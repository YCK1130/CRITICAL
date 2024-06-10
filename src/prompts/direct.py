
direct = { "system":
"""
You will receive the following information:

1. **Git Commit Message**: A brief message summarizing the changes made in the commit.
2. **Diff of the Commit**: The actual code changes, wrapped within [Diff # Start] and [Diff # End] tags, where # indicates the section number.

please tell us if there is any security issue in the commit.
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

class Direct:
    def __init__(self, commit_message: str, diffs: list, with_example=False):
        self.setting = direct
        self.commit_message = self.setting["init"].format(commit_message=commit_message)
        self.diffs = diffs
        self.system_setting = ""
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
    analyst = Direct("Changed \"Hello, World!\" to \"Hello, OpenAI!\"", ["diff --git a/file1.py b/file1.py\nindex 1a2b3c..4d5e6f 100644\n--- a/file1.py\n+++ b/file1.py\n@@ -1,5 +1,5 @@\n def function():\n-    print(\"Hello, World!\")\n+    print(\"Hello, OpenAI!\")"])
    print(analyst.prompts)