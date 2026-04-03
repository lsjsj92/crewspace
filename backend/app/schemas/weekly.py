# backend/app/schemas/weekly.py
# 주간 뷰 응답 스키마

from datetime import date

from pydantic import BaseModel


class MonthlyGoalSubItem(BaseModel):
    title: str
    card_type: str
    status: str


class MonthlyGoalGroup(BaseModel):
    epic_title: str
    project_name: str
    items: list[MonthlyGoalSubItem]


class ActiveProjectItem(BaseModel):
    project_name: str
    epic_title: str


class WeeklyCardItem(BaseModel):
    epic_title: str | None = None
    story_title: str | None = None
    task_title: str
    card_type: str
    due_date: date | None = None
    status: str
    project_name: str


class WeeklyViewResponse(BaseModel):
    week_start: date
    week_end: date
    month: int
    monthly_goals: list[MonthlyGoalGroup]
    active_projects: list[ActiveProjectItem]
    last_week_items: list[WeeklyCardItem]
    this_week_items: list[WeeklyCardItem]
