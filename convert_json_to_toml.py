import json
import toml
import os

# 1️⃣ 파일 경로 설정
json_path = "korean-spelling-app-19e357dc02fa.json"  # 구글 서비스 계정 키 파일명
output_path = ".streamlit/secrets.toml"

# 2️⃣ Gemini API 키 직접 입력 (또는 환경변수에서 불러오기)
GEMINI_API_KEY = "AIzaSyDDMc2Nn8xJgHOUfOLhzOd1V7B6k-CYLTw"

# 3️⃣ JSON 파일 읽기
with open(json_path, "r") as f:
    data = json.load(f)

# 4️⃣ private_key의 줄바꿈 복원 (2단계 처리)
if "private_key" in data:
    pk = data["private_key"]

    # 첫 번째: 실제 역슬래시 처리 (\\n → \n)
    pk = pk.encode("utf-8").decode("unicode_escape")

    # 두 번째: 혹시 남아있는 이중 인코딩 제거
    pk = pk.replace("\\n", "\n")

    data["private_key"] = pk.strip()

# 5️⃣ TOML 구조 생성
toml_data = {
    "gcp_service_account": data,
    "gemini": {"api_key": GEMINI_API_KEY}
}

# 6️⃣ .streamlit 폴더 생성
os.makedirs(".streamlit", exist_ok=True)

# 7️⃣ TOML 파일 저장
with open(output_path, "w", encoding="utf-8") as f:
    toml.dump(toml_data, f)

print(f"✅ 변환 완료! secrets.toml 파일이 생성되었습니다 → {output_path}")
