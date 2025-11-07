import streamlit as st
from google.cloud import vision
from google.cloud import storage
import tempfile
import time
import os
import json
import requests # Gemini API 호출을 위해 requests 라이브러리 사용

# ----------------------------------------------------------------------
# ⚠️ 주의: 인증 정보
# GCP 클라이언트: 환경 변수 GOOGLE_APPLICATION_CREDENTIALS에 서비스 계정 키 경로 설정 필수.
# GEMINI API: API_KEY 변수에 발급받은 Gemini API 키를 설정해야 작동합니다.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 사용자 정의 설정 (필수 수정)
# ----------------------------------------------------------------------
# OCR 결과를 저장하고 읽을 GCS 버킷 이름 (GCP 콘솔에서 생성된 이름과 동일)
GCS_BUCKET_NAME = "ocr-temp-bucket-for-korean-app"

# 🌟 API KEY 로딩 로직 🌟
API_KEY = "" # 초기화
try:
    # 1. Streamlit secrets에서 로드 시도 (배포 환경 권장)
    API_KEY = st.secrets.get("GEMINI_API_KEY", "") 
except Exception:
    # 2. secrets.toml이 없을 경우 환경 변수에서 로드 시도 (로컬 환경 권장)
    API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 클라이언트 초기화
vision_client = None
storage_client = None

# API_KEY가 설정되지 않은 경우 경고
if not API_KEY:
    st.warning(
        "⚠️ **Gemini API 키가 설정되지 않았습니다.** "
        "다음 방법 중 하나를 사용하여 키를 설정해주세요:\n"
        "1. 로컬에서: `export GEMINI_API_KEY='YOUR_KEY'`\n"
        "2. Streamlit Secrets: `.streamlit/secrets.toml` 파일에 `GEMINI_API_KEY = \"YOUR_KEY\"` 추가"
    )

try:
    # GCP 클라이언트 초기화
    vision_client = vision.ImageAnnotatorClient()
    storage_client = storage.Client()
except Exception as e:
    st.error("❌ Google Cloud 클라이언트 초기화 실패.")
    st.error(f"오류 메시지: {e}")
    st.warning("⚠️ **터미널에서 `export GOOGLE_APPLICATION_CREDENTIALS=...` 환경 변수가 설정되었는지 확인하세요.**")


# --- GCP GCS 및 Vision API Functions ---

