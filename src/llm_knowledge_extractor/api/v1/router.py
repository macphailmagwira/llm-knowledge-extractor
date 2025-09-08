from fastapi import APIRouter


from llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api import router as text_analyzer_router


router = APIRouter()

router.include_router(text_analyzer_router, prefix="/text_analyzer", tags=["text_analyzer"])


# Health Check Endpoint
@router.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "message": "Service is healthy"}


# Root Check Endpoint
@router.get("/", tags=["system"])
def root_check():
    return {"status": "ok", "message": "Service is running"}
