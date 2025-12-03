"""
제품명 정규화 및 변형 처리 모듈
다양한 제품명 변형을 표준화된 형태로 변환
실제 존재하는 모델만 반환하여 환각 방지
"""
import re

try:
    from thefuzz import process, fuzz
    THEFUZZ_AVAILABLE = True
except ImportError:
    THEFUZZ_AVAILABLE = False
    print("⚠️ thefuzz 라이브러리가 설치되지 않았습니다. pip install thefuzz로 설치하세요.")

# 브랜드/시리즈 매핑
BRAND_MAP = {
    '갤럭시': ['갤럭시', '갤', 'galaxy', 'samsung'],
    '아이폰': ['아이폰', '아폰', 'iphone', 'apple'],
    # Z 시리즈 (폴더블)
    'Z플립': ['z플립', 'zflip', '제트플립', 'z 플립', '플립'],
    'Z폴드': ['z폴드', 'zfold', '제트폴드', 'z 폴드', '폴드'],
    'Z트라이폴드': ['z트라이폴드', 'z trifold', 'ztrifold', '트라이폴드', 'trifold', '3단폴드', 'tri fold']
}

# 서브 모델명 매핑
SUFFIX_MAP = {
    'Pro Max': ['promax', 'pro max', '프로맥스', '프맥'], 
    'Pro': ['pro', '프로'],
    'Plus': ['plus', '플러스', '플', '+'],
    'Ultra': ['ultra', '울트라', '울', 'u'],
    'Air': ['air', '에어'],
    'Edge': ['edge', '엣지'],
    'Mini': ['mini', '미니'],
    'Slim': ['slim', '슬림']
}

# 실제 존재하는 모델명 리스트 (환각 방지)
VALID_MODELS = [
    # 갤럭시 S25 시리즈
    "갤럭시 S25",
    "갤럭시 S25 Plus",
    "갤럭시 S25 Ultra",
    "갤럭시 S25 Edge",
    # 아이폰 17 시리즈
    "아이폰 17",
    "아이폰 17 Pro",
    "아이폰 17 Pro Max",
    "아이폰 17 Air",
    # 폴더블
    "Z플립 7",
    "Z폴드 7",
    "Z트라이폴드"
]

def _get_canonical(text, mapping_dict):
    """매핑 딕셔너리를 사용하여 표준어 반환"""
    text_lower = text.lower().replace(" ", "")
    for standard, aliases in mapping_dict.items():
        for alias in aliases:
            clean_alias = alias.lower().replace(" ", "")
            if clean_alias == text_lower:
                return standard
    return None

def _pre_normalize_for_fuzzy(query):
    """Fuzzy 매칭을 위한 전처리"""
    if not query:
        return ""
    
    # 소문자 변환 및 공백 제거
    normalized = query.lower().replace(" ", "")
    
    # 브랜드명 치환
    brand_replacements = {
        'samsung': '갤럭시',
        'iphone': '아이폰',
        'galaxy': '갤럭시'
    }
    for eng, kor in brand_replacements.items():
        if eng in normalized:
            normalized = normalized.replace(eng, kor)
    
    # 숫자와 문자 사이에 공백 넣기
    normalized = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', normalized)
    
    return normalized.strip()

