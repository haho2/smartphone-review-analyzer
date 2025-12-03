# MongoDB 설정 가이드

## 방법 1: Docker 사용 (가장 간단, 권장)

### 1. Docker 설치 확인
```powershell
docker --version
```

### 2. MongoDB 컨테이너 실행
```powershell
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. 실행 확인
```powershell
docker ps
```

### 4. 중지/삭제
```powershell
# 중지
docker stop mongodb

# 삭제
docker rm mongodb
```

---

## 방법 2: MongoDB Community Server 설치

### 1. 다운로드
- https://www.mongodb.com/try/download/community
- Windows용 MSI 설치 파일 다운로드

### 2. 설치
- 설치 마법사 따라하기
- "Install MongoDB as a Service" 옵션 선택 (자동 시작)

### 3. 서비스 확인
```powershell
# Windows 서비스에서 MongoDB 확인
services.msc
```

### 4. 수동 시작 (필요 시)
```powershell
net start MongoDB
```

---

## 방법 3: MongoDB Atlas (클라우드, 무료)

### 1. 계정 생성
- https://www.mongodb.com/cloud/atlas 접속
- 무료 계정 생성

### 2. 클러스터 생성
- M0 (무료) 티어 선택
- 리전: Seoul (ap-northeast-2)

### 3. 데이터베이스 사용자 생성
- Database Access → Add New Database User
- Username/Password 설정

### 4. 네트워크 접근 설정
- Network Access → Add IP Address
- "Allow Access from Anywhere" (0.0.0.0/0) 선택

### 5. 연결 문자열 복사
- Connect → Connect your application
- Connection String 복사
- 예: `mongodb+srv://username:password@cluster.mongodb.net/`

### 6. .env 파일 설정
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=youtube_reviews_db
MONGODB_COLLECTION=reviews
```

---

## 테스트

설치 후 다음 명령어로 테스트:
```powershell
cd backend
python test_database.py
```

또는 백엔드 서버 실행 시 연결 메시지 확인:
```powershell
python app.py
```

