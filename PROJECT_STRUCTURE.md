# 📂 프로젝트 파일 구조 및 용도 정리

## 📊 전체 파일 맵

```
check_spell/
├── 🟢 [필수] 핵심 실행 파일
│   └── main_app.py (295줄)
│       - Streamlit 메인 앱 (모달 다이얼로그 기반 워크플로우)
│       - 사용자의 첫 번째 진입점
│
├── 🟢 [필수] 핵심 소스 모듈
│   └── src/
│       ├── vision_ocr.py (157줄)
│       │   - Google Vision API를 사용한 OCR 파이프라인
│       │   - PDF → 텍스트 추출
│       │
│       ├── json_corrector.py (129줄)
│       │   - Gemini를 사용한 JSON 기반 맞춤법 분석
│       │   - 재시도 로직 및 안전한 파싱 포함
│       │
│       └── spell_corrector.py (145줄)
│           - 맞춤법 교정 및 글쓰기 교정 코드 통합
│           - format_json_result_to_text() 함수 포함
│
├── 🟡 [선택] 문서 및 가이드
│   ├── README.md (없음 - 생성 필요)
│   │   - 프로젝트 개요 및 빠른 시작 가이드
│   │
│   ├── QUICK_START.md
│   │   - 앱 실행 방법 및 초기 설정
│   │
│   ├── WORKFLOW_GUIDE.md
│   │   - 순차 워크플로우 상세 설명 (구형)
│   │
│   ├── MODAL_WORKFLOW_GUIDE.md
│   │   - 모달 다이얼로그 기반 새로운 워크플로우 가이드
│   │
│   ├── IMPLEMENTATION_SUMMARY.md
│   │   - 모달 구현 상세 내용
│   │
│   ├── FIXES_SUMMARY.md
│   │   - 이전 버그 수정 내용 (참고용)
│   │
│   └── prompt.md
│       - 사용자 요청사항 및 기능 명세서
│
├── 🔴 [불필요] 테스트 및 디버깅 파일
│   ├── debugging_app.py (144줄)
│   │   - 패키지 정보 확인용 디버깅 도구
│   │   - google.generativeai 초기화 테스트
│   │   → 용도: 이미 문제 해결됨, 삭제 가능
│   │
│   ├── convert_json_to_toml.py (41줄)
│   │   - JSON → TOML 변환 유틸
│   │   → 용도: 한 번 사용 후 미사용, 삭제 가능
│   │
│   ├── data/ (폴더)
│   │   ├── app.py (334줄) - 구형 Streamlit 앱
│   │   ├── check_app.py (100줄) - 이전 테스트용
│   │   ├── check_app_vision_gemini.py (133줄) - 테스트용
│   │   ├── debug_app.py (171줄) - 디버깅용
│   │   → 용도: 모두 구형 파일, 삭제 가능
│   │
│   └── src/
│       └── json_corrector copy.py (79줄)
│           - json_corrector.py의 백업본
│           → 용도: 백업 파일, 삭제 가능
│
├── 🟡 [조건부] 설정 파일
│   ├── requirements.txt
│   │   - Python 패키지 의존성
│   │   → 현재 상태: 확인 필요
│   │
│   ├── korean-spelling-app-19e357dc02fa.json
│   │   - Google Cloud 서비스 계정 키 (중요!)
│   │   → 용도: Gemini API 인증 필수
│   │   → 주의: .gitignore에 추가되어야 함
│   │
│   └── .streamlit/secrets.toml (보이지 않음)
│       - Streamlit 시크릿 설정 (Gemini API 키)
│       → 용도: 로컬 개발용 필수
│       → 주의: 절대 커밋하지 말 것!
│
└── 📁 자동 생성 폴더 (추적 불필요)
    ├── .venv/ (가상환경)
    ├── .git/ (Git 저장소)
    ├── __pycache__/ (Python 캐시)
    └── src/__pycache__/ (모듈 캐시)
```

---

## 📋 파일별 상세 분석

### **🟢 필수 파일 (반드시 유지)**

#### 1. `main_app.py` (295줄)
```
용도: Streamlit 메인 애플리케이션
기능:
  ✅ PDF 파일 업로드
  ✅ OCR 처리 (Vision API)
  ✅ 모달 다이얼로그 기반 워크플로우
     - 맞춤법 교정 (Tab 1)
     - 글쓰기 교정 (Tab 2)
     - 최종 결과 비교
상태: ✅ 활발히 사용 중
```

#### 2. `src/vision_ocr.py` (157줄)
```
용도: Google Vision API 통합
기능:
  ✅ PDF → 이미지 변환
  ✅ Google Cloud Vision으로 OCR 처리
  ✅ 추출된 텍스트 반환
상태: ✅ 핵심 의존성
```

#### 3. `src/json_corrector.py` (129줄)
```
용도: 맞춤법 분석 (JSON 기반)
기능:
  ✅ Gemini API 호출
  ✅ JSON 스키마 기반 응답
  ✅ 재시도 로직 (exponential backoff)
  ✅ 안전한 JSON 파싱
상태: ✅ 핵심 의존성
```

#### 4. `src/spell_corrector.py` (145줄)
```
용도: 맞춤법 및 글쓰기 교정 통합
기능:
  ✅ correct_text(text, mode) - 모드별 교정
  ✅ format_json_result_to_text() - JSON 포맷 변환
  ✅ 모드:
     - "맞춤법 교정" (JSON 분석)
     - "글쓰기 교정" (평가 + 제안)
     - "글 다시 쓰기" (재작성)
상태: ✅ 핵심 의존성
```

