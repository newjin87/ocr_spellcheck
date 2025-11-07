import streamlit as st
from google.oauth2 import service_account
from google.cloud import vision
import google.generativeai as genai
import tempfile
import io
from PIL import Image
import json

# -------------------------------------------------------
# 🔐 1️⃣ 서비스 계정 및 Gemini API 키 로드
# -------------------------------------------------------
raw_info = dict(st.secrets["gcp_service_account"])
credentials = service_account.Credentials.from_service_account_info(raw_info)
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# -------------------------------------------------------
# 🎨 2️⃣ Streamlit 앱 UI
# -------------------------------------------------------
st.set_page_config(page_title="AI 맞춤법 & 문장 교정 도우미", page_icon="📝", layout="wide")
st.title("🧠 AI 맞춤법 · 문장 교정기 (Google Cloud + Gemini)")

st.markdown("""
이 앱은 Google Cloud Vision API로 이미지/PDF에서 텍스트를 추출하고,  
Gemini AI를 이용해 맞춤법 및 문장 교정을 수행합니다. ✨
""")

# -------------------------------------------------------
# 📂 3️⃣ 파일 업로드 섹션
# -------------------------------------------------------
uploaded_file = st.file_uploader("📎 이미지 또는 PDF 파일 업로드", type=["jpg", "jpeg", "png", "pdf"])

# -------------------------------------------------------
# 🧾 4️⃣ OCR (텍스트 추출)
# -------------------------------------------------------
extracted_text = ""

if uploaded_file is not None:
    st.info("파일이 업로드되었습니다. 텍스트를 추출 중입니다...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if uploaded_file.type == "application/pdf" else ".png") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Vision API 클라이언트 생성
    client = vision.ImageAnnotatorClient(credentials=credentials)

    # 이미지 로드
    if uploaded_file.type == "application/pdf":
        st.warning("PDF의 첫 페이지만 처리합니다.")
        with open(tmp_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
    else:
        image = vision.Image(content=uploaded_file.getvalue())

    # 텍스트 감지 요청
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        extracted_text = texts[0].description
        st.success("✅ 텍스트 추출 완료!")
        st.text_area("📜 추출된 텍스트", extracted_text, height=200)
    else:
        st.error("텍스트를 감지하지 못했습니다.")

# -------------------------------------------------------
# ✍️ 5️⃣ Gemini를 통한 교정/피드백
# -------------------------------------------------------
if extracted_text:
    st.subheader("✏️ Gemini 맞춤법 및 문장 교정 결과")

    task = st.selectbox(
        "원하는 작업을 선택하세요:",
        ["맞춤법 교정", "문장 자연스럽게 다듬기", "요약하기", "영어 번역"]
    )

    if st.button("🚀 Gemini로 실행"):
        with st.spinner("Gemini가 작업 중입니다... ⏳"):
            prompt = {
                "맞춤법 교정": f"다음 한국어 문장의 맞춤법과 띄어쓰기를 교정해줘:\n\n{extracted_text}",
                "문장 자연스럽게 다듬기": f"다음 글을 문법적으로 자연스럽게 다듬어줘:\n\n{extracted_text}",
                "요약하기": f"다음 글을 간결하게 요약해줘:\n\n{extracted_text}",
                "영어 번역": f"다음 한국어 문장을 자연스럽게 영어로 번역해줘:\n\n{extracted_text}"
            }[task]

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            result = response.text.strip()
            st.success("✅ Gemini 처리 완료!")
            st.text_area("💬 Gemini 결과", result, height=250)

# -------------------------------------------------------
# 🧩 6️⃣ Footer
# -------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ by 유성진 | Google Cloud Vision + Gemini AI")