def normalize_product_name(product_name, use_fuzzy_matching=True):
    """
    제품명을 표준화된 형태로 변환 (실제 존재하는 모델만 반환)
    
    예:
    - "갤S25" -> "갤럭시 S25"
    - "갤럭시S25" -> "갤럭시 S25"
    - "아폰17" -> "아이폰 17"
    - "s25 프로" -> "갤럭시 S25" (Pro 무시, 실제 모델만 반환)
    - "아이폰17 울트라" -> "아이폰 17" (Ultra 무시, 실제 모델만 반환)
    
    Args:
        product_name: 입력 제품명
        use_fuzzy_matching: Fuzzy 매칭 사용 여부 (기본값: True)
    
    Returns:
        str: 정규화된 제품명 (실제 존재하는 모델만 반환)
    """
    if not product_name:
        return ""
    
    # Fuzzy 매칭 사용 시 (thefuzz 라이브러리 사용)
    if use_fuzzy_matching and THEFUZZ_AVAILABLE:
        normalized_query = _pre_normalize_for_fuzzy(product_name)
        
        # 유사도 검사로 실제 존재하는 모델 찾기
        best_match, score = process.extractOne(
            normalized_query,
            VALID_MODELS,
            scorer=fuzz.token_set_ratio
        )
        
        # 점수가 너무 낮으면(엉뚱한 검색어) 기존 로직 사용
        if score >= 55:
            return best_match
    
    # Fuzzy 매칭 실패 또는 비활성화 시 기존 로직 사용
    query = product_name.strip()
    
    # 1. 전처리: 숫자와 문자 사이 강제 분리
    processed = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', query)
    processed = re.sub(r'\s+', ' ', processed).strip()
    
    tokens = processed.split(' ')
    
    result_brand = ""
    result_model_num = ""
    result_suffixes = []
    
    # 2. 토큰 분석
    for token in tokens:
        token_lower = token.lower()
        
        # A. 브랜드/시리즈 확인
        brand = _get_canonical(token, BRAND_MAP)
        if brand:
            if result_brand == "갤럭시" and brand.startswith("Z"):
                result_brand = brand
            elif not result_brand:
                result_brand = brand
            continue
        
        # B. Suffix 확인
        suffix = _get_canonical(token, SUFFIX_MAP)
        if suffix:
            result_suffixes.append(suffix)
            continue
        
        # C. 모델 넘버 확인
        if re.match(r'^[sS]?\d+$', token):
            if token_lower.startswith('s'):
                result_model_num = token.upper()
                if not result_brand: 
                    result_brand = "갤럭시"
            else:
                result_model_num = token
            continue
    
    # 3. 문맥 기반 추론
    if not result_brand and result_model_num:
        if result_model_num.startswith('S'):
            result_brand = "갤럭시"
        elif result_model_num.isdigit():
            num = int(result_model_num)
            if 11 <= num <= 20: 
                result_brand = "아이폰"
            elif num >= 20: 
                result_brand = "갤럭시"
                if not result_model_num.startswith('S'):
                    result_model_num = "S" + result_model_num
    
    # 4. 재조립
    final_parts = []
    
    if result_brand: 
        final_parts.append(result_brand)
    
    if result_model_num:
        if result_brand == "갤럭시" and result_model_num.isdigit():
            final_parts.append(f"S{result_model_num}")
        else:
            final_parts.append(result_model_num)
    
    if result_suffixes:
        final_parts.extend(result_suffixes)
    
    normalized_result = " ".join(final_parts)
    
    # 5. 최종 결과가 실제 존재하는 모델인지 확인
    if normalized_result in VALID_MODELS:
        return normalized_result
    
    # 존재하지 않는 모델이면 Fuzzy 매칭으로 가장 유사한 실제 모델 찾기
    if THEFUZZ_AVAILABLE:
        best_match, score = process.extractOne(
            normalized_result,
            VALID_MODELS,
            scorer=fuzz.token_set_ratio
        )
        if score >= 55:
            return best_match
    
    # 매칭 실패 시 원본 반환 (하위 호환성)
    return normalized_result


def get_product_variations(product_name):
    """
    제품명의 다양한 검색 변형을 생성
    
    예: "갤럭시 S25" -> ["갤럭시 S25", "갤S25", "갤럭시S25", "Galaxy S25"]
    
    Args:
        product_name: 정규화된 제품명
    
    Returns:
        list: 검색 변형 리스트
    """
    variations = [product_name]  # 원본 포함
    
    normalized = normalize_product_name(product_name)
    
    # 갤럭시 변형
    if '갤럭시' in normalized:
        # "갤럭시 S25" -> "갤S25", "갤럭시S25"
        match = re.search(r'갤럭시\s*(.+)', normalized)
        if match:
            suffix = match.group(1)
            variations.extend([
                f"갤{suffix}",
                f"갤럭시{suffix}",
                f"Galaxy {suffix}",
                f"galaxy {suffix}",
            ])
    
    # 아이폰 변형
    if '아이폰' in normalized:
        # "아이폰 17" -> "아폰17", "iPhone17"
        match = re.search(r'아이폰\s*(.+)', normalized)
        if match:
            suffix = match.group(1)
            variations.extend([
                f"아폰{suffix}",
                f"아이폰{suffix}",
                f"iPhone {suffix}",
                f"iphone {suffix}",
            ])
    
    # 중복 제거
    return list(set(variations))


