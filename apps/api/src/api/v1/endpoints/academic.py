from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.src.core.database import get_db
from apps.api.src.core.dependencies import require_admin, require_any_authenticated
from apps.api.src.core.audit import log_audit_event
from apps.api.src.models.user import User
from apps.api.src.models.academic import (
    Classroom,
    ClassEntity,
    Subject,
    ClassEnrollment,
    TeacherAssignment,
)
from apps.api.src.schemas.academic import (
    ClassroomCreate,
    ClassroomResponse,
    ClassEntityCreate,
    ClassEntityResponse,
    SubjectCreate,
    SubjectResponse,
    ClassEnrollmentCreate,
    ClassEnrollmentResponse,
    TeacherAssignmentCreate,
    TeacherAssignmentResponse,
)

router = APIRouter(prefix="/academic", tags=["Academic & Classrooms"])


# --- CLASSROOMS ---
@router.get("/classrooms", response_model=List[ClassroomResponse])
def list_classrooms(db: Session = Depends(get_db), current_user: User = Depends(require_any_authenticated)):
    return db.query(Classroom).filter(Classroom.is_active == True).all()


@router.post("/classrooms", response_model=ClassroomResponse)
def create_classroom(payload: ClassroomCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    classroom = Classroom(**payload.model_dump())
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    log_audit_event(db, "CLASSROOM_CREATED", "classroom", admin.id, classroom.id, {"name": classroom.name})
    return classroom


# --- CLASSES ---
@router.get("/classes", response_model=List[ClassEntityResponse])
def list_classes(db: Session = Depends(get_db), current_user: User = Depends(require_any_authenticated)):
    return db.query(ClassEntity).all()


@router.post("/classes", response_model=ClassEntityResponse)
def create_class(payload: ClassEntityCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.query(ClassEntity).filter(ClassEntity.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Class {payload.name} already exists.")
    cls_entity = ClassEntity(**payload.model_dump())
    db.add(cls_entity)
    db.commit()
    db.refresh(cls_entity)
    log_audit_event(db, "CLASS_CREATED", "class", admin.id, cls_entity.id, {"name": cls_entity.name})
    return cls_entity


# --- SUBJECTS ---
@router.get("/subjects", response_model=List[SubjectResponse])
def list_subjects(class_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(require_any_authenticated)):
    query = db.query(Subject)
    if class_id:
        query = query.filter(Subject.class_id == class_id)
    subjects = query.all()
    results = []
    for s in subjects:
        results.append(
            SubjectResponse(
                id=s.id,
                code=s.code,
                title=s.title,
                class_id=s.class_id,
                class_name=s.class_entity.name if s.class_entity else None
            )
        )
    return results


@router.post("/subjects", response_model=SubjectResponse)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    cls_exists = db.query(ClassEntity).filter(ClassEntity.id == payload.class_id).first()
    if not cls_exists:
        raise HTTPException(status_code=404, detail="Referenced class does not exist.")
    subj = Subject(**payload.model_dump())
    db.add(subj)
    db.commit()
    db.refresh(subj)
    log_audit_event(db, "SUBJECT_CREATED", "subject", admin.id, subj.id, {"code": subj.code, "title": subj.title})
    return SubjectResponse(id=subj.id, code=subj.code, title=subj.title, class_id=subj.class_id, class_name=cls_exists.name)


# --- ENROLLMENTS ---
@router.get("/enrollments", response_model=List[ClassEnrollmentResponse])
def list_enrollments(class_id: Optional[str] = None, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    query = db.query(ClassEnrollment)
    if class_id:
        query = query.filter(ClassEnrollment.class_id == class_id)
    enrollments = query.all()
    results = []
    for e in enrollments:
        student_name = f"{e.student.user.first_name} {e.student.user.last_name}" if e.student and e.student.user else "Unknown"
        results.append(
            ClassEnrollmentResponse(
                id=e.id,
                class_id=e.class_id,
                student_id=e.student_id,
                student_name=student_name,
                roll_number=e.student.roll_number if e.student else None
            )
        )
    return results


@router.post("/enrollments", response_model=ClassEnrollmentResponse)
def enroll_student(payload: ClassEnrollmentCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == payload.class_id,
        ClassEnrollment.student_id == payload.student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled in this class.")
    enrollment = ClassEnrollment(**payload.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    log_audit_event(db, "STUDENT_ENROLLED", "enrollment", admin.id, enrollment.id, payload.model_dump())
    student_name = f"{enrollment.student.user.first_name} {enrollment.student.user.last_name}" if enrollment.student and enrollment.student.user else "Student"
    return ClassEnrollmentResponse(
        id=enrollment.id,
        class_id=enrollment.class_id,
        student_id=enrollment.student_id,
        student_name=student_name,
        roll_number=enrollment.student.roll_number if enrollment.student else None
    )


# --- TEACHER ASSIGNMENTS ---
@router.post("/teacher-assignments", response_model=TeacherAssignmentResponse)
def assign_teacher(payload: TeacherAssignmentCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.query(TeacherAssignment).filter(
        TeacherAssignment.subject_id == payload.subject_id,
        TeacherAssignment.teacher_id == payload.teacher_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher already assigned to this subject.")
    assignment = TeacherAssignment(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    log_audit_event(db, "TEACHER_ASSIGNED", "assignment", admin.id, assignment.id, payload.model_dump())
    return TeacherAssignmentResponse(
        id=assignment.id,
        subject_id=assignment.subject_id,
        teacher_id=assignment.teacher_id,
        subject_title=assignment.subject.title if assignment.subject else None,
        teacher_name=f"{assignment.teacher.user.first_name} {assignment.teacher.user.last_name}" if assignment.teacher and assignment.teacher.user else None
    )

