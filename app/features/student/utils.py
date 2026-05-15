import base64
from datetime import datetime
import io
import secrets
import string

import qrcode


def generate_parent_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_student_qr_base64(student_code: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(student_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_student_code() -> str:
    date_part = datetime.utcnow().strftime("%y%m%d")
    random_part = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"STD-{date_part}-{random_part}"
