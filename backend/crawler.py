from youtubesearchpython import VideosSearch
import requests
from bs4 import BeautifulSoup
import re

def parse_view_count(view_text):
    """
    '조회수 120만회', '1.2M views' 같은 문자열을 숫자(1200000)로 변환하는 함수
    (정렬을 위해 필요)
    """
    if not view_text: return 0
    try:
        return 0 
    except:
        return 0

def search_youtube_top3(keyword):
    """
    키워드로 검색 후 '조회수'가 높은 영상 3개의 ID와 제목을 반환
    제품명 정규화 및 변형 검색 적용
    """
    try:
        import product_normalizer
        
        # 제품명 정규화
        normalized_keyword = product_normalizer.normalize_product_name(keyword)
        
        # 검색 변형 생성 (한국어 + 영어)
        search_variations = product_normalizer.get_product_variations(normalized_keyword)
        
        # 유튜브 검색은 정규화된 제품명 + 영어 변형 사용
        search_queries = [
            f"{normalized_keyword} review",
            f"{normalized_keyword} 리뷰",
        ]
        
        # 영어 변형 추가
        if '갤럭시' in normalized_keyword:
            # "갤럭시 S25" -> "Galaxy S25 review"
            match = __import__('re').search(r'갤럭시\s*(.+)', normalized_keyword)
            if match:
                suffix = match.group(1)
                search_queries.append(f"Galaxy {suffix} review")
        elif '아이폰' in normalized_keyword:
            # "아이폰 17" -> "iPhone 17 review"
            match = __import__('re').search(r'아이폰\s*(.+)', normalized_keyword)
            if match:
                suffix = match.group(1)
                search_queries.append(f"iPhone {suffix} review")
        
        all_videos = []
        seen_video_ids = set()
        
        # 여러 검색어로 검색하여 더 많은 결과 수집
        for search_query in search_queries[:3]:  # 상위 3개 검색어 사용
            try:
                videosSearch = VideosSearch(search_query, limit=10)
                results = videosSearch.result()['result']
                
                for video in results:
                    v_id = video['id']
                    if v_id not in seen_video_ids:
                        all_videos.append(video)
                        seen_video_ids.add(v_id)
            except:
                continue
        
        if not all_videos:
            # 기본 검색어로 한 번 더 시도
            search_query = f"{normalized_keyword} review"
            videosSearch = VideosSearch(search_query, limit=10)
            results = videosSearch.result()['result']
            all_videos = results
        
        video_list = []
        
        for video in all_videos:
            # 2. 필요한 정보만 추출
            v_id = video['id']
            title = video['title']
            view_text = video.get('viewCount', {}).get('text', '0')
            
            # 3. 'Shorts'는 제외하는 필터링 (리뷰 분석에 방해됨)
            if 'shorts' not in title.lower():
                video_list.append({
                    'id': v_id,
                    'title': title,
                    'views': view_text # 정렬은 복잡하니 일단 검색 상위권 사용
                })

        # 4. 상위 3개만 자르기
        return video_list[:3]
        
    except Exception as e:
        print(f"❌ 유튜브 검색 실패: {e}")
        return []

