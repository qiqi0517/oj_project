import streamlit as st

if __package__:
    from .config import APP_TITLE
    from .pages import auth, problems, profile, submissions, users
    from .session import get_current_user, init_session_state, is_admin
    from .ui import format_role
else:
    from config import APP_TITLE
    from pages import auth, problems, profile, submissions, users
    from session import get_current_user, init_session_state, is_admin
    from ui import format_role


_NAVIGATION_KEY = "navigation_page"


def configure_page() -> None:
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_app_styles() -> None:
    """应用统一的 OJ 工作台视觉样式。"""
    st.markdown(
        """
        <style>
        :root {
            --oj-bg: #f7f5fa;
            --oj-surface: #ffffff;
            --oj-text: #241b2b;
            --oj-muted: #746b7b;
            --oj-line: #e8e1ec;
            --oj-accent: #713183;
            --oj-accent-dark: #572466;
            --oj-accent-soft: #f2eaf5;
            --oj-sidebar: #ffffff;
            --oj-sidebar-soft: #f4edf6;
        }

        .stApp {
            background: var(--oj-bg);
            color: var(--oj-text);
            font-family: Inter, "Noto Sans SC", "Microsoft YaHei", sans-serif;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1180px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
        }
        [data-testid="stSidebar"] {
            background: var(--oj-sidebar);
            border-right: 1px solid var(--oj-line);
            box-shadow: 8px 0 24px rgba(67, 31, 78, 0.035);
        }
        [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding: 1.25rem 0.75rem 1rem;
        }
        [data-testid="stSidebar"] * {
            color: #35263b;
        }
        [data-testid="stSidebar"] .stButton > button {
            justify-content: flex-start;
            min-height: 2.75rem;
            padding: 0.65rem 0.85rem;
            border: 1px solid transparent;
            border-radius: 0.55rem;
            background: transparent;
            color: #62566a;
            font-weight: 600;
            transition: background-color 120ms ease, color 120ms ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: var(--oj-sidebar-soft);
            color: var(--oj-accent-dark);
            border-color: #eadced;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--oj-accent-soft);
            color: var(--oj-accent-dark);
            border-left: 3px solid var(--oj-accent);
        }
        [data-testid="stSidebar"] .st-key-sidebar_user_card {
            margin-top: auto;
            padding-top: 1.25rem;
            padding-bottom: 0.75rem;
        }
        [data-testid="stSidebar"] .st-key-sidebar_user_card
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #faf8fb;
            border: 1px solid var(--oj-line);
            border-radius: 0.65rem;
        }
        .oj-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0 0.35rem 1.4rem;
        }
        .oj-brand-mark {
            display: grid;
            place-items: center;
            width: 2.35rem;
            height: 2.35rem;
            border-radius: 0.6rem;
            background: var(--oj-accent);
            color: #ffffff !important;
            font-size: 1.05rem;
            font-weight: 900;
        }
        .oj-brand-name {
            color: #3b2443 !important;
            font-size: 1.18rem;
            font-weight: 800;
            line-height: 1.2;
        }
        .oj-brand-subtitle {
            color: #8a7891 !important;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.04em;
        }

        h1, h2, h3 {
            color: #2e1d35;
            letter-spacing: -0.02em;
        }
        h1 {
            font-size: 1.85rem !important;
            font-weight: 760 !important;
            margin-bottom: 1.25rem !important;
        }
        h2, h3 {
            font-weight: 700 !important;
        }
        [data-testid="stForm"] {
            background: var(--oj-surface);
            border: 1px solid var(--oj-line);
            border-radius: 0.75rem;
            padding: 1.35rem;
            box-shadow: 0 8px 26px rgba(72, 35, 84, 0.045);
        }
        [data-testid="stMetric"] {
            background: var(--oj-surface);
            border: 1px solid var(--oj-line);
            border-radius: 0.65rem;
            padding: 0.9rem 1rem;
        }
        [data-testid="stMetricLabel"] {
            color: var(--oj-muted);
            font-family: "SFMono-Regular", Consolas, monospace;
        }
        .st-key-problem_metadata [data-testid="stMetric"] {
            padding: 0.7rem 0.75rem;
        }
        .st-key-problem_metadata [data-testid="stMetricLabel"] p {
            font-size: 0.72rem !important;
        }
        .st-key-problem_metadata [data-testid="stMetricValue"] {
            font-size: 0.92rem !important;
            line-height: 1.3;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--oj-line);
            border-radius: 0.65rem;
            overflow: hidden;
            background: var(--oj-surface);
        }
        [data-testid="stDataEditor"] {
            border: 1px solid var(--oj-line);
            border-radius: 0.65rem;
            overflow: hidden;
        }
        .stButton > button {
            min-height: 2.55rem;
            border-radius: 0.5rem;
            border-color: #d6dae1;
            font-weight: 650;
        }
        .stButton > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: var(--oj-accent);
            border-color: var(--oj-accent);
            color: #ffffff;
        }
        .stButton > button[kind="primary"]:hover,
        [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background: var(--oj-accent-dark);
            border-color: var(--oj-accent-dark);
            color: #ffffff;
        }
        [data-baseweb="input"],
        [data-baseweb="textarea"],
        [data-baseweb="select"] > div {
            border-radius: 0.5rem !important;
            border-color: #d9dde4 !important;
            background: #ffffff !important;
        }
        [data-baseweb="input"]:focus-within,
        [data-baseweb="textarea"]:focus-within,
        [data-baseweb="select"] > div:focus-within {
            border-color: var(--oj-accent) !important;
            box-shadow: 0 0 0 2px rgba(113, 49, 131, 0.1) !important;
        }
        [data-testid="stAlert"] {
            border-radius: 0.6rem;
        }
        [data-testid="stExpander"] {
            background: var(--oj-surface);
            border-color: var(--oj-line);
            border-radius: 0.65rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            color: var(--oj-muted);
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: var(--oj-accent-dark);
        }
        [data-testid="stCode"] {
            border-radius: 0.55rem;
        }
        textarea {
            line-height: 1.65 !important;
        }
        hr {
            border-color: var(--oj-line) !important;
        }
        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1.25rem 1rem 3rem;
            }
            h1 {
                font-size: 1.55rem !important;
            }
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
    elif selected_page == "我的信息":
        profile.render_page()
    elif selected_page == "用户管理":
        users.render_page()
    elif selected_page == "题目":
        problems.render_page()
    elif selected_page == "评测结果":
        submissions.render_page()


def build_navigation() -> None:
    """Build module navigation and render the selected page."""
    user = get_current_user()
    if user is None:
        module_pages = ["登录", "注册"]
        allowed_pages = module_pages
    else:
        module_pages = ["题目", "评测结果"]
        if is_admin():
            module_pages.append("用户管理")
        allowed_pages = [*module_pages, "我的信息"]

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
    """在侧栏顶部展示产品标识。"""
    st.sidebar.markdown(
        """
        <div class="oj-brand">
          <div class="oj-brand-mark">Q</div>
          <div>
            <div class="oj-brand-name">qiqiOJ</div>
            <div class="oj-brand-subtitle">在线评测系统</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_user() -> None:
    """Render username and role at the bottom of the sidebar."""
    user = get_current_user()
    with st.sidebar.container(key="sidebar_user_card", border=True):
        if user is None:
            st.caption("尚未登录")
            return

        username = str(user.get("username", "未知用户"))
        role = str(user.get("role", "未知"))
        st.write(f"**{username}**")
        st.caption(f"用户身份：{format_role(role)}")
        if st.button("我的信息", key="nav_user_profile", use_container_width=True):
            _select_page("我的信息")


def main() -> None:
    """Run the frontend application."""
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
