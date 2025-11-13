# src/json_corrector.py
import streamlit as st
import google.generativeai as genai
import json
import time
import re
import traceback
import hashlib

# ✅ Gemini 모델 클라이언트를 캐시하여 반복 초기화 방지
@st.cache_resource
def get_gemini_model():
    """Gemini 모델 인스턴스를 캐시하여 재사용"""
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        return None

# ----------------------------------------------------------------------
# 📝 JSON 출력 스키마 정의
# ----------------------------------------------------------------------
# Gemini 모델에게 요청할 JSON의 구조를 문자열로 명시합니다.
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

# ✅ 텍스트 해시 함수 (캐싱 키 생성용)
def get_text_hash(text: str) -> str:
    """텍스트의 SHA256 해시를 생성하여 캐시 키로 사용"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# ✅ @st.cache_data로 Gemini API 호출 결과 캐싱
@st.cache_data(ttl=3600)
def _call_gemini_api_cached(text_hash: str, prompt: str) -> dict:
    """
    Gemini API를 호출하고 결과를 캐싱합니다.
    
    Args:
        text_hash: 텍스트의 SHA256 해시 (캐싱 키)
        prompt: Gemini 모델에 보낼 프롬프트
    
    Returns:
        JSON 분석 결과 또는 오류 정보
    """
    model = get_gemini_model()
    if model is None:
        return {"error": "Gemini 클라이언트 초기화 실패"}

    # 안전한 JSON 파싱 유틸리티
    def try_parse_json(text: str):
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        arr_match = re.search(r"(\[.*\])", text, re.S)
        if arr_match:
            try:
                return json.loads(arr_match.group(1))
            except Exception:
                pass

        obj_match = re.search(r"(\{.*\})", text, re.S)
        if obj_match:
            try:
                return json.loads(obj_match.group(1))
            except Exception:
                pass

        raise ValueError("응답에서 JSON을 파싱할 수 없습니다.")

    response = None
    max_retries = 3
    base_delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(contents=prompt)

            if hasattr(response, 'text') and response.text:
                try:
                    json_data = try_parse_json(response.text)
                    return json_data
                except Exception as parse_err:
                    tb = traceback.format_exc()
                    return {"error": f"JSON 파싱 실패: {parse_err}. 응답 일부: {response.text[:200]}", "trace": tb}
            else:
                raise RuntimeError("응답 텍스트가 비어있습니다.")

        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
                continue
            else:
                resp_snippet = None
                try:
                    if response is not None and hasattr(response, 'text'):
                        resp_snippet = response.text[:300]
                except Exception:
                    resp_snippet = None

                tb = traceback.format_exc()
                return {"error": f"Gemini JSON API 호출 오류 (attempts={max_retries}): {e}", "response_snippet": resp_snippet, "trace": tb}

# -------------------------------------------------------
# ⚙️ JSON 교정 핵심 함수
# -------------------------------------------------------
def analyze_and_correct_to_json(text: str):
    """
    텍스트를 분석하여 맞춤법 오류를 찾아 JSON 구조로 반환합니다.
    ✅ 동일한 텍스트는 캐시된 결과를 즉시 반환합니다 (네트워크 요청 없음).
    """
    # 1. 프롬프트 구성
    prompt = (
        f"당신은 한국어 맞춤법 및 문법 분석 전문가입니다. "
        f"다음 텍스트를 문장 단위로 나누어 분석하고, 모든 오류(맞춤법, 띄어쓰기, 문법)를 찾아 {JSON_SCHEMA} 형식의 JSON 배열로만 반환하세요. "
        f"오류가 없으면 'is_correct'를 true로, 'corrections'는 빈 배열로 설정해야 합니다. "
        f"반드시 JSON만 출력해야 합니다. 원본 텍스트:\n\n{text}"
    )
    
    # 2. 텍스트 해시 생성 (캐싱 키)
    text_hash = get_text_hash(text)
    
    # 3. 캐시된 API 호출 (동일 텍스트면 네트워크 요청 없음)
    return _call_gemini_api_cached(text_hash, prompt)