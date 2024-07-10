import streamlit as st
from anthropic import Anthropic
from datetime import datetime
import os

# API 키를 st.secrets에서 가져옵니다
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# 모델 설정
ANTHROPIC_MODEL_HAIKU = "claude-3-haiku-20240307"

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# 레벨 설명
LEVEL_DESCRIPTIONS = {
    "초급": "초급 수준: 간단하고 기본적인 문장 구조, 일반적인 어휘 사용.",
    "중급": "중급 수준: 더 구체적인 표현, 부가적인 요청 포함, 약간 복잡한 어휘 사용.",
    "고급": "고급 수준: 복잡한 문장 구조, 전문 용어 사용, 상세한 설명과 질문, 높은 수준의 대화 능력 필요."
}

# 공통 system message 생성 함수
def create_system_message(language, level, use_formal_terms=False):
    system_message = (
        f"당신은 친절하고 능숙한 {language} 회화 도우미입니다. "
        f"주어진 상황과 장소에 맞는 한국어 질문을 생성하고 이를 {language}로 정확히 번역해주세요. "
        f"다음 레벨 설명을 엄격히 준수하세요: {LEVEL_DESCRIPTIONS[level]} "
        f"번역 시 원문의 의미와 구조를 그대로 유지하며, 추가적인 설명이나 확장을 하지 마세요. "
        f"레벨에 맞는 적절한 어휘를 사용하세요. "
        f"불필요한 설명이나 소개 문구 없이 바로 질문과 번역을 제공해주세요."
    )
    
    if use_formal_terms and language == '중국어':
        system_message += (
            """
            1. 격식 있는 용어, 성어, 사자성어를 적절히 사용하여 번역해주세요. 
            2. 각 문장에 1-2개의 격식 있는 표현이나 사자성어를 포함시키되, 과도한 사용은 피해주세요. 
            예시: '面试' → '甄选人才', '竞争优势' → '核心竞争力', '诚实' → '诚实守信' 등을 상황에 맞게 사용하세요. 
            3. 다음과 같은 격식 있는 표현을 적극 활용하세요:
           '甄选人才', '核心竞争力', '诚实守信', '迎刃而解', '宏伟蓝图', '价值理念',
           '企业文化', '英才', '社会担当', '贡献良多', '履历书', '贵司/敝司', '长处',
           '不足', '发展蓝图', '阅历', '精英团队' 등
            4.문장의 자연스러움을 유지하면서 격식을 높이는 것이 중요합니다."""
        )
    
    return system_message

# Anthropic 모델을 사용하여 콘텐츠 생성 함수
def generate_content_anthropic(model, query, max_tokens, temperature, language, level, use_formal_terms=False):
    system_message = create_system_message(language, level, use_formal_terms)
    
    response = anthropic_client.messages.create(
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_message,
        messages=[
            {"role": "user", "content": query}
        ],
        model=model,
    )
    return response.content[0].text

# 입력과 출력을 로그에 기록하는 함수
def log_interaction(input_data, output_data):
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    log_entry += f"입력:\n"
    log_entry += f"장소: {input_data['place']}\n"
    log_entry += f"상황: {input_data['situation']}\n"
    log_entry += f"역할: {input_data['role']}\n"
    log_entry += f"레벨: {input_data['level']}\n\n"
    log_entry += f"출력:\n{output_data}\n\n"
    
    if 'log_content' not in st.session_state:
        st.session_state.log_content = ""
    st.session_state.log_content += log_entry

# 대화 내용 다운로드 함수
def download_conversation():
    if 'log_content' in st.session_state and st.session_state.log_content:
        log_content = st.session_state.log_content
    else:
        log_content = "로그가 아직 생성되지 않았습니다."
    
    # 파일 다운로드 버튼 생성
    st.download_button(
        label="대화 내용 다운로드",
        data=log_content,
        file_name="conversation_log.txt",
        mime="text/plain"
    )

# Streamlit 앱 레이아웃 설정
st.title("중국어/영어 회화 앱")

# 세션 상태를 사용하여 상태 유지
if 'translated_questions' not in st.session_state:
    st.session_state.translated_questions = None
if 'show_custom_input' not in st.session_state:
    st.session_state.show_custom_input = False
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = "초급"
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "중국어"
if 'use_formal_terms' not in st.session_state:
    st.session_state.use_formal_terms = False
if 'place' not in st.session_state:
    st.session_state.place = ""
if 'situation' not in st.session_state:
    st.session_state.situation = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'clear_fields' not in st.session_state:
    st.session_state.clear_fields = False

# 언어 선택 (폼 외부)
language = st.selectbox("언어를 선택하세요:", ["중국어", "영어"], index=["중국어", "영어"].index(st.session_state.selected_language))
st.session_state.selected_language = language

# 질문 유형 선택
question_type = st.selectbox("질문 유형을 선택하세요:", ["질문", "질문&답변"])

# 격식 용어 옵션 (중국어일 때만)
if language == "중국어":
    st.session_state.use_formal_terms = st.checkbox("격식 용어 사용", value=st.session_state.use_formal_terms)

# 폼 생성
with st.form(key='input_form'):
    if 'clear_fields' in st.session_state and st.session_state.clear_fields:
        st.session_state.place = ""
        st.session_state.situation = ""
        st.session_state.role = ""
        st.session_state.clear_fields = False

    place = st.text_input("장소를 입력하세요:", value=st.session_state.get('place', ""), key="place")
    situation = st.text_input("상황을 입력하세요:", value=st.session_state.get('situation', ""), key="situation")
    role = st.text_input("역할을 입력하세요:", value=st.session_state.get('role', ""), key="role")
    level = st.selectbox("레벨을 선택하세요:", ["초급", "중급", "고급"], index=0)
    
    submit_button = st.form_submit_button(label='예문 생성')

# 대화 내용 다운로드 버튼
download_conversation()

if submit_button and place and situation and role and level:
    st.session_state.selected_level = level
    with st.spinner('예문을 작성 중입니다...'):
        query_for_questions = f"""다음 시나리오에 맞는 한국어 {'질문 10개' if question_type == '질문' else '질문 5개와 그에 대한 답변'}를 생성하고 {language}로 번역해주세요:
                                장소: {place}
                                상황: {situation}
                                역할: {role} (질문자)
                                레벨: {level}
                                {'질문은 ' + role + '이 하고, 답변은 상황에 맞는 다른 역할(예: 면접관)이 하도록 해주세요.' if question_type == '질문&답변' else ''}
                                각 질문{'과 답변' if question_type == '질문&답변' else ''}을 다음 형식으로 제공해주세요:
                                1.
                                [한국어 질문]
                                [번역된 {language}]
                                {'[한국어 답변]' if question_type == '질문&답변' else ''}
                                {'[번역된 ' + language + ' 답변]' if question_type == '질문&답변' else ''}
                                """
        
        translated_questions = generate_content_anthropic(
            ANTHROPIC_MODEL_HAIKU, 
            query_for_questions, 
            max_tokens=3000, 
            temperature=0.7, 
            language=language, 
            level=level, 
            use_formal_terms=st.session_state.use_formal_terms
        )
        
        st.session_state.translated_questions = translated_questions
        log_interaction({
            'place': place,
            'situation': situation,
            'role': role,
            'level': level
        }, st.session_state.translated_questions)

# 생성된 번역된 질문 출력
if st.session_state.translated_questions:
    st.text_area("생성된 질문" if question_type == "질문" else "생성된 질문과 답변", st.session_state.translated_questions, height=400)