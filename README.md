# 한글 맞춤법 및 문장 교정 앱 (Korean Spell & Writing Checker)

AI 기반 한글 맞춤법 검사 및 문장 개선 도구입니다. PDF 파일의 이미지에서 텍스트를 추출한 후, Google Gemini AI를 활용하여 맞춤법과 문장 표현을 교정합니다.

## 🎯 주요 기능

### 1️⃣ **OCR (광학 문자 인식)**
- PDF 파일 업로드
- Google Cloud Vision API를 사용한 고정확도 텍스트 추출

### 2️⃣ **맞춤법 교정** 
- 띄어쓰기 오류 감지 및 수정
- 문법 오류 감지
- 각 문장별 상세 분석

### 3️⃣ **글쓰기 교정**
- 어색한 표현 개선
- 문장 구조 평가
- 더 나은 표현 제안

### 4️⃣ **모달 기반 순차 워크플로우**
- 사용자 친화적인 모달 다이얼로그
- 각 단계별 실시간 편집 가능
- 최종 결과 비교 및 다운로드

---

## 📋 필요한 것들

### Python 환경
- **Python 3.10+**
- **Virtual Environment (권장)**

### API 인증
- **Google Cloud Project** 
  - Vision API 활성화
  - Gemini API 활성화
  - Service Account Key JSON 파일 필요

### 필수 패키지
```bash
pip install -r requirements.txt
```

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 가상환경 생성 (이미 있으면 스킵)
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: Google Cloud 인증 설정

```bash
# 프로젝트 루트에서 다음 파일 확인
ls korean-spelling-app-19e357dc02fa.json

# 환경 변수 설정 (Mac/Linux)
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/korean-spelling-app-19e357dc02fa.json"

# 또는 Streamlit 시크릿으로 설정 (권장)
# .streamlit/secrets.toml에 API 키 추가
```

### 3단계: 앱 실행

```bash
streamlit run main_app.py
```

앱이 브라우저에서 자동으로 열립니다: `http://localhost:8501`

---

## 📁 프로젝트 구조

```
check_spell/
├── README.md                         # 이 파일
├── QUICK_START.md                   # 빠른 시작 가이드
├── MODAL_WORKFLOW_GUIDE.md          # 모달 워크플로우 설명
├── IMPLEMENTATION_SUMMARY.md        # 기술 구현 상세
├── PROJECT_STRUCTURE.md             # 파일 구조 및 용도
│
├── main_app.py                      # 🎯 Streamlit 메인 앱 (실행 파일)
├── requirements.txt                 # Python 의존성
├── korean-spelling-app-19e357dc02fa.json  # Google Cloud 서비스 계정 키
│
├── src/                             # 📦 핵심 모듈
│   ├── vision_ocr.py               # Google Vision OCR 파이프라인
│   ├── json_corrector.py           # Gemini API 호출 (JSON 기반)
│   └── spell_corrector.py          # 맞춤법/글쓰기 교정 통합
│
├── .streamlit/                      # Streamlit 설정
│   └── secrets.toml                 # ⚠️ 로컬 시크릿 (커밋 금지)
│
└── .venv/                           # Python 가상환경 (추적 제외)
```

---

## 💻 사용 방법

### 기본 워크플로우

1. **PDF 업로드**
   - "PDF 선택" 버튼으로 파일 업로드
   - 자동으로 OCR 처리

2. **"글 고쳐쓰기 시작" 클릭**
   - 모달 다이얼로그 오픈
   - 순차 워크플로우 시작

3. **맞춤법 교정** (Stage 1)
   - 원본 텍스트 검토
   - 자동으로 맞춤법 분석
   - 결과 편집 가능
   - "다음 단계로" 클릭

4. **글쓰기 교정** (Stage 2)
   - 맞춤법이 교정된 텍스트 기반
   - 문장 표현 개선
   - 최종 편집 가능
   - "완료" 클릭

5. **최종 결과 확인** (Result)
   - 원본 ↔ 최종본 비교
   - 변경 사항 요약
   - 텍스트 다운로드 가능

---

## 🔧 기술 스택

| 컴포넌트 | 기술 | 버전 |
|---------|------|------|
| **웹 프레임워크** | Streamlit | 최신 |
| **OCR** | Google Cloud Vision API | - |
| **AI** | Google Generative AI (Gemini 2.5-flash) | - |
| **문서 처리** | PyPDF2 | - |
| **언어** | Python | 3.10+ |

---

## 📊 API 의존성

### Google Cloud Vision API
- PDF/이미지 → 텍스트 추출
- 고정확도 한글 인식

### Google Generative AI (Gemini)
- JSON 스키마 기반 구조화된 응답
- 재시도 로직 (exponential backoff)
- 안전한 JSON 파싱

---

## ⚙️ 설정 및 커스터마이징

### 모드별 프롬프트 수정
`src/spell_corrector.py`에서 각 모드의 프롬프트 수정:
```python
SYSTEM_PROMPTS = {
    "맞춤법 교정": "당신은 한글 맞춤법 검사 전문가입니다...",
    "글쓰기 교정": "당신은 문장 표현 개선 전문가입니다...",
    "글 다시 쓰기": "당신은 글쓰기 전문가입니다..."
}
```

### Gemini 모델 변경
`src/json_corrector.py`에서 모델명 수정:
```python
model = client.GenerativeModel("gemini-2.5-flash")  # 다른 모델로 변경 가능
```

---

## 🐛 트러블슈팅

### "Google API 인증 오류"
```bash
# 서비스 계정 키 확인
ls korean-spelling-app-19e357dc02fa.json

# 환경 변수 설정 확인
echo $GOOGLE_APPLICATION_CREDENTIALS
```

### "PDF를 읽을 수 없음"
- PDF 파일이 이미지 기반인지 확인
- 파일 크기 확인 (권장: 10MB 이하)

### "Gemini API 요청 실패"
- 인터넷 연결 확인
- API 配額(할당) 확인
- `src/json_corrector.py`의 재시도 로직 확인

---

## 📚 추가 문서

- **[QUICK_START.md](QUICK_START.md)** - 5분 안에 시작하기
- **[MODAL_WORKFLOW_GUIDE.md](MODAL_WORKFLOW_GUIDE.md)** - 모달 워크플로우 상세 가이드
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - 기술 구현 상세
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 파일 구조 및 정리 가이드
- **[prompt.md](prompt.md)** - 원본 요구사항 명세서

---

## 🤝 기여 방법

1. 기능 요청은 `prompt.md` 업데이트
2. 버그 보고는 코드 주석으로 `# TODO:` 마크
3. 개선 사항은 해당 모듈에서 구현

---

## 📝 라이선스

개인 프로젝트입니다.

---

## 👤 작성자

**Sung Jin Yoo**  
프로젝트 시작: 2025년 11월  
최종 업데이트: 2025년 11월 13일

---

## 🎓 학습 포인트

이 프로젝트에서 배울 수 있는 기술:

- ✅ Streamlit을 사용한 웹 UI 개발
- ✅ Google Cloud API 통합 (Vision, Generative AI)
- ✅ JSON 스키마 기반 구조화된 API 응답 처리
- ✅ 모달 다이얼로그 기반 UX 설계
- ✅ Python 세션 상태 관리 및 재시도 로직
- ✅ PDF 문서 처리 및 OCR 파이프라인

---

**시작하기**: `streamlit run main_app.py` 👈

