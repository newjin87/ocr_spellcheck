"""
vision_ocr.py
----------------------------------
Google Cloud Vision API를 이용한 PDF OCR 모듈

기능 요약:
1. GCS 버킷에 PDF 업로드
2. Vision API로 비동기 OCR 수행
3. OCR 결과 JSON 파일을 가져와 텍스트로 반환
----------------------------------
"""

import streamlit as st
from google.cloud import vision
from google.cloud import storage
import google.cloud.logging_v2 as logging_v2
from google.oauth2 import service_account
import tempfile
import time
import os
import json
import logging

# ----------------------------------------------------------------------
# ✅ 1️⃣ 인증 설정
# ----------------------------------------------------------------------
raw_info = dict(st.secrets["gcp_service_account"])
raw_info["private_key"] = raw_info["private_key"].replace("\\n", "\n")
gcp_credentials = service_account.Credentials.from_service_account_info(raw_info)

# ✅ GCS 버킷 및 결과 경로 설정
BUCKET_NAME = "ocr-temp-bucket-for-korean-app"  # ⚠️ 실제 버킷 이름으로 수정 필요
OUTPUT_PREFIX = "ocr_results/"

# ----------------------------------------------------------------------
# 🧠 2️⃣ 로깅 유틸리티
# ----------------------------------------------------------------------
logger = logging.getLogger("vision_ocr")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log(msg):
    logger.info(msg)
    if "log_text" in st.session_state:
        st.session_state["log_text"] += msg + "\n"

# ----------------------------------------------------------------------
# ☁️ 3️⃣ GCS 유틸리티 함수
# ----------------------------------------------------------------------
def refresh_gcs_client():
    client = storage.Client(credentials=gcp_credentials)
    bucket = client.bucket(BUCKET_NAME)
    bucket.reload()
    return client, bucket

def wait_for_gcs_file(bucket, prefix, timeout=15):
    """GCS에서 Vision 결과 파일이 생성될 때까지 대기"""
    for _ in range(timeout):
        blobs = list(bucket.list_blobs(prefix=prefix))
        if any(blob.name.endswith(".json") for blob in blobs):
            return True
        time.sleep(1)
    return False

def verify_file_via_logging(gcs_path):
    """Cloud Logging으로 Vision OCR 업로드 이력 확인"""
    log_client = logging_v2.Client(credentials=gcp_credentials)
    query = f'resource.type="gcs_bucket" AND textPayload:("{gcs_path}")'
    entries = list(log_client.list_entries(filter_=query))
    return len(entries) > 0

# ----------------------------------------------------------------------
# 👁 4️⃣ Vision API OCR 실행
# ----------------------------------------------------------------------
def perform_ocr(image_path, output_prefix):
    """GCS 상의 PDF 파일을 Vision API로 OCR 처리"""
    client = vision.ImageAnnotatorClient(credentials=gcp_credentials)
    gcs_source_uri = f"gs://{BUCKET_NAME}/{image_path}"
    gcs_destination_uri = f"gs://{BUCKET_NAME}/{output_prefix}"

    log(f"📤 OCR 요청 시작: {gcs_source_uri}")

    async_request = {
        "requests": [{
            "input_config": {
                "gcs_source": {"uri": gcs_source_uri},
                "mime_type": "application/pdf"
            },
            "features": [{"type": vision.Feature.Type.DOCUMENT_TEXT_DETECTION}],
            "output_config": {
                "gcs_destination": {"uri": gcs_destination_uri}
            },
        }]
    }

    operation = client.async_batch_annotate_files(requests=async_request["requests"])
    operation.result(timeout=300)
    log("✅ Vision API OCR 처리 완료")

# ----------------------------------------------------------------------
# 🧾 5️⃣ OCR 결과 가져오기
# ----------------------------------------------------------------------
def fetch_ocr_result(prefix):
    """Vision OCR 결과 JSON 파일을 가져와 텍스트 추출"""
    client, bucket = refresh_gcs_client()
    success = wait_for_gcs_file(bucket, prefix)

    if not success:
        log("⚠️ GCS에서 결과 파일을 찾지 못했습니다. Cloud Logging 조회 중...")
        predicted_uri = f"gs://{BUCKET_NAME}/{prefix}/output-1-to-1.json"
        if verify_file_via_logging(predicted_uri):
            log("✅ Cloud Logging에서 업로드 기록을 확인했습니다. 잠시 후 재시도하세요.")
        else:
            log("❌ 업로드 로그 없음 — Vision API 오류 가능.")
        return None

    blobs = list(bucket.list_blobs(prefix=prefix))
    json_blobs = [b for b in blobs if b.name.endswith(".json")]
    if not json_blobs:
        log("⚠️ JSON 결과 파일이 없습니다.")
        return None

    blob = json_blobs[0]
    data = blob.download_as_text(encoding="utf-8")
    return json.loads(data)

# ----------------------------------------------------------------------
# 🚀 6️⃣ 메인 OCR 파이프라인
# ----------------------------------------------------------------------
def run_ocr_pipeline(uploaded_file):
    """Streamlit에서 업로드된 파일을 OCR 처리하고 텍스트 반환"""
    # 🔐 사용자별 고유 세션 ID로 경로 격리
    user_session_id = st.session_state.get('user_session_id', 'default')
    user_output_prefix = f"ocr_results/{user_session_id}/"
    
    log(f"🔐 세션 ID: {user_session_id}")
    log(f"📊 출력 경로: {user_output_prefix}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    log(f"📂 파일 업로드 완료: {uploaded_file.name}")

    client, bucket = refresh_gcs_client()
    destination_blob_name = f"uploads/{user_session_id}/{os.path.basename(tmp_path)}"
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(tmp_path)
    log(f"✅ GCS 업로드 완료: {destination_blob_name}")

    perform_ocr(destination_blob_name, user_output_prefix)
    ocr_result = fetch_ocr_result(user_output_prefix)

    if ocr_result:
        text_blocks = [p["fullTextAnnotation"]["text"] for p in ocr_result["responses"] if "fullTextAnnotation" in p]
        full_text = "\n".join(text_blocks)
        log("🎉 OCR 결과를 성공적으로 불러왔습니다.")
        return full_text
    else:
        log("❌ OCR 결과를 가져오지 못했습니다.")
        return None
