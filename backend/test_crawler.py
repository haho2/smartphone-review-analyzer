"""
커뮤니티 크롤링 기능 테스트 스크립트
"""
import crawler
import sys

# Windows에서 UTF-8 출력을 위한 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_community_crawler():
    """커뮤니티 크롤링 테스트"""
    print("=" * 50)
    print("🧪 커뮤니티 크롤링 테스트")
    print("=" * 50)
    
    test_keywords = ["갤럭시 S25", "아이폰17"]
    
    for keyword in test_keywords:
        print(f"\n📱 테스트 키워드: {keyword}")
        print("-" * 50)
        
        try:
            result = crawler.crawl_community_reviews(keyword)
            
            if result and "가져오지 못했습니다" not in result:
                print(f"\n✅ 성공!")
                review_count = len(result.split('\n'))
                print(f"수집된 후기 수: {review_count}개")
                print(f"\n처음 500자 미리보기:")
                print(result[:500])
                if len(result) > 500:
                    print("...")
            else:
                print(f"\n❌ 실패: {result}")
                
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    test_community_crawler()

