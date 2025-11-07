import streamlit as st
from google.oauth2 import service_account
from google.cloud import vision
import google.generativeai as genai
import tempfile
import json

# -------------------------------------------------------
# 🔐 1️⃣ 서비스 계정 및 Gemini API 키 로드
# -------------------------------------------------------
raw_info = dict(st.secrets["gcp_service_account"])
raw_info["private_key"] = raw_info["private_key"].replace("\\n", "\n")
credentials = service_account.Credentials.from_service_account_info(raw_info)
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# -------------------------------------------------------
# 🎨 2️⃣ Streamlit 앱 UI
# -------------------------------------------------------
st.set_page_config(page_title="AI 맞춤법 & 문장 교정 도우미", page_icon="📝", layout="wide")
st.title("🧠 AI 맞춤법 · 문장 교정기 (Vision OCR + Gemini AI)")

st.markdown("""
이 앱은 Google Cloud Vision API로 **이미지 또는 PDF에서 텍스트를 추출**하고,  
**Gemini AI로 맞춤법 교정 / 문장 다듬기 / 요약 / 번역**을 수행합니다. ✨

📘 이번 버전은 **PDF의 모든 페이지를 자동 처리**합니다.
""")

# -------------------------------------------------------
# 📂 3️⃣ 파일 업로드
# -------------------------------------------------------
uploaded_file = st.file_uploader("📎 이미지 또는 PDF 파일 업로드", type=["jpg", "jpeg", "png", "pdf"])

# -------------------------------------------------------
# 🧾 4️⃣ OCR (텍스트 추출)
# -------------------------------------------------------
extracted_text = ""

if uploaded_file is not None:
    st.info("🔍 OCR 처리를 시작합니다...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if uploaded_file.type == "application/pdf" else ".png") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    client = vision.ImageAnnotatorClient(credentials=credentials)

    # ✅ PDF 파일 전체 페이지 처리
    if uploaded_file.type == "application/pdf":
        st.warning("📘 PDF의 모든 페이지를 Vision API로 분석합니다. (시간이 다소 걸립니다 ⏳)")
        with open(tmp_path, "rb") as pdf_file:
            content = pdf_file.read()

        mime_type = "application/pdf"
        async_request = {
            "requests": [{
                "input_config": {
                    "content": content,
                    "mime_type": mime_type
                },
                "features": [{"type": vision.Feature.Type.DOCUMENT_TEXT_DETECTION}],
            }]
        }

        try:
            operation = client.async_batch_annotate_files(requests=async_request["requests"])
            result = operation.result(timeout=300)

            all_text = []
            for i, response in enumerate(result.responses):
                for page_response in response.responses:
                    if "full_text_annotation" in page_response:
                        page_text = page_response.full_text_annotation.text
                        all_text.append(page_text)
                        st.info(f"📄 페이지 {i + 1} 처리 완료 ({len(page_text)}자)")

            if all_text:
                extracted_text = "\n".join(all_text)
                st.success(f"✅ 총 {len(all_text)}페이지 처리 완료!")
                st.text_area("📜 전체 추출 텍스트", extracted_text, height=300)
            else:
                st.error("❌ PDF에서 텍스트를 감지하지 못했습니다.")
        except Exception as e:
            st.error(f"Vision API 오류 발생: {e}")

    # ✅ 이미지 파일 처리
    else:
        image = vision.Image(content=uploaded_file.getvalue())
        try:
            response = client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                extracted_text = texts[0].description
                st.success("✅ 텍스트 추출 완료!")
                st.text_area("📜 추출된 텍스트", extracted_text, height=200)
            else:
                st.error("❌ 이미지를 인식하지 못했습니다.")
        except Exception as e:
            st.error(f"Vision API 오류 발생: {e}")

# -------------------------------------------------------
# ✍️ 5️⃣ Gemini 맞춤법 / 교정 / 요약 / 번역
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
st.caption("Made with ❤️ by 유성진 | Google Cloud Vision + Gemini AI (모든 페이지 OCR 지원)")
