from typing import List

from langchain.llms import OpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.pydantic_v1 import BaseModel, Field, validator


model_name = "text-davinci-003"
temperature = 0.0
model = OpenAI(model_name=model_name, temperature=temperature)


def get_calendar_date_parser():
    class CalendarDate(BaseModel):
        day: str = Field(description="calendar day of the week")
        time: str = Field(description="time of day")

        # You can add custom validation logic easily with Pydantic.
        @validator("day")
        def question_ends_with_question_mark(cls, field):
            if field[-1] != "?":
                raise ValueError("Badly formed question!")
            return field
    parser = PydanticOutputParser(pydantic_object=CalendarDate)
    return parser

