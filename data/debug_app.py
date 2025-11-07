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
# ✅ 1. Streamlit Secrets 인증 설정
# ----------------------------------------------------------------------
# secrets.toml 예시:
# [gcp_service_account]
# type="service_account"
# project_id="your-project-id"
# private_key="-----BEGIN PRIVATE KEY-----\\nXXXX\\n-----END PRIVATE KEY-----\\n"
# ...


# ✅ secrets.toml에서 서비스 계정 정보를 dict로 복사
raw_info = dict(st.secrets["gcp_service_account"])
raw_info["private_key"] = raw_info["private_key"].replace("\\n", "\n")

# ✅ Credentials 객체 생성
gcp_credentials = service_account.Credentials.from_service_account_info(raw_info)

BUCKET_NAME = "ocr-temp-bucket-for-korean-app"   # 👈 실제 버킷 이름으로 변경
OUTPUT_PREFIX = "ocr_results/"

# ✅ secrets.toml에서 서비스 계정 정보를 dict로 복사
raw_info = dict(st.secrets["gcp_service_account"])
raw_info["private_key"] = raw_info["private_key"].replace("\\n", "\n")

# ✅ Credentials 객체 생성
gcp_credentials = service_account.Credentials.from_service_account_info(raw_info)


# ----------------------------------------------------------------------
# 🧠 로깅 설정
# ----------------------------------------------------------------------
logger = logging.getLogger("ocr_debug")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log(msg):
    logger.info(msg)
    st.session_state["log_text"] += msg + "\n"

# ----------------------------------------------------------------------
# ☁️ GCS 유틸리티
# ----------------------------------------------------------------------
def refresh_gcs_client():
    """GCS 클라이언트 및 버킷 새로고침"""
    client = storage.Client(credentials=gcp_credentials)
    bucket = client.bucket(BUCKET_NAME)
    bucket.reload()
    return client, bucket

def wait_for_gcs_file(bucket, prefix, timeout=10):
    """GCS에서 결과 파일이 올라올 때까지 대기"""
    for _ in range(timeout):
        blobs = list(bucket.list_blobs(prefix=prefix))
        if any(blob.name.endswith(".json") for blob in blobs):
            return True
        time.sleep(1)
    return False

def verify_file_via_logging(gcs_path):
    """Cloud Logging으로 업로드 이력 확인"""
    log_client = logging_v2.Client(credentials=gcp_credentials)
    query = f'resource.type="gcs_bucket" AND textPayload:("{gcs_path}")'
    entries = list(log_client.list_entries(filter_=query))
    return len(entries) > 0

# ----------------------------------------------------------------------
# 👁 Vision API OCR 실행
# ----------------------------------------------------------------------
def perform_ocr(image_path, output_prefix):
    client = vision.ImageAnnotatorClient(credentials=gcp_credentials)
    gcs_source_uri = f"gs://{BUCKET_NAME}/{image_path}"
    gcs_destination_uri = f"gs://{BUCKET_NAME}/{output_prefix}"

    log(f"OCR 요청 시작: {gcs_source_uri}")

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
    log("📤 Vision API OCR 처리 완료")

# ----------------------------------------------------------------------
# 🧾 결과 파일 로드
# ----------------------------------------------------------------------
def fetch_ocr_result(prefix):
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
# 🎛 Streamlit 인터페이스
# ----------------------------------------------------------------------
st.title("📄 GPT-5 Google Vision OCR Analyzer (secrets.toml 인증 완성)")
st.markdown("Gemini보다 **안정적이고 보안 강화된** OCR 시스템입니다.")

if "log_text" not in st.session_state:
    st.session_state["log_text"] = ""

st.text_area("🪵 실시간 로그", value=st.session_state["log_text"], key="log_display", height=250)

uploaded_file = st.file_uploader("📤 PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.success(f"📂 업로드 완료: {uploaded_file.name}")

    if st.button("🚀 OCR 실행"):
        client, bucket = refresh_gcs_client()
        destination_blob_name = f"uploads/{os.path.basename(tmp_path)}"
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(tmp_path)
        log(f"✅ GCS 업로드 완료: {destination_blob_name}")

        perform_ocr(destination_blob_name, OUTPUT_PREFIX)
        ocr_result = fetch_ocr_result(OUTPUT_PREFIX)

        if ocr_result:
            text_blocks = [p["fullTextAnnotation"]["text"] for p in ocr_result["responses"] if "fullTextAnnotation" in p]
            full_text = "\n".join(text_blocks)
            st.text_area("📜 OCR 결과", value=full_text, height=300)
            st.success("🎉 OCR 결과를 성공적으로 불러왔습니다.")
        else:
            st.error("❌ OCR 결과를 가져오지 못했습니다. 로그를 확인하세요.")


