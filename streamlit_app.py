import os

import streamlit as st
from openai import OpenAI


st.set_page_config(
    page_title="AI日本考学推荐系统",
    page_icon="🎓",
    layout="wide",
)


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


DEEPSEEK_API_KEY = get_secret("DEEPSEEK_API_KEY")
DEFAULT_MODEL = get_secret("DEFAULT_MODEL", "deepseek-chat")


@st.cache_resource
def get_client(api_key: str):
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


client = get_client(DEEPSEEK_API_KEY)


st.title("🎓 AI日本考学推荐系统")
st.caption("Streamlit Cloud 简化版：AI顾问 + 择校推荐")

if not client:
    st.error("未配置 DEEPSEEK_API_KEY。请在 Streamlit Cloud Secrets 中添加 DEEPSEEK_API_KEY。")
    st.stop()


def chat_completion(messages, temperature: float = 0.7) -> str:
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


tab_chat, tab_recommend = st.tabs(["AI顾问", "择校推荐"])

with tab_chat:
    st.header("AI顾问")
    st.write("可以咨询日本大学院申请、研究计划书、语言成绩、教授套磁、择校策略等问题。")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "system",
                "content": (
                    "你是专业的日本大学院留学顾问。请用中文回答，回答要具体、务实、结构清晰。"
                    "如果信息不确定，请提醒用户以学校官网和募集要项为准。"
                ),
            }
        ]

    for message in st.session_state.chat_messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])

    user_input = st.chat_input("请输入你的问题，例如：我想申请日本大学院，该怎么准备？")

    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI正在思考..."):
                answer = chat_completion(st.session_state.chat_messages)
                st.write(answer)

        st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    if st.button("清空对话"):
        st.session_state.chat_messages = [
            {
                "role": "system",
                "content": (
                    "你是专业的日本大学院留学顾问。请用中文回答，回答要具体、务实、结构清晰。"
                    "如果信息不确定，请提醒用户以学校官网和募集要项为准。"
                ),
            }
        ]
        st.rerun()


with tab_recommend:
    st.header("AI择校推荐")
    st.write("填写你的基本背景，AI会给出冲刺校、稳妥校、保底校建议。")

    with st.form("recommend_form"):
        col1, col2 = st.columns(2)

        with col1:
            gpa = st.number_input("GPA（0-4.0）", min_value=0.0, max_value=4.0, value=3.0, step=0.01)
            english_type = st.selectbox("英语考试类型", ["TOEFL", "IELTS"])
            english_score = st.number_input("英语成绩", min_value=0.0, value=80.0, step=0.5)
            jlpt_level = st.selectbox("JLPT等级", ["无", "N1", "N2", "N3", "N4", "N5"])

        with col2:
            bachelor_school = st.text_input("本科院校", placeholder="如：北京大学、普通一本、双非等")
            bachelor_major = st.text_input("本科专业", placeholder="如：计算机科学")
            target_major = st.text_input("目标专业", placeholder="如：情报学、经济学、传媒学；不填则默认与本科相关")
            budget_yen = st.number_input("年预算（日元，可选）", min_value=0, value=0, step=100000)

        submitted = st.form_submit_button("生成推荐")

    if submitted:
        if not bachelor_school.strip() or not bachelor_major.strip():
            st.error("请填写本科院校和本科专业。")
            st.stop()

        actual_target_major = target_major.strip() or bachelor_major.strip()
        actual_jlpt = None if jlpt_level == "无" else jlpt_level
        actual_budget = None if budget_yen == 0 else budget_yen

        prompt = f"""
你是专业的日本大学院留学顾问，熟悉日本大学院申请、研究科选择、教授匹配和募集要项。

请根据以下学生背景，推荐日本大学院：

学生背景：
- GPA：{gpa}
- 英语考试：{english_type} {english_score}
- JLPT：{actual_jlpt or '无'}
- 本科院校：{bachelor_school}
- 本科专业：{bachelor_major}
- 目标专业：{actual_target_major}
- 年预算（日元）：{actual_budget or '未填写'}

请按以下结构输出：

## 总体评估
先简要评价该学生的申请竞争力、主要优势、主要短板。

## 冲刺校（3所）
每所学校包含：
- 学校名称
- 推荐研究科/专业方向
- 推荐理由
- 匹配度百分比
- 风险点
- 申请建议

## 稳妥校（3所）
每所学校包含同样字段。

## 保底校（3所）
每所学校包含同样字段。

## 后续准备建议
给出语言成绩、研究计划书、套磁、时间线方面的建议。

要求：
- 使用中文。
- 不要编造确定的截止日期或具体教授信息。
- 如果涉及具体募集要求，请提醒用户以学校官网和最新募集要项为准。
"""

        with st.spinner("正在生成推荐..."):
            answer = chat_completion(
                [
                    {"role": "system", "content": "你是熟悉日本大学院申请的专业留学顾问。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            st.markdown(answer)
