import streamlit as st

if __package__:
    from .config import APP_TITLE
    from .pages import auth, problems, profile, submissions, users
    from .session import get_current_user, init_session_state, is_admin
else:
    from config import APP_TITLE
    from pages import auth, problems, profile, submissions, users
    from session import get_current_user, init_session_state, is_admin


_NAVIGATION_KEY = "navigation_page"


def configure_page() -> None:
    """调用 st.set_page_config 配置页面。"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_app_styles() -> None:
    """调整侧栏为顶部模块导航和底部用户卡片。"""
    st.markdown(
        """
        <style>
        [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] .stButton > button {
            justify-content: flex-start;
            border-radius: 0.5rem;
        }
        [data-testid="stSidebar"] .st-key-sidebar_user_card {
            margin-top: auto;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _select_page(page: str) -> None:
    st.session_state[_NAVIGATION_KEY] = page
    st.rerun()


def _render_selected_page(selected_page: str) -> None:
    st.header(selected_page)
    if selected_page == "登录":
        auth.render_login_form()
    elif selected_page == "注册":
        auth.render_register_form()
    elif selected_page == "用户信息":
        profile.render_page()
    elif selected_page == "用户管理":
        users.render_page()
    elif selected_page == "题目":
        problems.render_page()
    elif selected_page == "评测结果":
        submissions.render_page()


def build_navigation() -> None:
    """创建模块导航并渲染当前页面。"""
    user = get_current_user()
    if user is None:
        module_pages = ["登录", "注册"]
        allowed_pages = module_pages
    else:
        module_pages = ["题目", "评测结果"]
        if is_admin():
            module_pages.append("用户管理")
        allowed_pages = [*module_pages, "用户信息"]

    selected_page = st.session_state.get(_NAVIGATION_KEY)
    if selected_page not in allowed_pages:
        selected_page = module_pages[0]
        st.session_state[_NAVIGATION_KEY] = selected_page

    for page in module_pages:
        if st.sidebar.button(
            page,
            key=f"nav_{page}",
            type="primary" if page == selected_page else "tertiary",
            use_container_width=True,
        ):
            _select_page(page)

    _render_selected_page(str(selected_page))


def render_sidebar_brand() -> None:
    """在侧栏最上方展示系统标题。"""
    st.sidebar.title(APP_TITLE)


def render_sidebar_user() -> None:
    """在侧栏底部展示当前 username 和 role。"""
    user = get_current_user()
    with st.sidebar.container(key="sidebar_user_card", border=True):
        if user is None:
            st.caption("未登录")
            return

        username = str(user.get("username", "unknown"))
        role = str(user.get("role", "unknown"))
        st.write(f"**{username}**")
        st.caption(f"role: {role}")
        if st.button("用户信息", key="nav_user_profile", use_container_width=True):
            _select_page("用户信息")


def main() -> None:
    """前端入口。"""
    configure_page()
    init_session_state()
    apply_app_styles()
    notice = auth.pop_auth_notice()
    if notice is not None:
        st.success(notice)
    render_sidebar_brand()
    build_navigation()
    render_sidebar_user()


if __name__ == "__main__":
    main()