def extract_sub_model(product_name):
    """
    제품명에서 서브 모델명 추출 (에어, 프로, 프로맥스, 플러스, 울트라 등)
    
    Args:
        product_name: 제품명
    
    Returns:
        str: 서브 모델명 (없으면 빈 문자열)
    """
    normalized = normalize_product_name(product_name)
    
    # 정규화된 제품명을 토큰으로 분리하여 서브 모델명 확인
    tokens = normalized.split(' ')
    
    for token in tokens:
        suffix = _get_canonical(token, SUFFIX_MAP)
        if suffix:
            return suffix.lower()
    
    return ""


def find_similar_product_in_db(product_name, db_products):
    """
    DB에 저장된 제품명 중 유사한 제품 찾기 (엄격한 매칭)
    
    Args:
        product_name: 검색할 제품명
        db_products: DB에 저장된 제품명 리스트
    
    Returns:
        str: 가장 유사한 제품명 또는 None
    """
    normalized_search = normalize_product_name(product_name)
    search_variations = get_product_variations(normalized_search)
    
    # 서브 모델명 추출
    search_sub_model = extract_sub_model(normalized_search)
    
    # 정확히 일치하는 경우
    for db_product in db_products:
        normalized_db = normalize_product_name(db_product)
        if normalized_search.lower() == normalized_db.lower():
            return db_product
        
        # 변형 중 하나와 일치하는 경우
        db_variations = get_product_variations(normalized_db)
        if any(var.lower() in [v.lower() for v in search_variations] for var in db_variations):
            return db_product
    
    # 부분 일치 검색 (엄격한 매칭)
    search_keywords = set()
    for var in search_variations:
        # 모델명 추출 (S25, S24, 17, 16 등)
        model_matches = re.findall(r'[A-Z]+\s*\d+[A-Z]*|\d+[A-Z]+|[A-Z]\d+', var)
        # 한글 키워드 추출
        korean_matches = re.findall(r'[가-힣]+', var)
        search_keywords.update([k.lower().strip() for k in model_matches + korean_matches])
    
    # 핵심 모델명 추출 (S25, 17 등) - 서브 모델명 제외
    core_model = None
    for keyword in search_keywords:
        # S25, S24, 17, 16 같은 패턴 찾기 (서브 모델명 제외)
        model_match = re.search(r's?\d+', keyword)
        if model_match:
            core_model = model_match.group(0)
            break
    
    best_match = None
    best_score = 0
    
    for db_product in db_products:
        normalized_db = normalize_product_name(db_product)
        db_sub_model = extract_sub_model(normalized_db)
        
        # 서브 모델명이 둘 다 있으면 반드시 일치해야 함
        if search_sub_model and db_sub_model:
            if search_sub_model != db_sub_model:
                continue  # 서브 모델명이 다르면 스킵
        
        # 서브 모델명이 하나만 있으면 매칭하지 않음 (엄격한 매칭)
        if (search_sub_model and not db_sub_model) or (not search_sub_model and db_sub_model):
            continue
        
        db_keywords = set(re.findall(r'[A-Z]+\s*\d+[A-Z]*|\d+[A-Z]+|[A-Z]\d+|[가-힣]+', normalized_db))
        db_keywords = {k.lower().strip() for k in db_keywords}
        
        # 핵심 모델명이 있으면 우선 확인
        if core_model:
            db_core_model = None
            for keyword in db_keywords:
                model_match = re.search(r's?\d+', keyword)
                if model_match:
                    db_core_model = model_match.group(0)
                    break
            
            # 핵심 모델명이 정확히 일치해야 함
            if db_core_model and core_model == db_core_model:
                # 공통 키워드 개수로 유사도 계산
                common = len(search_keywords & db_keywords)
                if common > best_score:
                    best_score = common
                    best_match = db_product
        else:
            # 핵심 모델명이 없으면 일반 키워드 매칭
            common = len(search_keywords & db_keywords)
            if common > best_score:
                best_score = common
                best_match = db_product
    
    return best_match if best_score > 0 else None

