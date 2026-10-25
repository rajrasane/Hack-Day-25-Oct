"""FastAPI Microservice demonstrating Pydantic v1 endpoint integration."""
from fastapi import FastAPI, HTTPException
from service.models import UserProfile

app = FastAPI(
    title="Cloud Native Pune SRE Remediation Target Service",
    description="Demo microservice representing a legacy service needing automated dependency upgrade.",
    version="1.0.0",
)


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "user-profile-service", "version": "1.0.0"}


@app.post("/users", response_model=UserProfile)
def create_user(profile: UserProfile):
    # Pydantic v1 `.dict()` call
    profile_data = profile.dict()
    profile_data["bio"] = (profile_data.get("bio") or "") + " [Verified by SRE]"
    return UserProfile(**profile_data)
