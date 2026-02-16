from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    """
    Schema for sending a refresh token to obtain new JWT tokens.
    """
    refresh_token: str = Field(..., description="Refresh token")