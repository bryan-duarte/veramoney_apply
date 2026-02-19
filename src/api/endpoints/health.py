from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field


health_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "healthy", "service": "veramoney-api", "version": "0.1.0"}
            ]
        }
    )

    status: str = Field(
        default="healthy",
        description="Health status of the API service",
    )
    service: str = Field(
        default="veramoney-api",
        description="Name of the service",
    )
    version: str = Field(
        default="0.1.0",
        description="Current API version",
    )


@health_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health status",
    description="Returns the health status of the VeraMoney API. "
    "Use this endpoint for health checks, monitoring, and load balancer probes.\n\n"
    "**Status Values:**\n"
    "- `healthy`: Service is operating normally\n\n"
    "This endpoint does not require authentication.",
    response_description="Health status information",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "veramoney-api",
                        "version": "0.1.0",
                    }
                }
            },
        },
    },
)
async def health_check() -> HealthResponse:
    return HealthResponse()
