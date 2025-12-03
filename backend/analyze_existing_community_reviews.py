"""
기존 커뮤니티 후기에 대해 AI 분석을 수행하고 DB에 저장하는 스크립트
"""
import sys
import product_normalizer
import ai_service
from batch_crawler import save_community_analysis_to_db, get_community_reviews_from_db

# Windows에서 UTF-8 출력을 위한 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_existing_reviews():
    """기존 커뮤니티 후기에 대해 분석 수행"""
    print("🚀 기존 커뮤니티 후기 분석 시작\n")
    
    # VALID_MODELS의 모든 제품에 대해 분석 수행
    products = product_normalizer.VALID_MODELS
    
    success_count = 0
    fail_count = 0
    
    for product_name in products:
        print(f"\n{'='*60}")
        print(f"📱 제품 분석: {product_name}")
        print(f"{'='*60}")
        
        # DB에서 커뮤니티 후기 조회
        result = get_community_reviews_from_db(product_name)
        
        if len(result) == 3:
            reviews_text, sources, cached_analysis = result
        else:
            reviews_text, sources = result[:2]
            cached_analysis = None
        
        if not reviews_text:
            print(f"   ⚠️ 커뮤니티 후기가 없습니다. 스킵합니다.")
            fail_count += 1
            continue
        
        # 이미 분석 결과가 있으면 스킵
        if cached_analysis:
            print(f"   ⚡ 이미 분석 결과가 있습니다. 스킵합니다.")
            success_count += 1
            continue
        
        # AI 분석 수행
        print(f"   🤖 AI 분석 시작...")
        try:
            analysis = ai_service.analyze_community_reviews_with_gemini(reviews_text)
            
            if isinstance(analysis, str) and analysis.startswith("❌"):
                print(f"      ❌ 분석 실패: {analysis}")
                fail_count += 1
            else:
                # 분석 결과 저장
                save_community_analysis_to_db(product_name, analysis)
                print(f"      ✅ 분석 완료 및 저장")
                success_count += 1
        except Exception as e:
            print(f"      ❌ 오류 발생: {str(e)}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ 완료: {success_count}개 성공, ❌ 실패: {fail_count}개")
    print(f"{'='*60}")

if __name__ == "__main__":
    analyze_existing_reviews()

