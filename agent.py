from dataclasses import dataclass
from enum import Enum
import os
import subprocess
import sys
import tempfile
from typing import List
from openai import OpenAI


@dataclass
class Message:
    role: str  # is actually an enumeration
    content: str


# TODO: subclass for different model providers
class Model:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        # TODO: eval which models can be effective at this.
        # evaluated 3.5 very minimally and it was able to solve basic
        # problems but would not return output as requested in the form of a diff.
        # self.model_name = "gpt-3.5-turbo"
        self.model_name = "gpt-4-0125-preview"
        self.client = OpenAI()

    def infer(self, prompt: str, context: List[Message]) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. You are helping an engineer to update their source code so that it passes well-defined tests.",
            }
        ]
        messages.extend(
            map(
                lambda m: {"role": m.role, "content": m.content},
                context,
            )
        )
        messages.append(
            {
                "role": "user",
                "content": prompt,
            },
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        # TODO: dont assume a single response choice.
        return response.choices[0].message.content


class Result(Enum):
    PASSED = 0
    FAILED = 1
    EXIT = 2


class Agent:
    def __init__(self):
        # TODO: generalize to a collection of input files, test files, and possible run commands.
        self.source_file = "source.py"
        self.test_file = "test_source.py"
        self.eval_command = ["poetry", "run", "pytest", "test_source.py"]
        self.max_loop_count = 10
        self.loop_count = 0
        self.conversations: List[Message] = []
        self.model = Model()
        self.debug = True

    def loop(self) -> Result:
        if self.debug:
            print("STARTING LOOP")

        output = self.run()
        if self.debug:
            print("TEST OUTPUT:")
            print(output)

        if output.returncode == 0:
            if self.debug:
                print("PASSED")
            return Result.PASSED

        self.loop_count += 1
        if self.loop_count > self.max_loop_count:
            return Result.EXIT
        # TODO: don't assume the content is in stdout
        test_output = output.stdout
        prompt = self.prompt(test_output=test_output)
        response = self.model.infer(prompt, self.conversations)
        self.conversations.extend(
            (
                Message(role="user", content=prompt),
                Message(role="assistant", content=response),
            )
        )
        if self.debug:
            print("PROMPT:")
            print(prompt)
            print("RESPONSE:")
            print(response)

        if self.patch(response) != 0:
            raise RuntimeError(
                "failed to apply recommended diff",
            )

        return Result.FAILED

    def prompt(self, test_output: str):
        source = None
        with open(self.source_file, "r") as file:
            source = file.read()
        test_source = None
        with open(self.test_file, "r") as file:
            test_source = file.read()

        return f"""
Your goal is to update existing code or write new code to make this test suite pass. You are being prompted because the test suite failed.
Each block is clearly marked with start and end blocks like START_<X> and END_<X> blocks. Return only an updated block of code to be evaluated.
The block of code to be edited is between the blocks START_SOURCE and END_SOURCE. This updated code block should be formatted as a git file diff which can be
supplied to the "patch" command to achieve the desired outcome.

START_SOURCE
```
{source}
```
END_SOURCE

START_TEST_SOURCE
```
{test_source}
```
END_TEST_SOURCE

START_TEST_OUTPUT
```
{test_output}
```
END_TEST_OUTPUT
        """

    def patch(self, diff: str) -> int:

        if diff.startswith("```"):
            # trim the first line
            diff = diff[diff.find("\n") + 1 :]
        if diff.endswith("```"):
            # trim the last line
            diff = diff[: diff.rfind("\n")]
        if self.debug:
            print("PATCH:")
            print(diff)
        tmp_file_path = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(diff.encode())
            tmp_file_path = tmp_file.name

        return subprocess.run(
            [
                "patch",
                self.source_file,
                tmp_file_path,
            ],
            text=True,
            check=False,
        ).returncode

    def run(self):
        return subprocess.run(
            self.eval_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )


if __name__ == "__main__":
    working_directory = sys.argv[1]  # Accept working directory as an argument
    os.chdir(working_directory)  # Change to the specified working directory

    agent = Agent()
    solved = False
    while not solved:
        print("EXEC")
        result = agent.loop()
        if result == Result.PASSED:
            print("SOLVED")
            subprocess.run(
                ["git", "diff"], cwd=working_directory, check=False
            )  # Execute from the specified directory
            solved = True
        if result == Result.EXIT:
            raise RuntimeError("Failed to solve in max iterations")
