from sqlalchemy.orm import Session

from app.features.student.model import Student


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, student: Student) -> Student:
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def get_by_id(self, student_id: int) -> Student | None:
        return self.db.query(Student).filter(Student.id == student_id).first()

    def get_by_code(self, student_code: str) -> Student | None:
        return self.db.query(Student).filter(Student.student_code == student_code).first()

    def get_by_national_id(self, national_id: str) -> Student | None:
        return self.db.query(Student).filter(Student.national_id == national_id).first()

    def get_by_parent_user_id(self, parent_user_id: int) -> Student | None:
        return self.db.query(Student).filter(Student.parent_user_id == parent_user_id).first()

    def list_all(self, national_id: str | None = None) -> list[Student]:
        query = self.db.query(Student)
        if national_id:
            query = query.filter(Student.national_id == national_id)
        return query.order_by(Student.id.desc()).all()

    def list_issued_cards(self) -> list[Student]:
        return (
            self.db.query(Student)
            .filter(Student.card_issued_at.isnot(None))
            .order_by(Student.card_issued_at.desc(), Student.id.desc())
            .all()
        )
