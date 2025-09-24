
from typing import Union
from pydantic import BaseModel, Field

class Thought(BaseModel):
    thought: str

class Action(BaseModel):
    action: str
    action_input: str

class Observation(BaseModel):
    observation: str

class Answer(BaseModel):
    answer: str

class Example(BaseModel):
    user: str
    agent: list[Union[Thought, Action, Observation, Answer]] = Field(default_factory=list)

class Prompt(BaseModel):
    role: str
    constraints: list[str] = Field(default_factory=list)
    task_rules: list[str] = Field(default_factory=list)
    examples: list[Example] = Field(default_factory=list)
