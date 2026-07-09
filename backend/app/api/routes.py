from fastapi import APIRouter

from app.core.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)

router = APIRouter()


@router.post("/analyze")
def analyze_project(request: AnalyzeRequest) -> AnalyzeResponse:

    return AnalyzeResponse(status="connected", project_path=request.project_path)
