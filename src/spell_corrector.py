# src/spell_corrector.py (수정된 최종 코드)
import streamlit as st
import google.generativeai as genai
# ✅ 새로 만든 모듈 import
from src.json_corrector import analyze_and_correct_to_json 
import json 

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
        
    # ----------------------------------------------------------------------
    # 💡 기존 일반 텍스트 교정 로직 (나머지 모드)
    # ----------------------------------------------------------------------

    try:
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return "❌ Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."
    
    try:
        genai.configure(api_key=api_key)
        # ✅ 모델 이름을 일관성 있게 변경 (gemini-2.5-flash)
        model = genai.GenerativeModel("gemini-2.5-flash") 
    except Exception as e:
        return f"❌ Gemini 클라이언트 초기화 실패: {e}"


    # 글쓰기 관련 모드 처리
    try:
        # 모드 포맷: "글쓰기 교정::평가" 또는 "글쓰기 교정::제안" 또는 "글 다시 쓰기"
        if mode == "글쓰기 교정":
            # 종합 글쓰기 교정: 평가(교사용) + 고쳐쓰기 제안(학생용)을 한 번에 출력
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
            try:
                response = model.generate_content(contents=prompt)
                return response.text
            except Exception as e:
                return {"error": f"Gemini 호출 오류 (글쓰기 교정 종합): {e}"}

        if mode.startswith("글쓰기 교정::"):
            submode = mode.split("::", 1)[1]
            if submode == "평가":
                prompt = (
                    "당신은 논설문을 평가하는 6학년 교사입니다. 아래 평가 기준에 따라 학생의 글을 교사의 입장에서 평가하고, "
                    "각 항목별로 1(매우 부족)~5(우수) 점수와 간단한 코멘트를 제공하세요. 항목은:\n"
                    "1) 주장 명확성 및 통일성\n"
                    "2) 근거의 타당성 및 다양성\n"
                    "3) 논리적 흐름과 단계(서론/본론/결론)\n"
                    "4) 독자를 고려한 표현\n"
                    "5) 맞춤법 및 형식의 정확성\n\n"
                    f"학생 글:\n{text}\n\n"
                    "출력 형식: 각 항목별로 '항목명 - 점수: X/5 - 코멘트' 형태로 줄바꿈하여 출력하세요. 마지막에 총평을 한 문단으로 덧붙이세요."
                )
            else:
                # 제안 모드: 6학년 교사의 부드러운 말투로 고쳐쓰기 방향 제시
                prompt = (
                    "당신은 6학년 담임 교사입니다. 학생이 더 설득력있고 읽기 쉬운 글을 쓸 수 있도록 부드럽고 친절한 말투로 구체적인 고쳐쓰기 방향을 제시하세요. "
                    "각 문단별로 개선 포인트를 짚어주고, 간단한 예문(한두 문장)으로 어떻게 수정하면 좋을지 보여주세요.\n\n"
                    f"학생 글:\n{text}\n\n"
                    "출력형식: '개선 포인트:' 항목화, '예시 수정문:'로 간단한 예시를 제시하세요. 마지막에 학생에게 건네는 격려의 한마디를 추가하세요."
                )

            try:
                response = model.generate_content(contents=prompt)
                return response.text
            except Exception as e:
                return {"error": f"Gemini 호출 오류 (글쓰기 교정): {e}"}

        elif mode == "글 다시 쓰기":
            # 사용자가 전달한 text를 더 명료하고 자연스럽게 고쳐줍니다. 원래 의미를 유지하세요.
            prompt = (
                "당신은 국어 교사입니다. 아래 학생의 글을 의미는 그대로 유지하면서 더 명확하고 자연스럽게, 문장 구성을 정돈해 다시 써주세요. "
                "학생의 원문 길이를 많이 변형하지 말고, 필요하면 문장 하나를 두 문장으로 나누어 가독성을 높이세요.\n\n"
                f"원문:\n{text}\n\n"
                "출력은 '다시 쓴 글:' 한 단락으로만 출력하세요."
            )
            try:
                response = model.generate_content(contents=prompt)
                return response.text
            except Exception as e:
                return {"error": f"Gemini 호출 오류 (다시 쓰기): {e}"}

        else:
            return {"error": f"정의되지 않은 모드: {mode}"}

    except Exception as e:
        return {"error": f"내부 오류: {e}"}