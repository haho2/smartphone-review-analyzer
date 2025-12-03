# Project Context: AI-Based Product Review Summarizer

## 1. Project Overview

이 프로젝트는 스마트폰(갤럭시 S25, 아이폰 17 등)의 유튜브 리뷰 영상을 분석하여, 소비자가 구매 결정을 빠르게 내릴 수 있도록 **'핵심 장단점 요약'**과 **'타임스탬프 증거'**를 제공하는 웹 서비스입니다.

## 2. Tech Stack

- **Frontend:** React (Vite), Axios, CSS (Vanilla)
- **Backend:** Python (Flask), Flask-CORS
- **AI Engine:** Google Gemini API (`gemini-pro` or `gemini-1.5-flash`)
- **Data Source:** `youtube-transcript-api` (Video Scripts)
- **Database:** MongoDB (NoSQL for Caching) ✅ **구현 완료**
- **Infra:** AWS Lambda & EventBridge (Planned for Batch processing)

## 3. Current Directory Structure

```
root/
├── backend/
│   ├── app.py              # Flask Main Server (API Endpoints) ✅
│   ├── ai_service.py       # Core Logic (YouTube script fetch + Gemini Analysis) ✅
│   ├── database.py         # MongoDB connection & CRUD logic ✅
│   ├── crawler.py          # (새로 추가된 파일)
│   ├── requirements.txt    # Python dependencies ✅
│   └── .env                # API Keys (GOOGLE_API_KEY, MONGODB_URI...)
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main UI (Input + Result View) ✅
│   │   └── App.css         # Styles ✅
│   └── package.json
└── PROJECT_CONTEXT.md      # 이 파일
```

## 4. Current Development Status

### ✅ 완료된 기능

- **Backend:** Flask 서버가 구축되었으며, `/api/analyze` 엔드포인트를 통해 유튜브 ID를 받으면 스크립트를 추출하고 Gemini로 요약하여 JSON을 반환하는 기능까지 구현 완료.

- **Frontend:** React에서 영상 ID를 입력하고 '분석하기' 버튼을 누르면 백엔드와 통신하여 결과를 화면에 출력하는 프로토타입 구현 완료.

- **AI Logic:** `ai_service.py`에서 `genai.list_models()`를 활용한 동적 모델 선택 및 에러 핸들링 로직 구현 완료.

- **Database Caching:** MongoDB를 사용한 캐싱 레이어 구현 완료
  - `get_review_from_db(video_id)`: 캐시 조회 함수 ✅
  - `save_review_to_db(video_id, analysis_result)`: 캐시 저장 함수 ✅
  - `app.py`에서 요청 시 먼저 DB 확인 → Hit 시 즉시 반환, Miss 시 AI 분석 후 저장 ✅

### 🔄 현재 상태

- MongoDB 연결 성공 ✅
- 캐싱 기능 정상 작동 확인 ✅
- 유튜브 자막 요약 기능 정상 작동 확인 ✅

## 5. Next Steps (To-Do)

### [Goal 1: 크롤링 기능 확장]

현재는 수동으로 영상 ID를 입력받고 있지만, 다음 기능들을 추가할 수 있습니다:

**Requirements:**

1. 유튜브 검색 API 또는 웹 크롤링을 통한 영상 자동 검색
   - 키워드 입력 (예: "갤럭시 S25 리뷰")
   - 관련 영상 목록 반환
   - 사용자가 선택한 영상 분석

2. 배치 처리 기능
   - 여러 영상 ID를 한 번에 분석
   - CSV 파일 업로드로 대량 처리

### [Goal 2: 프론트엔드 UI 개선]

**Requirements:**

1. 분석 결과 시각화
   - 장점/단점을 카드 형태로 표시
   - 타임스탬프를 클릭하면 해당 시간으로 이동하는 링크 제공
   - 차트/그래프로 요약 정보 시각화

2. 검색 기능 추가
   - 유튜브 검색 통합
   - 최근 분석한 영상 목록 표시
   - 즐겨찾기 기능

### [Goal 3: AWS Lambda & EventBridge 배치 처리]

**Requirements:**

1. AWS Lambda 함수 생성
   - 주기적으로 인기 영상 분석
   - EventBridge로 스케줄링

2. DynamoDB 또는 MongoDB Atlas를 통한 결과 저장
   - 이미 MongoDB 구현 완료 ✅

### [Goal 4: 추가 기능]

**Requirements:**

1. 분석 결과 비교 기능
   - 여러 제품/영상 비교
   - 차이점 하이라이트

2. 사용자 피드백 수집
   - 분석 결과 정확도 평가
   - 개선 사항 제안

3. 알림 기능
   - 특정 키워드로 새 영상이 올라오면 알림
   - 분석 완료 알림

## 6. API Endpoints

### 현재 구현된 엔드포인트

- `GET /` - 서버 상태 확인
- `POST /api/analyze` - 영상 분석 요청
  ```json
  {
    "video_id": "sCffhYaBP4s"
  }
  ```
  Response:
  ```json
  {
    "video_id": "sCffhYaBP4s",
    "analysis": "AI 분석 결과 텍스트...",
    "cached": false
  }
  ```

### 추가 가능한 엔드포인트

- `GET /api/search?q=갤럭시+S25` - 유튜브 검색
- `POST /api/batch` - 배치 분석
- `GET /api/history` - 분석 이력 조회
- `GET /api/stats` - 통계 정보

## 7. Database Schema

### MongoDB Collection: `reviews`

```javascript
{
  "_id": ObjectId("..."),
  "video_id": "sCffhYaBP4s",
  "analysis": "AI 분석 결과 텍스트...",
  "created_at": 1234567890,
  "updated_at": 1234567890
}
```

**Index:**
- `video_id` (unique)

## 8. Environment Variables

`.env` 파일 예시:

```env
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# MongoDB 설정
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=youtube_reviews_db
MONGODB_COLLECTION=reviews
```

## 9. 실행 방법

### Backend
```bash
cd backend
python app.py
```

### Frontend
```bash
cd frontend
npm run dev
```

### 테스트
```bash
# MongoDB 연결 테스트
python backend/test_database.py

# 전체 시스템 테스트
# 1. 백엔드 서버 실행
# 2. 프론트엔드 실행
# 3. 브라우저에서 http://localhost:5173 접속
# 4. 영상 ID 입력 후 분석
```

## 10. 참고 자료

- MongoDB Atlas: https://www.mongodb.com/cloud/atlas
- Google Gemini API: https://ai.google.dev/
- YouTube Transcript API: https://github.com/jdepoix/youtube-transcript-api

