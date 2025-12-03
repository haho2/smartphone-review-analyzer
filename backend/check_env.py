"""
.env 파일 확인 스크립트
"""
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()  # 루트 폴더
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))  # backend 폴더

print("=" * 50)
print("🔍 .env 파일 확인")
print("=" * 50)

# .env 파일 위치 확인
root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
backend_env = os.path.join(os.path.dirname(__file__), '.env')

print(f"\n1️⃣ 루트 폴더 .env: {root_env}")
print(f"   존재 여부: {'✅ 있음' if os.path.exists(root_env) else '❌ 없음'}")

print(f"\n2️⃣ backend 폴더 .env: {backend_env}")
print(f"   존재 여부: {'✅ 있음' if os.path.exists(backend_env) else '❌ 없음'}")

# 환경변수 확인
print("\n" + "=" * 50)
print("📋 환경변수 값 확인")
print("=" * 50)

mongodb_uri = os.getenv('MONGODB_URI', 'NOT_SET')
mongodb_database = os.getenv('MONGODB_DATABASE', 'NOT_SET')
mongodb_collection = os.getenv('MONGODB_COLLECTION', 'NOT_SET')
google_api_key = os.getenv('GOOGLE_API_KEY', 'NOT_SET')

print(f"\nMONGODB_URI: {mongodb_uri[:50]}..." if len(mongodb_uri) > 50 else f"MONGODB_URI: {mongodb_uri}")
print(f"MONGODB_DATABASE: {mongodb_database}")
print(f"MONGODB_COLLECTION: {mongodb_collection}")
print(f"GOOGLE_API_KEY: {'✅ 설정됨' if google_api_key != 'NOT_SET' else '❌ 설정 안 됨'}")

if mongodb_uri == 'NOT_SET' or mongodb_uri == 'mongodb://localhost:27017/':
    print("\n⚠️ MONGODB_URI가 기본값입니다.")
    print("   → .env 파일에 MONGODB_URI를 추가하세요.")
    print("   → 예: MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/")

