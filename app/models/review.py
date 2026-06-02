from pydantic import BaseModel, Field
from typing import List

class ReviewComment(BaseModel):
    file_path: str = Field(description="The path of the file being reviewed")
    line_number: int = Field(description="The exact line number where the issue occurs in the diff")
    severity: str = Field(description="Severity of the issue: 'low', 'medium', or 'high'")
    comment: str = Field(description="The review comment text explaining the issue and suggesting a fix")

class PRReview(BaseModel):
    comments: List[ReviewComment] = Field(description="List of review comments for the pull request")