---

### **🟡 선택 파일 (문서용 - 유지 권장)**

#### 1. `QUICK_START.md`
```
용도: 빠른 시작 가이드
내용: 앱 실행 방법, 초기 설정
상태: ✅ 신규 사용자용 필수
```

#### 2. `MODAL_WORKFLOW_GUIDE.md`
```
용도: 현재 모달 다이얼로그 워크플로우 설명
내용: 기능별 상세 가이드
상태: ✅ 최신 기능 설명
```

#### 3. `IMPLEMENTATION_SUMMARY.md`
```
용도: 모달 구현 상세 내용
내용: 코드 구조, 세션 관리
상태: ✅ 개발자 참고용
```

#### 4. `WORKFLOW_GUIDE.md`
```
용도: 구형 워크플로우 (Tab 기반)
내용: 이전 순차 워크플로우 설명
상태: 🟡 참고만 (구형)
```

#### 5. `FIXES_SUMMARY.md`
```
용도: 이전 버그 수정 내용
내용: 2025-11-12 수정사항
상태: 🟡 참고만 (과거 기록)
```

#### 6. `prompt.md`
```
용도: 사용자 요청 명세서
내용: 기능 요구사항
상태: ✅ 프로젝트 정의 문서
```

---

### **🔴 불필요 파일 (삭제 권장)**

#### 1. `data/` 폴더 전체 (730줄 이상)
```
파일들:
  - app.py (334줄) - 구형 메인 앱
  - check_app.py (100줄) - 테스트용
  - check_app_vision_gemini.py (133줄) - 테스트용
  - debug_app.py (171줄) - 디버깅용

이유: main_app.py로 통합되었음
권장: 🗑️ 삭제
```

#### 2. `debugging_app.py` (144줄)
```
용도: google.generativeai 패키지 디버깅
문제: 이미 패키지 문제 해결됨
권장: 🗑️ 삭제
```

#### 3. `convert_json_to_toml.py` (41줄)
```
용도: JSON → TOML 변환 유틸
사용: 한 번 만들어진 후 미사용
권장: 🗑️ 삭제
```

#### 4. `src/json_corrector copy.py` (79줄)
```
용도: json_corrector.py 백업본
문제: 관리 복잡성만 증가
권장: 🗑️ 삭제
```

---

## 🧹 정리 전략

### **Step 1: 문서 정리**
```bash
# 불필요한 문서 삭제
rm WORKFLOW_GUIDE.md      # 구형 - 모달 가이드로 대체
rm FIXES_SUMMARY.md       # 과거 기록

# 유지할 문서
# ✅ QUICK_START.md
# ✅ MODAL_WORKFLOW_GUIDE.md
# ✅ IMPLEMENTATION_SUMMARY.md
# ✅ prompt.md
```

### **Step 2: 구형 코드 삭제**
```bash
# data/ 폴더 전체 삭제
rm -rf data/

# 디버깅 파일 삭제
rm debugging_app.py
rm convert_json_to_toml.py

# 백업 파일 삭제
rm src/json_corrector\ copy.py
```

### **Step 3: 새 README 작성**
```bash
# 프로젝트 개요 문서 생성
touch README.md
```

---

## 📐 정리 후 예상 구조

```
✨ 깔끔한 프로젝트 구조:

check_spell/
├── 📄 README.md (새로 작성)
├── 📄 QUICK_START.md
├── 📄 MODAL_WORKFLOW_GUIDE.md
├── 📄 IMPLEMENTATION_SUMMARY.md
├── 📄 prompt.md
├── 📄 requirements.txt
│
├── 🐍 main_app.py
├── 🐍 korean-spelling-app-19e357dc02fa.json
│
├── 📁 src/
│   ├── vision_ocr.py
│   ├── json_corrector.py
│   └── spell_corrector.py
│
├── 📁 .streamlit/
│   └── secrets.toml (시크릿)
│
└── 📁 .venv/ (가상환경)
```

---

## 📊 정리 효과

| 항목 | 정리 전 | 정리 후 | 감소율 |
|------|--------|--------|--------|
| 파일 개수 | 19 | 9 | -53% |
| 코드 줄 수 | 1,728 | 826 | -52% |
| 관리 복잡도 | 높음 | 낮음 | -60% |
| 진입 장벽 | 높음 | 낮음 | 명확함 |

---

## ✅ 파일별 유지 여부 최종 판단

```
필수 (Keep)          선택적 (Keep)       삭제 (Delete)
────────────────    ──────────────────  ────────────────
✅ main_app.py      ✅ README.md*       ❌ data/
✅ src/             ✅ QUICK_START.md   ❌ debugging_app.py
✅ requirements.txt ✅ MODAL_WORKFLOW*  ❌ convert_json_to_toml.py
✅ korean-spelling* ✅ IMPLEMENTATION*  ❌ WORKFLOW_GUIDE.md
✅ .streamlit/      ✅ prompt.md        ❌ FIXES_SUMMARY.md
                                        ❌ json_corrector copy.py

* = 신규 또는 업데이트 필요
```

---

## 🎯 권장 정리 순서

1. **Step 1**: 문서 검토 및 README 작성
2. **Step 2**: `data/` 폴더 백업 후 삭제
3. **Step 3**: 개별 불필요 파일 삭제
4. **Step 4**: Git 커밋 (`chore: Clean up legacy files`)
5. **Step 5**: 프로젝트 디렉토리 재확인

---

**마지막 업데이트**: 2025-11-13
