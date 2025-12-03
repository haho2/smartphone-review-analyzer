import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 1. 환경변수 로드
load_dotenv()

# .env에서 값 가져오기
MONGO_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
COL_NAME = os.getenv('MONGODB_COLLECTION', 'reviews')

print("--- 📡 MongoDB 연결 테스트 시작 ---")

# 2. URI 확인
if not MONGO_URI:
    print("❌ 오류: .env 파일에서 MONGODB_URI를 찾을 수 없습니다.")
    exit()

print(f"1. 접속 주소 확인: {MONGO_URI[:15]}... (보안상 일부만 표시)")
print(f"2. 타겟 데이터베이스: {DB_NAME}")
print(f"3. 타겟 컬렉션: {COL_NAME}")

try:
    # 3. 클라이언트 연결 시도
    client = MongoClient(MONGO_URI)
    
    # 4. 실제 서버에 Ping 날려보기 (가장 중요!)
    # 이 명령어가 성공해야 진짜 연결된 것임
    client.admin.command('ping')
    print("\n✅ [성공] MongoDB 서버와 연결되었습니다! (Ping Success)")
    
    # 5. 데이터베이스 및 컬렉션 확인
    db = client[DB_NAME]
    collection = db[COL_NAME]
    
    # 6. 테스트 데이터 쓰기/읽기 (선택사항)
    print("   테스트 데이터를 하나 넣었다가 지워볼게요...")
    test_doc = {"test": "connection_check", "status": "ok"}
    
    # 삽입
    insert_result = collection.insert_one(test_doc)
    print(f"   -> 데이터 쓰기 성공! ID: {insert_result.inserted_id}")
    
    # 삭제
    collection.delete_one({"_id": insert_result.inserted_id})
    print("   -> 테스트 데이터 삭제 완료 (Clean up)")
    
    print("\n🎉 모든 테스트를 통과했습니다. app.py를 실행해도 좋습니다.")

except Exception as e:
    print(f"\n❌ [실패] 연결 중 오류가 발생했습니다:\n{str(e)}")
    print("\n[Tip] 오류가 'bad auth'라면 아이디/비번 확인, 'timeout'이라면 IP 허용 설정을 확인하세요.")