def upload_pdf_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """로컬 PDF 파일을 GCS에 업로드합니다."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    st.info(f"📤 GCS 버킷 '{bucket_name}'에 파일 업로드 중...")
    blob.upload_from_filename(source_file_name)
    st.success("✅ 파일 업로드 완료!")
    return f"gs://{bucket_name}/{destination_blob_name}"

def async_detect_document_text(gcs_source_uri, gcs_destination_uri):
    """GCS URI를 사용하여 비동기 OCR을 수행하고 결과를 대기합니다."""
    
    # 1. 입력 설정
    input_config = vision.InputConfig(
        mime_type='application/pdf',
        gcs_source=vision.GcsSource(uri=gcs_source_uri)
    )
    
    # 2. 출력 설정
    output_config = vision.OutputConfig(
        gcs_destination=vision.GcsDestination(uri=gcs_destination_uri),
        batch_size=1
    )

    # 3. API에 요청할 기능 정의
    features = [vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
    
    # 4. 비동기 파일 요청 객체 정의
    async_file_request = vision.AsyncAnnotateFileRequest(
        features=features,
        input_config=input_config,
        output_config=output_config
    )
    
    # 5. 배치 요청 객체 정의
    batch_request = vision.AsyncBatchAnnotateFilesRequest(
        requests=[async_file_request]
    )

    # 6. 배치 요청 실행
    operation = vision_client.async_batch_annotate_files(
        request=batch_request 
    )
    
    # 7. 작업 완료 대기 로직
    start_time = time.time()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while not operation.done():
        time.sleep(10) # 10초마다 상태 확인
        
        elapsed_time = time.time() - start_time
        progress = min(99, int(elapsed_time / 5))
        
        status_text.text(f"현재 상태: OCR 처리 중... | 경과 시간: {int(elapsed_time)}초")
        progress_bar.progress(progress)
        
        if elapsed_time > 300: 
            st.error("❌ OCR 작업이 5분 이상 소요되어 타임아웃 처리되었습니다. PDF 파일이나 네트워크 상태를 확인하세요.")
            raise TimeoutError("OCR Operation Timeout")

    progress_bar.progress(100)
    st.success("✅ OCR 처리 완료!")
    return operation.result()


def download_and_combine_ocr_results(gcs_output_uri, bucket_name):
    """GCS에 저장된 OCR 결과 파일(JSON)들을 다운로드하고 하나의 텍스트로 합칩니다."""
    
    prefix = gcs_output_uri[5 + len(bucket_name):] 
    bucket = storage_client.bucket(bucket_name)
    
    MAX_WAIT_TIME = 300 
    POLL_INTERVAL = 10 
    start_time = time.time()
    wait_status = st.empty()

    json_blobs = []
    
    st.warning(f"🔍 **GCS 검색 경로 확인:** 버킷='{bucket_name}', 접두사(Prefix)='{prefix}'")

    while time.time() - start_time < MAX_WAIT_TIME:
        wait_time = int(time.time() - start_time)
        wait_status.info(f"🔍 GCS에서 OCR 결과 파일 검색 중... | 경과 시간: {wait_time}초 (최대 {MAX_WAIT_TIME}초 대기)")
        
        blob_list = list(bucket.list_blobs(prefix=prefix))
        json_blobs = [b for b in blob_list if b.name.endswith(".json")]

        if json_blobs:
            wait_status.success(f"✅ OCR 결과 파일 발견! (총 {len(json_blobs)}개)")
            break
        
        time.sleep(POLL_INTERVAL)
    else:
        wait_status.error(f"❌ 최대 대기 시간({MAX_WAIT_TIME}초) 초과: GCS 출력 경로 ({gcs_output_uri})에서 JSON 결과 파일을 찾을 수 없습니다.")
        return ""
    
    full_text = ""
    st.info(f"⬇️ {len(json_blobs)}개의 OCR 결과 파일 다운로드 중...")
    
    for blob in json_blobs:
        try:
            json_content = blob.download_as_bytes().decode('utf-8')
            result = json.loads(json_content)
            
            for response in result['responses']:
                if 'fullTextAnnotation' in response:
                    # 페이지 구분을 위해 줄바꿈 추가
                    full_text += response['fullTextAnnotation']['text'] + "\n\n"
            
            # 임시 파일 삭제
            blob.delete()
        except Exception as e:
            st.warning(f"⚠️ 결과 파일 {blob.name} 처리 중 오류 발생: {e}")
            
    st.success("✅ 모든 텍스트 추출 및 임시 GCS 파일 삭제 완료!")
    return full_text

# --- Gemini API Functions ---

def correct_korean_spelling_with_gemini(text_to_correct, api_key):
    """Gemini API를 호출하여 한국어 맞춤법 및 문법 교정을 요청합니다."""
    
    if not api_key:
        return "Gemini API 키가 설정되지 않아 교정을 수행할 수 없습니다."
        
    st.header("3. Gemini 기반 맞춤법 교정 중...")
    
    # 🌟 교정을 위한 프롬프트 정의
    system_instruction = (
        "당신은 최고의 한국어 맞춤법 및 문법 교정 전문가입니다. "
        "사용자가 제공한 텍스트를 검토하여, '맞춤법', '띄어쓰기', '문법 오류', '어색한 표현'을 자연스럽고 정확하게 교정해주세요. "
        "교정된 최종 텍스트만 출력하고, 불필요한 설명(예: '교정된 텍스트입니다')은 추가하지 마십시오."
    )
    user_prompt = f"다음 텍스트를 한국어 맞춤법 및 문법에 맞게 교정해 주세요:\n\n---\n\n{text_to_correct}"
    
    # Gemini API 엔드포인트
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"

    # 요청 페이로드
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }
    
    # 응답 처리
    try:
        # 지연된 API 호출을 위한 지수 백오프 로직 구현
        MAX_RETRIES = 5
        RETRY_DELAY = 1 # 1초
        
        for attempt in range(MAX_RETRIES):
            try:
                with st.spinner(f"🤖 Gemini 모델이 텍스트를 교정 중입니다... (시도 {attempt+1}/{MAX_RETRIES})"):
                    response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, json=payload)
                    response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
                    break # 성공하면 루프 탈출
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt)) # 지수 백오프
                    continue
                else:
                    raise e # 마지막 시도에서도 실패하면 예외 발생

        result = response.json()
            
        if result.get('candidates') and result['candidates'][0]['content']['parts'][0]['text']:
            corrected_text = result['candidates'][0]['content']['parts'][0]['text']
            return corrected_text
        else:
            return "Gemini API 응답에서 교정된 텍스트를 찾을 수 없습니다."

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gemini API 요청 실패 (네트워크 또는 인증 문제): {e}")
        return "API 호출에 실패하여 교정을 수행할 수 없습니다."
    except Exception as e:
        st.error(f"❌ 응답 처리 중 오류 발생: {e}")
        return "응답 처리 중 오류가 발생했습니다."


# --- Main Application Logic ---

def main():
    st.set_page_config(layout="wide")
    st.title("📄 PDF 손글씨 OCR 및 맞춤법 분석기 (Google Vision + Gemini)")
    st.caption("고성능 손글씨 OCR과 Gemini LLM 기반의 한국어 맞춤법 교정 기능을 통합합니다.")
    
    # 클라이언트 초기화 실패 시 앱 실행 중단
    # Note: 클라이언트 초기화 실패 시, 위에 출력된 st.error와 st.warning은 보일 수 있습니다.
    if not vision_client or not storage_client: 
        return
    
    if not API_KEY:
        st.warning("⚠️ **Gemini API 키가 설정되지 않아 맞춤법 교정 기능이 작동하지 않습니다.**")

    # ------------------- 파일 업로드 UI -------------------
    st.header("1. PDF 파일 업로드")

    uploaded_file = st.file_uploader(
        "스캔된 PDF 파일을 업로드하세요.",
        type="pdf",
        key="pdf_uploader",
        help=f"파일은 처리 후 결과를 저장하기 위해 GCS 버킷 ({GCS_BUCKET_NAME})에 임시로 업로드됩니다."
    )

    if uploaded_file is not None:
        
        if st.button("OCR & 맞춤법 교정 시작", key="ocr_button"):
            
            with st.spinner("파일 업로드 및 OCR 작업 요청 중..."):
                
                # 1. 로컬에 임시 파일 생성 및 GCS 경로 설정
                with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as temp_pdf:
                    uploaded_file.seek(0)
                    temp_pdf.write(uploaded_file.read())
                    local_pdf_path = temp_pdf.name
                    
                    # 파일명에 타임스탬프 추가
                    unique_id = time.time()
                    gcs_file_name = f"input/{uploaded_file.name}_{unique_id}"
                    gcs_output_prefix = f"output/{uploaded_file.name}_result_{unique_id}"
                    gcs_output_uri = f'gs://{GCS_BUCKET_NAME}/{gcs_output_prefix}'
                    
                    try:
                        # 2. GCS 업로드
                        gcs_input_uri = upload_pdf_to_gcs(
                            GCS_BUCKET_NAME,
                            local_pdf_path,
                            gcs_file_name
                        )
                        
                        # 3. 비동기 OCR 작업 실행 및 대기
                        operation_result = async_detect_document_text(gcs_input_uri, gcs_output_uri)

                        # 4. GCS에서 OCR 결과 JSON 다운로드 및 텍스트 조합
                        extracted_text = download_and_combine_ocr_results(gcs_output_uri, GCS_BUCKET_NAME)

                        # 5. GCS 입력 파일 삭제 (정리)
                        storage_client.bucket(GCS_BUCKET_NAME).blob(gcs_file_name).delete()
                        st.info("임시 GCS 입력 파일 삭제 완료.")
                        
                        if extracted_text:
                            
                            st.header("2. 추출된 원문 텍스트")
                            st.text_area(
                                "OCR 결과 (교정 전 텍스트)",
                                extracted_text,
                                height=300
                            )
                            
                            # 6. Gemini를 사용하여 맞춤법 교정
                            corrected_text = correct_korean_spelling_with_gemini(extracted_text, API_KEY)
                            
                            st.header("4. ✨ Gemini 교정 결과 텍스트")
                            st.text_area(
                                "맞춤법 및 문법 교정 완료",
                                corrected_text,
                                height=300
                            )
                            st.success("🎉 모든 작업이 성공적으로 완료되었습니다!")

                        else:
                            st.error("❌ 텍스트 추출에 실패했거나 추출된 내용이 없습니다. GCP 로그를 확인하세요.")

                    except Exception as e:
                        st.error(f"❌ OCR 통합 과정 중 치명적인 오류 발생: {e}")
                        st.warning(
                            "⚠️ **GCP 설정 최종 확인: 권한 문제!**\n\n"
                            "이 오류는 Vision API가 결과를 GCS에 쓸 수 있는 권한이 없음을 의미합니다. 다음을 확인하세요:\n\n"
                            "1. **Vision API 서비스 에이전트 ID:** `ocr-service-471@korean-spelling-app.iam.gserviceaccount.com` (사용자님의 ID)\n"
                            "2. **GCS 버킷 IAM 역할:** GCP 콘솔 > Cloud Storage > 해당 버킷의 **Permissions** 탭에서 위 ID에 **'Storage 개체 작성자' (Storage Object Creator)** 역할이 **반드시** 부여되었는지 확인하세요.\n"
                            "3. **Cloud Logging 재확인:** `resource.type=\"gcs_bucket\"` 쿼리로 버킷 로그를 전체 검색하여 `403` 또는 `denied` 메시지를 직접 찾으세요."
                        )

# 실행 진입점 추가
if __name__ == '__main__':
    main()
