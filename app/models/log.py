from pydantic import BaseModel


class AccessLogResponse(BaseModel):
    user_id: str
    problem_id: str
    action: str
    time: str
    status: str
