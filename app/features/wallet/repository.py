from sqlalchemy.orm import Session

from app.features.wallet.model import Wallet


class WalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, wallet: Wallet) -> Wallet:
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_by_student_id(self, student_id: int) -> Wallet | None:
        return self.db.query(Wallet).filter(Wallet.student_id == student_id).first()
