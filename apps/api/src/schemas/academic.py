from typing import Optional, List
from pydantic import BaseModel, Field


class ClassroomBase(BaseModel):
    name: str = Field(..., example="Room 304 - Central AI Lab")
    building: str = Field(default="Building A - ZCOER Narhe")
    latitude: float = Field(..., example=18.4485)
    longitude: float = Field(..., example=73.8245)
    radius_meters: float = Field(default=100.0, ge=10.0, le=500.0)
    is_active: bool = True


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomResponse(ClassroomBase):
    id: str

    class Config:
        from_attributes = True


class ClassEntityBase(BaseModel):
    name: str = Field(..., example="TE-AIDS-DivA")
    academic_year: str = Field(default="2026-2027")
    semester: int = Field(default=6, ge=1, le=8)


class ClassEntityCreate(ClassEntityBase):
    pass


class ClassEntityResponse(ClassEntityBase):
    id: str

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    code: str = Field(..., example="AIDS-401")
    title: str = Field(..., example="Deep Learning & Neural Networks")
    class_id: str


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: str
    class_name: Optional[str] = None

    class Config:
        from_attributes = True


class ClassEnrollmentCreate(BaseModel):
    class_id: str
    student_id: str


class ClassEnrollmentResponse(BaseModel):
    id: str
    class_id: str
    student_id: str
    student_name: Optional[str] = None
    roll_number: Optional[str] = None

    class Config:
        from_attributes = True


class TeacherAssignmentCreate(BaseModel):
    subject_id: str
    teacher_id: str


class TeacherAssignmentResponse(BaseModel):
    id: str
    subject_id: str
    teacher_id: str
    subject_title: Optional[str] = None
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True
