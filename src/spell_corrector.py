# src/spell_corrector.py (수정된 최종 코드)
import streamlit as st
import google.generativeai as genai
# ✅ 새로 만든 모듈 import
from src.json_corrector import analyze_and_correct_to_json 
import json
import hashlib
import time
import traceback

# ✅ 텍스트 해시 함수
def get_text_hash(text: str) -> str:
    """텍스트의 SHA256 해시를 생성하여 캐시 키로 사용"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# ✅ @st.cache_data로 Gemini API 호출 결과 캐싱
@st.cache_data(ttl=3600)
def _call_gemini_writing_api_cached(text_hash: str, prompt: str) -> str:
    """
    Gemini API를 호출하여 글쓰기 교정을 수행하고 결과를 캐싱합니다.
    
    Args:
        text_hash: 텍스트의 SHA256 해시 (캐싱 키)
        prompt: Gemini 모델에 보낼 프롬프트
    
    Returns:
        글쓰기 교정 결과 (문자열)
    """
    try:
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return "❌ Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        return f"❌ Gemini 클라이언트 초기화 실패: {e}"

    max_retries = 3
    base_delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(contents=prompt)
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                raise RuntimeError("응답 텍스트가 비어있습니다.")
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
                continue
            else:
                tb = traceback.format_exc()
                return f"❌ Gemini 호출 오류 (attempts={max_retries}): {e}"

def format_json_result_to_text(json_data):
    """
    JSON 분석 결과를 main_app.py가 표시할 수 있는 깔끔한 텍스트 형식으로 변환합니다.
    (오류 통계 및 상세 교정 내용을 포함)
    """
    if isinstance(json_data, dict) and 'error' in json_data:
        return f"❌ 오류 발생: {json_data['error']}"

    output_text = []
    total_sentences = len(json_data)
    incorrect_sentences = sum(1 for item in json_data if not item['is_correct'])

    # 1. 통계 요약
    output_text.append("="*50)
    output_text.append(f"          맞춤법 오류 분석 결과 (총 {total_sentences} 문장)")
    output_text.append("="*50)
    output_text.append(f"🟢 오류 없음: {total_sentences - incorrect_sentences} 문장")
    output_text.append(f"🔴 오류 발견: {incorrect_sentences} 문장")
    output_text.append("="*50 + "\n")

    # 2. 문장별 상세 분석 (오류 문장만)
    for i, item in enumerate(json_data):
        if not item['is_correct']:
            output_text.append(f"--- [문장 {i+1}] 오류 발견 ---")
            output_text.append(f"원본: {item['original_sentence']}")
            
            # 오류 내용 목록
            if item['corrections']:
                output_text.append("세부 교정 내용:")
                for correction in item['corrections']:
                    output_text.append(
                        f"  - [틀린 부분: {correction['incorrect_word']}] -> "
                        f"[교정: {correction['correct_word']}] ({correction['reason']})"
                    )
            else:
                output_text.append("  - 상세 교정 내용 없음")
            output_text.append("\n")

    return "\n".join(output_text)


def correct_text(text: str, mode: str = "맞춤법 교정") -> str:
    """Gemini API를 사용해 텍스트 맞춤법/문법 교정"""
    
    # 🟢 "맞춤법 교정" 모드를 JSON 분석 기능으로 연결
    if mode == "맞춤법 교정":
        json_data = analyze_and_correct_to_json(text)
        # JSON 결과를 텍스트로 변환하여 main_app.py에 반환
        return format_json_result_to_text(json_data)
        
    # ✅ 글쓰기 교정 모드: 캐싱 적용
    if mode == "글쓰기 교정":
        prompt = (
            "당신은 논설문을 평가하고 고쳐쓰기를 지도하는 6학년 국어 교사입니다. 아래의 평가 기준에 따라 먼저 '평가'를 수행하고, "
            "그 다음에 같은 글에 대해 '고쳐쓰기 제안'을 학생에게 건네는 부드러운 말투로 작성하세요.\n\n"
            "평가 기준:\n"
            "1) 주장 명확성 및 통일성 - 중심 주장이 도입부에 제시되고 글 전체에서 일관되게 유지되는지 여부\n"
            "2) 근거의 타당성 및 다양성 - 경험/통계/전문가 의견 등 최소 세 가지 유형의 근거 제시 여부\n"
            "3) 논리적인 흐름과 단계 - 서론/본론/결론의 구성 및 문단 간 연결성\n"
            "4) 독자를 고려한 표현 - 대상 독자에 맞는 어휘와 설득적 표현 사용 여부\n"
            "5) 맞춤법 및 형식의 정확성 - 맞춤법, 띄어쓰기, 문단 구성 등\n\n"
            f"학생 글:\n{text}\n\n"
            "출력 형식: 먼저 '=== 평가 ===' 섹션에서 각 항목별로 '항목명 - 점수(1-5): 코멘트' 형식으로 줄바꿈하여 제시하고, 한 문단의 총평을 추가하세요. "
            "그 다음 '=== 고쳐쓰기 제안 ===' 섹션에서는 문단별 개선 포인트와 간단한 예시 문장을 제공하고, 마지막에 학생을 격려하는 말로 마무리하세요."
        )
        text_hash = get_text_hash(text)
        return _call_gemini_writing_api_cached(text_hash, prompt)