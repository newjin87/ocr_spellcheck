"""
vision_ocr.py
----------------------------------
Google Cloud Vision API를 이용한 PDF OCR 모듈
(로컬 임시 파일 기반 - 사용자별 격리)

기능 요약:
1. PDF를 로컬 임시 파일로 저장
2. Vision API로 동기식 OCR 수행 (로컬 메모리에서)
3. OCR 결과 텍스트로 반환
4. 자동 정리됨
----------------------------------
"""

import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import tempfile
import os
import json
import logging

# -----------------------------------------------------------------------
# ✅ 1️⃣ 인증 설정
# -----------------------------------------------------------------------
raw_info = dict(st.secrets["gcp_service_account"])
raw_info["private_key"] = raw_info["private_key"].replace("\\n", "\n")
gcp_credentials = service_account.Credentials.from_service_account_info(raw_info)

# -----------------------------------------------------------------------
# 🧠 2️⃣ 로깅 유틸리티
# -----------------------------------------------------------------------
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

# -----------------------------------------------------------------------
# 👁 3️⃣ Vision API OCR 실행 (로컬 파일 기반)
# -----------------------------------------------------------------------
def perform_ocr_local(pdf_path):
    """
    로컬 PDF 파일을 Vision API로 OCR 처리 (동기식)
    GCS 버킷을 사용하지 않고 로컬 메모리에서 직접 처리
    """
    try:
        client = vision.ImageAnnotatorClient(credentials=gcp_credentials)
        
        log(f"📂 로컬 파일에서 OCR 시작: {os.path.basename(pdf_path)}")
        
        # PDF를 바이너리로 읽기
        with open(pdf_path, 'rb') as image_file:
            content = image_file.read()
        
        # Vision API 요청 (로컬 파일 기반)
        image = vision.Image(content=content)
        request = vision.AnnotateImageRequest(
            image=image,
            features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
        )
        
        response = client.annotate_image(request)
        log("✅ Vision API OCR 처리 완료")
        
        return response
        
    except Exception as e:
        log(f"❌ OCR 처리 중 오류: {str(e)}")
        return None

# -----------------------------------------------------------------------
# 🧾 4️⃣ OCR 결과에서 텍스트 추출
# -----------------------------------------------------------------------
def extract_text_from_response(response):
    """Vision API 응답에서 텍스트 추출"""
    if not response:
        return None
    
    if response.error.message:
        log(f"❌ Vision API 오류: {response.error.message}")
        return None
    
    # fullTextAnnotation에서 전체 텍스트 추출
    if response.full_text_annotation:
        full_text = response.full_text_annotation.text
        log(f"📄 추출된 텍스트 길이: {len(full_text)} 글자")
        return full_text
    else:
        log("⚠️ 텍스트 추출 실패")
        return None

# -----------------------------------------------------------------------
# 🚀 5️⃣ 메인 OCR 파이프라인 (사용자별 격리)
# -----------------------------------------------------------------------
def run_ocr_pipeline(uploaded_file):
    """
    Streamlit에서 업로드된 파일을 OCR 처리하고 텍스트 반환
    
    사용자별 독립적인 세션에서 실행됨
    (main_app.py에서 user_session_id 기반으로 격리됨)
    """
    try:
        # 사용자별 고유 임시 디렉토리에 저장
        user_session_id = st.session_state.get('user_session_id', 'default')
        session_temp_dir = os.path.join(tempfile.gettempdir(), f"streamlit_{user_session_id}")
        os.makedirs(session_temp_dir, exist_ok=True)
        
        # 임시 파일에 PDF 저장
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".pdf", 
            dir=session_temp_dir
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        log(f"📤 파일 저장 완료: {os.path.basename(tmp_path)}")
        log(f"🔐 세션 ID: {user_session_id}")
        
        # OCR 수행
        response = perform_ocr_local(tmp_path)
        
        # 텍스트 추출
        full_text = extract_text_from_response(response)
        
        # 임시 파일 정리
        try:
            os.remove(tmp_path)
            log("🧹 임시 파일 정리 완료")
        except:
            pass
        
        if full_text:
            log("🎉 OCR 결과를 성공적으로 불러왔습니다.")
            return full_text
        else:
            log("❌ OCR 결과를 가져오지 못했습니다.")
            return None
            
    except Exception as e:
        log(f"❌ OCR 파이프라인 오류: {str(e)}")
        return None
