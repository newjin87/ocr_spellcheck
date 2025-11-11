"""
debugging_app.py
----------------------------------
Gemini API 설정 및 패키지 정보 디버깅
----------------------------------
"""

import sys
import streamlit as st

st.title("🔍 Gemini API 디버깅")

# 1. google.genai 패키지 정보 확인
st.subheader("1️⃣ google.genai 패키지 정보")
try:
    import google.genai as genai
    st.write("✅ google.genai 임포트 성공")
    st.write(f"**패키지 위치**: {genai.__file__}")
    st.write(f"**패키지 버전**: {genai.__version__ if hasattr(genai, '__version__') else 'Version 정보 없음'}")
    
    # 사용 가능한 속성 확인
    st.write("**사용 가능한 주요 속성:**")
    attrs = dir(genai)
    important_attrs = ['configure', 'GenerativeModel', 'types', 'protos']
    for attr in important_attrs:
        status = "✅" if attr in attrs else "❌"
        st.write(f"  {status} {attr}")
    
except ImportError as e:
    st.error(f"❌ google.genai 임포트 실패: {e}")
    sys.exit(1)

# 2. google-generativeai 패키지 확인
st.subheader("2️⃣ 설치된 패키지 확인")
try:
    import pkg_resources
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    if 'google-generativeai' in installed_packages:
        st.write(f"✅ google-generativeai 설치됨: v{installed_packages['google-generativeai']}")
    else:
        st.warning("❌ google-generativeai 패키지가 설치되지 않았습니다!")
        st.write("다음 명령어로 설치하세요:")
        st.code("pip install --upgrade google-generativeai", language="bash")
        
except Exception as e:
    st.write(f"패키지 확인 중 오류: {e}")

# 3. Streamlit Secrets 확인
st.subheader("3️⃣ Streamlit Secrets 확인")
try:
    api_key = st.secrets["gemini"]["api_key"]
    masked_key = api_key[:10] + "***" + api_key[-10:] if len(api_key) > 20 else "***"
    st.write(f"✅ Gemini API 키 로드 성공")
    st.write(f"**API 키 (마스킹)**: {masked_key}")
except KeyError as e:
    st.error(f"❌ Secrets 로드 실패: {e}")
    st.write("`.streamlit/secrets.toml` 파일을 확인하세요:")
    st.code("""[gemini]
api_key = "your-api-key-here"
""", language="toml")
except Exception as e:
    st.error(f"❌ 예상치 못한 오류: {e}")

# 4. 올바른 API 사용 방법 테스트
st.subheader("4️⃣ 올바른 Gemini API 초기화 방법")

try:
    # 최신 패키지의 올바른 초기화 방법 확인
    if hasattr(genai, 'configure'):
        st.write("**방법 1: genai.configure() 사용 가능**")
        try:
            api_key = st.secrets["gemini"]["api_key"]
            genai.configure(api_key=api_key)
            st.write("✅ genai.configure() 성공")
            
            # GenerativeModel 확인
            if hasattr(genai, 'GenerativeModel'):
                model = genai.GenerativeModel("gemini-pro", api_key=api_key)
                st.write("✅ GenerativeModel 초기화 성공")
            else:
                st.warning("❌ GenerativeModel 속성 없음")
        except Exception as e:
            st.error(f"❌ genai.configure() 실패: {e}")
    else:
        st.write("**방법 1: genai.configure() 사용 불가**")
        st.write("**방법 2: 직접 API 키 전달 시도**")
        try:
            api_key = st.secrets["gemini"]["api_key"]
            
            # 새로운 방식 시도
            if hasattr(genai, 'GenerativeModel'):
                model = genai.GenerativeModel("gemini-pro")
                st.write("✅ GenerativeModel 초기화 성공 (API 키 필요)")
                
                # API 키 설정 방법 확인
                st.write("**API 키 설정 방법:**")
                st.code("""import google.generativeai as genai
api_key = "your-api-key"
model = genai.GenerativeModel("gemini-pro")
# 또는
genai.api_key = api_key
model = genai.GenerativeModel("gemini-pro")
""", language="python")
            else:
                st.error("❌ GenerativeModel을 찾을 수 없습니다")
        except Exception as e:
            st.error(f"❌ 초기화 실패: {e}")

except Exception as e:
    st.error(f"❌ 디버깅 중 오류: {e}")

# 5. 권장 해결 방법
st.subheader("5️⃣ 권장 해결 방법")
st.markdown("""
### 단계별 진행:

1. **패키지 재설치**
   ```bash
   pip uninstall google-generativeai -y
   pip install --upgrade google-generativeai
   ```

2. **Python 버전 확인** (Python 3.8 이상 필요)
   ```bash
   python --version
   ```

3. **최신 API 문법 확인**
   - [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)에서 최신 사용법 확인

4. **올바른 초기화 방법**
   ```python
   import google.generativeai as genai
   
   # 방법 1: API 키 설정
   genai.api_key = "your-api-key"
   model = genai.GenerativeModel("gemini-pro")
   
   # 방법 2: configure 사용 (구버전)
   genai.configure(api_key="your-api-key")
   model = genai.GenerativeModel("gemini-pro")
   ```
""")
