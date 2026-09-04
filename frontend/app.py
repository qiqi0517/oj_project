import streamlit as st

if __package__:
    from .config import APP_TITLE
    from .session import get_current_user, init_session_state, is_admin
else:
    from config import APP_TITLE
    from session import get_current_user, init_session_state, is_admin


def configure_page() -> None:
    """调用 st.set_page_config 配置页面。"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def build_navigation() -> None:
    """创建 Streamlit 页面导航。"""
    user = get_current_user()
    if user is None:
        pages = ["登录", "注册"]
    else:
        pages = [
            "我的信息",
            "题目",
            "新增 / 编辑题目",
            "提交代码",
            "提交记录",
        ]
        if is_admin():
            pages.append("用户管理")
        pages.append("退出登录")

    selected_page = st.sidebar.radio("导航", pages)
    st.header(selected_page)
    st.info("公共基础已就绪；该页面的业务功能将在后续阶段接入。")


def render_sidebar_user() -> None:
    """在侧边栏显示当前登录用户和角色。"""
    user = get_current_user()
    st.sidebar.title(APP_TITLE)
    if user is None:
        st.sidebar.caption("当前未登录")
        return

    username = user.get("username", "未知用户")
    role = user.get("role", "unknown")
    st.sidebar.write(f"当前用户：{username}")
    st.sidebar.caption(f"角色：{role}")


def main() -> None:
    """前端入口。"""
    configure_page()
    init_session_state()
    render_sidebar_user()
    build_navigation()

if __name__ == "__main__":
    main()