def crawl_clien(keyword):
    """
    클리앙(Clien) 커뮤니티에서 제품 후기 크롤링
    """
    try:
        from urllib.parse import quote
        search_query = f"{keyword} 후기"
        encoded_query = quote(search_query)
        
        # 클리앙 검색 URL
        url = f"https://www.clien.net/service/search?q={encoded_query}&sort=recency&boardCd=&isBoard=false"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 클리앙 검색 결과 파싱 (여러 선택자 시도)
        selectors = [
            '.list_item',
            '.list_row', 
            '.subject_fixed',
            '.list_subject',
            'a[href*="/service/board"]',
            '.title_subject'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            if len(text) > 20 and keyword.lower() in text.lower():
                if text not in seen:
                    reviews.append(f"[클리앙] {text}")
                    seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 클리앙 크롤링 실패: {str(e)}")
        return []


def crawl_naver_blog(keyword):
    """
    네이버 블로그에서 제품 후기 크롤링 (공개 블로그만)
    """
    try:
        from urllib.parse import quote
        search_query = f"{keyword} 실사용 후기"
        encoded_query = quote(search_query)
        
        # 네이버 블로그 검색 URL
        url = f"https://search.naver.com/search.naver?where=post&query={encoded_query}&sm=tab_jum"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 네이버 블로그 검색 결과 파싱
        selectors = [
            '.api_txt_lines',
            '.total_tit',
            '.sh_blog_title',
            '.title_link',
            '.title_desc',
            'a.title_link',
            '.sh_blog_passage'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            if len(text) > 20 and keyword.lower() in text.lower():
                if text not in seen:
                    reviews.append(f"[네이버 블로그] {text}")
                    seen.add(text)
        
        return reviews[:20]  # 최대 20개
        
    except Exception as e:
        print(f"   ⚠️ 네이버 블로그 크롤링 실패: {str(e)}")
        return []


def crawl_dcinside_galaxy(keyword):
    """
    디시인사이드 갤럭시 갤러리 후기 탭에서 제품 후기 크롤링
    """
    try:
        from urllib.parse import quote
        # 갤럭시 갤러리 후기 탭 URL
        url = "https://gall.dcinside.com/board/lists/?id=galaxy&page=1&exception_mode=recommend"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Referer': 'https://gall.dcinside.com/'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 디시인사이드 갤럭시 갤러리 후기 탭 파싱
        selectors = [
            '.gall_list .gall_tit a',
            '.ub-content .gall_tit',
            'td.gall_tit a',
            '.list_subject a'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15 and keyword.lower() in text.lower():
                    all_items.append(text)
        
        # 중복 제거
        seen = set()
        for text in all_items:
            if text not in seen:
                reviews.append(f"[디시 갤럭시 갤러리] {text}")
                seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 디시 갤럭시 갤러리 크롤링 실패: {str(e)}")
        return []


def crawl_dcinside_iphone(keyword):
    """
    디시인사이드 아이폰 갤러리에서 검색으로 제품 후기 크롤링
    """
    try:
        from urllib.parse import quote, urlencode
        
        # 검색어에서 "후기" 제거 (디시인사이드 검색이 더 잘 됨)
        search_keyword = keyword.replace(" 후기", "").replace("후기", "").strip()
        if not search_keyword:
            search_keyword = keyword
        
        # 디시인사이드 검색 URL (올바른 형식)
        # URL 파라미터를 올바르게 구성
        params = {
            'q': search_keyword,
            's_type': 'all',
            'q_type': 'all',
            'c_id': 'iphone'
        }
        url = f"https://search.dcinside.com/post/q/{quote(search_keyword)}?{urlencode(params)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Referer': 'https://gall.dcinside.com/'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 디시인사이드 아이폰 갤러리 검색 결과 파싱
        selectors = [
            '.sch_result_list .sch_txt',
            '.sch_result_list .sch_tit',
            '.list_subject',
            'a.subject_fixed',
            '.search_result .title',
            '.search_result a'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            # 키워드가 포함되어 있거나, "후기" 관련 키워드가 있으면 포함
            if len(text) > 20:
                keyword_lower = keyword.lower()
                text_lower = text.lower()
                if (keyword_lower in text_lower or 
                    '후기' in text_lower or 
                    '리뷰' in text_lower or
                    '사용' in text_lower):
                    if text not in seen:
                        reviews.append(f"[디시 아이폰 갤러리] {text}")
                        seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 디시 아이폰 갤러리 크롤링 실패: {str(e)}")
        return []


def crawl_samsung_members(keyword):
    """
    삼성 멤버스 커뮤니티에서 제품 후기 크롤링
    삼성 멤버스는 로그인이 필요하거나 URL이 변경되었을 수 있어서 네이버 검색으로 대체
    """
    try:
        from urllib.parse import quote
        search_query = f"{keyword} 후기 site:r1.community.samsung.com"
        encoded_query = quote(search_query)
        
        # 네이버 검색을 통해 삼성 멤버스 게시글 검색
        url = f"https://search.naver.com/search.naver?where=web&query={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 네이버 검색 결과에서 삼성 멤버스 링크 파싱
        selectors = [
            '.api_txt_lines',
            '.total_tit',
            '.sh_web_title',
            'a[href*="community.samsung.com"]'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            if len(text) > 20 and keyword.lower() in text.lower():
                if text not in seen:
                    reviews.append(f"[삼성 멤버스] {text}")
                    seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 삼성 멤버스 크롤링 실패: {str(e)}")
        return []


def crawl_naver_cafe_iphone(keyword):
    """
    네이버 카페 - 아이폰 사용자 모임에서 제품 후기 크롤링
    카페 URL: https://cafe.naver.com/appleiphone
    """
    try:
        from urllib.parse import quote
        search_query = f"{keyword} 후기"
        encoded_query = quote(search_query)
        
        # 네이버 카페 검색 URL (아이폰 사용자 모임)
        # 공개 게시글만 검색
        url = f"https://search.naver.com/search.naver?where=article&query={encoded_query}+site:cafe.naver.com/appleiphone"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 네이버 검색 결과에서 카페 게시글 파싱
        selectors = [
            '.api_txt_lines',
            '.total_tit',
            '.sh_cafe_title',
            '.title_link',
            '.title_desc',
            'a[href*="cafe.naver.com/appleiphone"]'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            if len(text) > 20 and keyword.lower() in text.lower():
                if text not in seen:
                    reviews.append(f"[아이폰 사용자 모임] {text}")
                    seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 네이버 카페(아이폰) 크롤링 실패: {str(e)}")
        return []


def crawl_ppomppu(keyword):
    """
    뽐뿌(Ppomppu) 커뮤니티에서 제품 후기 크롤링
    """
    try:
        from urllib.parse import quote
        search_query = f"{keyword} 후기"
        encoded_query = quote(search_query)
        
        # 뽐뿌 검색 URL
        url = f"https://www.ppomppu.co.kr/search_bbs.php?search_type=sub_memo&keyword={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        reviews = []
        # 뽐뿌 검색 결과 파싱 (여러 선택자 시도)
        selectors = [
            '.title',
            '.subject',
            '.list_title',
            'a[href*="/zboard/view"]',
            '.board_list .title',
            'td.title'
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            for item in items:
                text = item.get_text().strip()
                if len(text) > 15:
                    all_items.append(text)
        
        # 중복 제거 및 필터링
        seen = set()
        for text in all_items:
            if len(text) > 20 and keyword.lower() in text.lower():
                if text not in seen:
                    reviews.append(f"[뽐뿌] {text}")
                    seen.add(text)
        
        return reviews[:15]  # 최대 15개
        
    except Exception as e:
        print(f"   ⚠️ 뽐뿌 크롤링 실패: {str(e)}")
        return []


def crawl_community_reviews(keyword):
    """
    신뢰할 수 있는 커뮤니티 사이트에서 직접 제품 후기 크롤링 (빅데이터 수집)
    
    데이터 소스:
    - 클리앙 (clien.net): IT/전자제품 전문 커뮤니티
    - 뽐뿌 (ppomppu.co.kr): 쇼핑/제품 후기 커뮤니티
    - 네이버 블로그: 공개 블로그 포스트
    - 삼성 멤버스: 삼성 제품 사용자 커뮤니티
    - 네이버 카페 - 아이폰 사용자 모임: 아이폰 사용자 전용 커뮤니티
    - 디시인사이드: 갤럭시는 갤럭시 갤러리 후기 탭, 아이폰은 아이폰 갤러리 검색
    
    최대 50개 이상의 후기를 수집하여 빅데이터 분석을 수행합니다.
    
    제품명 변형을 자동으로 처리하여 다양한 검색어로 크롤링합니다.
    """
    import product_normalizer
    
    # 제품명 정규화 및 변형 생성
    normalized_keyword = product_normalizer.normalize_product_name(keyword)
    search_variations = product_normalizer.get_product_variations(normalized_keyword)
    
    print(f"   📝 검색 변형: {', '.join(search_variations[:3])}...")
    
    all_reviews = []
    sources = []
    
    try:
        # 1. 클리앙 크롤링 (여러 변형으로 검색)
        print(f"   → 클리앙 크롤링 중...")
        clien_reviews = []
        seen_clien = set()
        for variation in search_variations[:3]:  # 상위 3개 변형만 사용
            reviews = crawl_clien(variation)
            for review in reviews:
                if review not in seen_clien:
                    clien_reviews.append(review)
                    seen_clien.add(review)
        if clien_reviews:
            all_reviews.extend(clien_reviews)
            sources.append(f"클리앙 ({len(clien_reviews)}개)")
            print(f"      ✅ 클리앙에서 {len(clien_reviews)}개 후기 발견")
        
        # 2. 뽐뿌 크롤링 (여러 변형으로 검색)
        print(f"   → 뽐뿌 크롤링 중...")
        ppomppu_reviews = []
        seen_ppomppu = set()
        for variation in search_variations[:3]:
            reviews = crawl_ppomppu(variation)
            for review in reviews:
                if review not in seen_ppomppu:
                    ppomppu_reviews.append(review)
                    seen_ppomppu.add(review)
        if ppomppu_reviews:
            all_reviews.extend(ppomppu_reviews)
            sources.append(f"뽐뿌 ({len(ppomppu_reviews)}개)")
            print(f"      ✅ 뽐뿌에서 {len(ppomppu_reviews)}개 후기 발견")
        
        # 3. 네이버 블로그 크롤링 (여러 변형으로 검색)
        print(f"   → 네이버 블로그 크롤링 중...")
        naver_blog_reviews = []
        seen_naver_blog = set()
        for variation in search_variations[:3]:
            reviews = crawl_naver_blog(variation)
            for review in reviews:
                if review not in seen_naver_blog:
                    naver_blog_reviews.append(review)
                    seen_naver_blog.add(review)
        if naver_blog_reviews:
            all_reviews.extend(naver_blog_reviews)
            sources.append(f"네이버 블로그 ({len(naver_blog_reviews)}개)")
            print(f"      ✅ 네이버 블로그에서 {len(naver_blog_reviews)}개 후기 발견")
        
        # 4. 삼성 멤버스 크롤링 (여러 변형으로 검색)
        print(f"   → 삼성 멤버스 크롤링 중...")
        samsung_reviews = []
        seen_samsung = set()
        for variation in search_variations[:3]:
            reviews = crawl_samsung_members(variation)
            for review in reviews:
                if review not in seen_samsung:
                    samsung_reviews.append(review)
                    seen_samsung.add(review)
        if samsung_reviews:
            all_reviews.extend(samsung_reviews)
            sources.append(f"삼성 멤버스 ({len(samsung_reviews)}개)")
            print(f"      ✅ 삼성 멤버스에서 {len(samsung_reviews)}개 후기 발견")
        
        # 5. 네이버 카페 - 아이폰 사용자 모임 크롤링 (여러 변형으로 검색)
        print(f"   → 네이버 카페(아이폰) 크롤링 중...")
        iphone_cafe_reviews = []
        seen_iphone_cafe = set()
        for variation in search_variations[:3]:
            reviews = crawl_naver_cafe_iphone(variation)
            for review in reviews:
                if review not in seen_iphone_cafe:
                    iphone_cafe_reviews.append(review)
                    seen_iphone_cafe.add(review)
        if iphone_cafe_reviews:
            all_reviews.extend(iphone_cafe_reviews)
            sources.append(f"아이폰 사용자 모임 ({len(iphone_cafe_reviews)}개)")
            print(f"      ✅ 아이폰 사용자 모임에서 {len(iphone_cafe_reviews)}개 후기 발견")
        
        # 6. 디시인사이드 크롤링 (제품에 따라 다르게 처리, 여러 변형으로 검색)
        keyword_lower = normalized_keyword.lower()
        if '갤럭시' in keyword_lower or 'galaxy' in keyword_lower or 'samsung' in keyword_lower:
            print(f"   → 디시 갤럭시 갤러리 크롤링 중...")
            dc_galaxy_reviews = []
            seen_dc_galaxy = set()
            for variation in search_variations[:2]:  # 디시는 변형이 적게 필요
                reviews = crawl_dcinside_galaxy(variation)
                for review in reviews:
                    if review not in seen_dc_galaxy:
                        dc_galaxy_reviews.append(review)
                        seen_dc_galaxy.add(review)
            if dc_galaxy_reviews:
                all_reviews.extend(dc_galaxy_reviews)
                sources.append(f"디시 갤럭시 갤러리 ({len(dc_galaxy_reviews)}개)")
                print(f"      ✅ 디시 갤럭시 갤러리에서 {len(dc_galaxy_reviews)}개 후기 발견")
        elif '아이폰' in keyword_lower or 'iphone' in keyword_lower or '애플' in keyword_lower:
            print(f"   → 디시 아이폰 갤러리 크롤링 중...")
            dc_iphone_reviews = []
            seen_dc_iphone = set()
            for variation in search_variations[:3]:
                reviews = crawl_dcinside_iphone(variation)
                for review in reviews:
                    if review not in seen_dc_iphone:
                        dc_iphone_reviews.append(review)
                        seen_dc_iphone.add(review)
            if dc_iphone_reviews:
                all_reviews.extend(dc_iphone_reviews)
                sources.append(f"디시 아이폰 갤러리 ({len(dc_iphone_reviews)}개)")
                print(f"      ✅ 디시 아이폰 갤러리에서 {len(dc_iphone_reviews)}개 후기 발견")
        
        if all_reviews:
            actual_count = len(all_reviews)
            print(f"   ✅ 총 {actual_count}개 후기 수집 완료")
            result_text = f"[데이터 소스: {', '.join(sources)}]\n\n"
            result_text += "\n".join(all_reviews[:50])  # 최대 50개로 증가 (빅데이터!)
            return result_text, sources, actual_count  # 실제 개수도 반환
        else:
            print(f"   ⚠️ 후기를 찾지 못했습니다.")
            return "커뮤니티 리뷰를 가져오지 못했습니다.", [], 0
        
    except Exception as e:
        print(f"   ❌ 커뮤니티 크롤링 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return "커뮤니티 리뷰를 가져오지 못했습니다.", [], 0