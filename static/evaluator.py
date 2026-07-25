
from pydantic import BaseModel
class EssayEvaluation(BaseModel):
    grammar_score: int
    spelling_score: int
    vocabulary_score: int
    organization_score: int
    content_score: int
    total_score: int
    strengths: list[str]
    weaknesses: list[str]
    feedback: str

from pydantic_ai import Agent
from models import EssayEvaluation

agent = Agent(
    "ollama:qwen2.5vl:3b",
    result_type=EssayEvaluation,
    system_prompt="""
You are an English essay evaluator.

Evaluate the essay using the rubric.

Grammar: /20
Spelling: /20
Vocabulary: /20
Organization: /20
Content: /20

Return ONLY structured JSON.
"""
)

from pdf_utils import pdf_to_images

images = pdf_to_images("essay.pdf")

prompt = """
Evaluate this essay.

Check

- Grammar
- Spelling
- Vocabulary
- Content
- Organization

Return scores and feedback.
"""

result = agent.run_sync(
    prompt,
    images=images
)

print(result.output)