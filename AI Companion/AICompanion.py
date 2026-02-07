import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

#基本布局
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="👾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

#生成会话标识
def generate_session_id():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#保存会话记录
def save_session():
    if st.session_state.current_session:
        st.session_state.data = {
            "message": st.session_state.message,
            "name": st.session_state.name,
            "persona": st.session_state.persona,
            "current_session": st.session_state.current_session
        }
        # 判断有无 session 文件，没有时创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        # 将信息保存为json文件
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.data, f, ensure_ascii=False, indent=4)

#加载所有的会话列表信息
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    #反转列表
    session_list.sort(reverse=True)
    return session_list

#加载会话信息
def load_session(session_id):
    try:
        if os.path.exists(f"sessions/{session_id}.json"):
            with open(f"sessions/{session_id}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.message = session_data["message"]
                st.session_state.name = session_data["name"]
                st.session_state.persona = session_data["persona"]
                st.session_state.current_session = session_data["current_session"]
    except Exception:
        st.error("会话加载失败！")

#删除历史会话
def delete_session(session_id):
    try:
        if os.path.exists(f"sessions/{session_id}.json"):
            os.remove(f"sessions/{session_id}.json")
            #如果删除的是当前会话，则更新当前会话标识
            if session_id == st.session_state.current_session:
                st.session_state.message = []
                st.session_state.current_session = generate_session_id()
    except Exception:
        st.error("会话删除失败！")

#大标题
st.title("AI智能伴侣")

#logo
st.logo("./resourses/logo.png")

#prompt
system_prompt = """
        你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。：
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 回复简短，像微信聊天一样
            5. 有需要的话可以用❤️🌸等emoji表情
            6. 用符合伴侣性格的方式对话
            7. 回复的内容, 要充分体现伴侣的性格特征
        伴侣性格：
            - %s
        你必须严格遵守上述规则来回复用户。
    """

if "message" not in st.session_state:
    st.session_state.message = []

if "name" not in st.session_state:
    st.session_state.name = "小明"

if "persona" not in st.session_state:
    st.session_state.persona = "活泼开朗乐观的男大学生"

if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_id()

#展示聊天记录
st.text(f"会话名称{st.session_state.current_session}")
for message in st.session_state.message:
    st.chat_message(message["role"]).write(message["content"])

#创建OpenAI客户端
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")

#创建侧边栏
with st.sidebar:
    st.subheader("AI控制面板")
    # 创建一个按钮
    if st.button("新建会话", icon="🎭️", width="stretch"):
        #1.保存会话记录
        save_session()

        #2.新建会话
        if st.session_state.message:
            st.session_state.message = []
            st.session_state.current_session = generate_session_id()
            save_session()
            st.rerun()

    #历史会话
    st.text("历史会话")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([5,1])
        #加载会话记录
        with col1:
            if st.button(session, width="stretch",icon="💌", key=f"load_{session}",type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        #删除历史会话
        with col2:
            if st.button("", width="stretch",icon="🗑️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #分割线
    st.divider()

    st.subheader("伴侣设置")
    name = st.text_input("请输入伴侣名称：",  placeholder="请输入昵称", value=st.session_state.name)
    if name:
        st.session_state.name = name
    persona = st.text_area("请输入伴侣人设：",  placeholder="请输入人设", value=st.session_state.persona)
    if persona:
        st.session_state.persona = persona

#对话框
prompt = st.chat_input("说点什么吧~")
if prompt:
    st.chat_message("user").write(prompt)

    #添加到会话记录中
    st.session_state.message.append({"role": "user", "content": prompt})

    #调用大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.name, st.session_state.persona)},
            *st.session_state.message
        ],
        stream=True
    )

    #输出结果（流式）
    response_message = st.empty ()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    #添加到会话记录中
    st.session_state.message.append({"role": "assistant", "content": full_response})
    save_session()
