import streamlit as st
import google.genai as genai
from google.genai.types import GenerateContentConfig # JSON Config 클래스 import
import json

# ----------------------------------------------------------------------
# 📝 JSON 출력 스키마 정의
# ----------------------------------------------------------------------
JSON_SCHEMA = """
[
  {
    "sentence_id": int, // 0부터 시작하는 문장 인덱스
    "original_sentence": "string", // 원본 문장 내용
    "is_correct": bool, // 문장에 오류가 없으면 true, 있으면 false
    "corrections": [
      {
        "incorrect_word": "string", // 틀린 단어 또는 구
        "correct_word": "string", // 올바른 교정 내용
        "reason": "string" // 오류가 발생한 이유 또는 유형 (띄어쓰기, 맞춤법 등)
      }
    ]
  }
]
"""

# ----------------------------------------------------------------------
# ⚙️ JSON 교정 핵심 함수
# ----------------------------------------------------------------------
def analyze_and_correct_to_json(text: str):
    """
    텍스트를 분석하여 맞춤법 오류를 찾아 JSON 구조로 반환합니다.
    """
    try:
        # ✅ API 키 경로 통일: st.secrets["gemini"]["api_key"] 사용
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return {"error": "Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."}
    
    try:
        # ✅ SDK 오류 해결: Client 방식으로 변경
        client = genai.Client(api_key=api_key) 
    except Exception as e:
        return {"error": f"Gemini 클라이언트 초기화 실패: {e}"}

    prompt = (
        f"당신은 한국어 맞춤법 및 문법 분석 전문가입니다. "
        f"다음 텍스트를 문장 단위로 나누어 분석하고, 모든 오류(맞춤법, 띄어쓰기, 문법)를 찾아 {JSON_SCHEMA} 형식의 JSON 배열로만 반환하세요. "
        f"오류가 없으면 'is_correct'를 true로, 'corrections'는 빈 배열로 설정해야 합니다. "
        f"반드시 JSON만 출력해야 합니다. 원본 텍스트:\n\n{text}"
    )

    try:
        # 2. Gemini API 호출 (Client.models.generate_content 사용)
        response = client.models.generate_content(
            model='gemini-2.5-flash', # gemini-2.5-flash 모델 사용
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        json_data = json.loads(response.text)
        return json_data
        
    except Exception as e:
        # 오류 발생 시 response 객체가 없을 수 있으므로 안전하게 처리
        error_msg = f"Gemini JSON API 호출 오류: {e}"
        if 'response' in locals() and hasattr(response, 'text'):
             error_msg += f" (응답 텍스트: {response.text[:50]}...)"
        return {"error": error_msg}