import pandas as pd
import requests
import sys
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# =====================
# 1. PYDANTIC MODEL
# =====================
class OrderModel(BaseModel):
    order_id: str = Field(min_length=1)
    qty: int = Field(ge=0)
    amount: float = Field(ge=0)
    currency: str = Field(pattern="^INR$")
    ship_country: str = Field(pattern="^IN$")
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%m-%d-%y")
        except ValueError:
            raise ValueError(f"Tarih formatı hatalı: {v}")
        return v

# =====================
# 2. CSV YUKLE
# =====================
df = pd.read_csv("data/amazon_orders.csv")
print(f"✅ Veri yüklendi: {len(df)} satır")

# =====================
# 3. VALIDATE ET
# =====================
valid_rows = []
invalid_rows = []

for index, row in df.iterrows():
    try:
        row_dict = row.where(pd.notnull(row), None).to_dict()
        if not row_dict.get("order_id"):
            raise ValueError("order_id boş olamaz")
        OrderModel(**row_dict)
        valid_rows.append(row)
    except Exception as e:
        row_copy = row.copy()
        row_copy["hata"] = str(e)
        invalid_rows.append(row_copy)

# =====================
# 4. OZET
# =====================
print(f"✅ Geçerli satır: {len(valid_rows)}")
print(f"❌ Geçersiz satır: {len(invalid_rows)}")

if invalid_rows:
    print("\nHatalı satırlar:")
    for row in invalid_rows:
        print(f"  - order_id: {row.get('order_id', 'N/A')} | Hata: {row.get('hata', '')}")

# =====================
# 5. SLACK BILDIRIMI (opsiyonel)
# =====================
import os
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

if SLACK_WEBHOOK_URL:
    if invalid_rows:
        message = {
            "text": f":warning: *CI Data Quality Sonucu*\n\n"
                    f"✅ Geçerli: {len(valid_rows)}\n"
                    f"❌ Geçersiz: {len(invalid_rows)}"
        }
    else:
        message = {
            "text": f":white_check_mark: *CI Data Quality Başarılı!*\n✅ Tüm satırlar geçerli: {len(valid_rows)}"
        }
    requests.post(SLACK_WEBHOOK_URL, json=message)
    print("✅ Slack bildirimi gönderildi!")

# =====================
# 6. CI CIKIS
# =====================
if invalid_rows:
    print("\n❌ Validation başarısız! CI durduruluyor...")
    sys.exit(1)
else:
    print("\n✅ Validation başarılı!")
    sys.exit(0)