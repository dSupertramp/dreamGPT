import itertools
import json
import random

import openai
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional, List
from colorama import Fore, Style

load_dotenv()

OPEN_AI_API_KEY = os.environ.get('SECRET_KEY')
INIT_IDEA_SIZE = 4
MIX_IDEA_SIZE = 4
STORAGE = []


@dataclass
class Entity:
    title: str
    description: str
    implementation_score: Optional[int] = None
    usefulness_score: Optional[int] = None
    innovation_score: Optional[int] = None


def chat_complete(messages, model="gpt-4"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
    return response


def chat_test():
    messages = [
        {"role": "system", "content": "You are a friendly neighbour GPT"},
        {"role": "user", "content": "Hi, neighbour"},
    ]
    print(chat_complete(messages))


""" Input Message structure
    [
        {"role": "system", "content": ""},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": ""},
        {"role": "user", "content": ""}
    ]"""

""" Output Message structure
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "Hello! How are you today, neighbour? It's nice to see you. If you need any help or just want to chat, feel free to reach out!",
        "role": "assistant"
      }
    }
  ],
  "created": 1682279983,
  "id": "chatcmpl-78aA3nPI5sCkbD3PjyNDXcUbN79i9",
  "model": "gpt-4-0314",
  "object": "chat.completion",
  "usage": {
    "completion_tokens": 33,
    "prompt_tokens": 21,
    "total_tokens": 54
  }
}
"""

"""[
    {"title": String,
    "description": String,
    "score": float,
    }
]"""


def get_combinations(ideas):

    all_combinations = list(itertools.combinations(ideas, 2))

    if MIX_IDEA_SIZE > len(all_combinations):
        print("Number of desired combinations exceeds the total possible combinations.")
        return all_combinations

    return all_combinations[:MIX_IDEA_SIZE]


def send_data(data):
    ...


def sort_by_score(ideas):
    def score_sum(item):
        return sum(item['score'].values())
    return sorted(ideas, key=score_sum, reverse=True)


def parse_step3_json(data: str) -> List[Entity]:
    json_data = json.loads(data)

    result = []

    for item in json_data:
        result.append(
            Entity(
                item["title"],
                item["description"],
                item["score"]["implementation"],
                item["score"]["usefulness"],
                item["score"]["innovation"]
            )
        )

    return result


def parse_step2_json(data: str) -> Entity:
    json_data = json.loads(data)

    return Entity(json_data["title"], json_data["description"])


def parse_step1_json(data: str) -> List[Entity]:
    json_data = json.loads(data)

    result = []

    for item in json_data:
        result.append(Entity(item["title"], item["description"]))

    return result


def parse_json_list(ideas):
    ideas = {"ideas": ideas}
    ...


def step3(mixed_ideas):
    """
    Evaluate, rank & sort best results
    :return:
    """
    print(Fore.YELLOW + "\n\nStep 3: Best results\n" + Style.RESET_ALL)
    evaluated_mixed_ideas = []
    for _ in mixed_ideas:
        prompt = """
        Given the following JSON add a score (0 to 10) in the following format and evaluate the idea in terms of how easy it is to implement, how useful it is to humanity, and how innovative it is

        "score": {
          "implementation" ...
          "usefulness": ...
          "innovation": ...
        }
        """ + json.dumps(mixed_ideas)
        compelition_raw = chat_complete(prompt)
        compelition = parse_step3_json(compelition_raw)
        # TODO: this needs to be a loop
        # print(Fore.WHITE + 'Title: ' + compelition)
        # print('Description: ' + compelition + '\n')
        evaluated_mixed_ideas.append(compelition)
    best_ideas = sort_by_score(evaluated_mixed_ideas)[:len(mixed_ideas)//2]
    return best_ideas


def step2(ideas, priv_best_ideas=[]):
    """
    Combine ideas
    :return:
    """
    print(Fore.YELLOW + "\n\nStep 2: Combine ideas\n" + Style.RESET_ALL)
    combinations = get_combinations(ideas+priv_best_ideas)
    mixed_ideas = []
    for _ in combinations:
        prompt = """
        Given the following JSON, create a single item which takes both ideas and combines a single, coherent and useful idea. Output JSON in the same format. Output JSON only.
        
        [
          {
            "title": "Smart Traffic Lights",
            "description": "Develop a system of traffic lights that use sensors and AI to optimize traffic flow, reduce congestion, and improve safety on the road."
          },
          {
            "title": "Virtual Wardrobe",
            "description": "Create an app that allows users to upload pictures of their clothing and create virtual outfits, making it easier to plan outfits and reduce the environmental impact of fast fashion."
          }
        ]
        """
        compelition_raw = chat_complete(prompt)
        compelition = parse_step2_json(compelition_raw)
        print(Fore.WHITE + 'Title: ' + compelition.title)
        print('Description: ' + compelition.description + '\n')
        mixed_ideas.append(compelition)
    return mixed_ideas


def step1():
    """
    Generate N new ideas
    :return:
    """
    print(Fore.YELLOW + "\n\nStep 1: Generate new ideas\n" + Style.RESET_ALL)
    prompt = f"""
    Generate {INIT_IDEA_SIZE} ideas that are new and useful
        Reply in JSON with this format:
        [
          {
            "title": ...
            "description": ...
          }
        ]
    """
    compelition = chat_complete(prompt)
    raw_ideas = parse_step1_json(compelition)
    for idea in raw_ideas:
        print(Fore.WHITE + 'Title: ' + idea.title)
        print('Description: ' + idea.description + '\n')
    return raw_ideas


def execute_cycle(priv_best_ideas=[]):
    print(Fore.GREEN + "\n\n#################################################")
    print("\n\n#################################################" + Style.RESET_ALL)
    step1_compelition = step1()
    step2_compelition = step2(step1_compelition, priv_best_ideas)
    best_ideas = step3(step2_compelition)
    send_data(best_ideas)
    return best_ideas


def main():
    best_ideas = []
    while True:
        best_ideas = execute_cycle(best_ideas)


if __name__ == "__main__":
    main()
