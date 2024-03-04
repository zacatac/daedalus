from dataclasses import dataclass
import os
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
