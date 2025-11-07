import streamlit as st
import google.generativeai as genai 

def correct_text(text: str, mode: str = "맞춤법 교정") -> str:
    """Gemini API를 사용해 텍스트 맞춤법/문법 교정 및 기타 모드 수행"""

    # ... (키 로드 및 configure 부분은 이전 단계에서 수정되어 정상 작동 중이어야 함)
    try:
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return "❌ Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."
    
    try:
        genai.configure(api_key=api_key)
        # 🟢 모델 이름을 유효한 이름으로 변경합니다.
        model = genai.GenerativeModel("gemini-2.5-flash") # ⚡️ 빠른 응답을 위해 flash 사용 
    except Exception as e:
        return f"❌ Gemini 클라이언트 초기화 실패: API 키를 확인하세요. (오류: {e})"
    
    # ✅ 3. main_app.py의 4가지 모드에 맞춰 프롬프트 확장
    prompts = {
        "맞춤법 교정": (
            f"당신은 한국어 맞춤법 전문가입니다. 다음 문장의 맞춤법, 띄어쓰기, 문법을 교정하고 수정된 결과만 보여주세요. "
            f"원본 내용은 포함하지 마세요:\n\n{text}"
        ),
        "문장 자연스럽게 다듬기": (
            f"다음 텍스트를 읽고, 내용의 핵심을 유지하면서 한국인이 보기에 가장 자연스럽고 세련된 문장으로 다듬어주세요. "
            f"수정된 결과만 출력해:\n\n{text}"
        ),
        "요약하기": f"다음 문장을 간결하게 요약해줘. 결과만 보여줘:\n\n{text}",
        "영어 번역": f"다음 텍스트를 전문적인 비즈니스 영어로 번역해주세요. 번역된 결과만 출력해:\n\n{text}"
    }

    selected_prompt = prompts.get(mode, prompts["맞춤법 교정"])
    
    try:
        response = model.generate_content(selected_prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini API 호출 오류: {e}"