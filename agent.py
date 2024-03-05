from enum import Enum
import sys
from typing import List, Optional
from functools import reduce
from collections import namedtuple
from modulefinder import ModuleFinder

from model import Model


class ImportSource(Enum):
    STANDARD_LIBRARY = 0
    LOCAL = 1
    EXTERNAL = 2


Import = namedtuple("Import", ["name", "filepath", "source"])


class Agent:
    def __init__(
        self, test_filepath: str, test_output: Optional[str] = None, debug: bool = True
    ):
        self.test_filepath = test_filepath
        self.test_output = test_output
        self.debug = debug
        self.model = Model()

    def run(self):
        if self.debug:
            print(f"Processing test file: {self.test_filepath}")
        imports = self.get_imports(self.test_filepath)
        source_files = list(
            map(
                lambda imp: imp.filepath,
                filter(lambda imp: imp.source == ImportSource.LOCAL, imports),
            )
        )
        if self.debug:
            print(f"Local imports: {source_files}")
        source = self.collect_files(source_files)
        test_source = self.collect_files([self.test_filepath])
        prompt = self.prompt(source, test_source, self.test_output)
        response = self.model.infer(prompt, [])
        if self.debug:
            print("PROMPT:")
            print(prompt)
            print("RESPONSE:")
            print(response)
        self.replace(response)

    def replace(self, response: str):
        file_responses = response.split("FILENAME: ")
        if len(file_responses) < 2:
            raise RuntimeError("Unable to process the response")
        for file_response in file_responses[1:]:
            # TODO: more robust parsing. this fails in a number of cases in surprising ways
            filename, file_content = file_response.split("\n", 1)
            file_content = file_content.strip()
            if self.debug:
                print(f"Processing FILENAME: {filename}")
                print(f"File content: {file_content}")
            # find the contents of the response string between ```python and ``` and write it to the file
            if file_content.startswith("```python"):
                file_content = file_content.split("```python")[1]
            if file_content.startswith("```"):
                file_content = file_content.split("```")[1]
            if file_content.endswith("```"):
                file_content = file_content.split("```")[0]
            if file_content.strip() == "":
                # not deleting all content from files
                continue
            with open(filename.strip(), "w") as file:
                file.write(file_content.strip())

    def collect_files(self, files: List[str]) -> str:
        return reduce(
            lambda acc, file_name: acc
            + f"FILENAME: {file_name}\n"
            + open(file_name, "r").read()
            + "\n",
            files,
            "",
        )

    def get_imports(self, path: str) -> List[Import]:
        finder = ModuleFinder()
        try:
            finder.run_script(self.test_filepath)
        except AttributeError as e:
            # there is a known issue with modulefinder that
            # causes it to fail when spec.loader is None, which
            # is the case for namespaced packages.
            # This blocks usage of the tool in common scenarios
            # like if a user is using Flask.
            print(e)
            raise RuntimeError("Unable to process the test file") from e
        local_filepath = sys.path[0]

        imports = []
        for name, mod in finder.modules.items():
            filename = mod.__file__
            if filename is None:
                continue
            if "__" in name:
                continue
            source = ImportSource.EXTERNAL
            if filename.startswith(local_filepath):
                source = ImportSource.LOCAL
            # TODO: generalize this to other standard library paths
            if "Python.framework" in filename:
                source = ImportSource.STANDARD_LIBRARY
            imports.append(Import(name, filename, source))
            # TODO: use mod.globalnames.keys() to figure out which
            # bits of a file to import if we don't need to import the entire file
        return imports

    def prompt(self, source: str, test_source: str, test_output: str):

        # previous output format prompt: This updated code block should be formatted as a git file diff which can be
        # supplied to the "patch" command to achieve the desired outcome.
        return f"""
Your goal is to update existing code or write new code to make this test suite pass. You are being prompted because the test suite failed.
Each block is clearly marked with start and end blocks like START_<X> and END_<X> blocks. Return only an updated block of code to be evaluated.
The block of code to be edited is between the blocks START_SOURCE and END_SOURCE. Ensure that if multiple source files are present, the correct source file is being edited.
Identify the source file to be edited by the file name in your response with the following format: FILENAME: <file_name>.

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


if __name__ == "__main__":
    agent = Agent(sys.argv[1], sys.argv[2])
    agent.run()
