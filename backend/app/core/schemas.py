from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    project_path: str


class AnalyzeResponse(BaseModel):
    status: str
    project_path: str
