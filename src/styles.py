import streamlit as st

def apply_custom_css():
    """Applies a professional, minimalist pastel light-purplish SaaS UI design with strict light-mode overrides."""
    css = """
    <style>
    /* GLOBAL LIGHT PASTEL THEME */
    :root {
        --background-color: #FAF9FD !important;
        --secondary-background-color: #F4F0F9 !important;
        --primary-color: #8B7BC8 !important;
        --text-color: #2E2842 !important;
    }
    
    /* Base App Container & Header */
    .stApp, .stApp > header, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FAF9FD !important;
        color: #2E2842 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .main .block-container {
        max-width: 920px;
        margin: 0 auto;
        padding-top: 1.25rem;
        padding-bottom: 4.5rem;
    }
    
    /* Universal Text Color */
    .stApp, 
    .stApp p, 
    .stApp span, 
    .stApp h1, 
    .stApp h2, 
    .stApp h3, 
    .stApp h4, 
    .stApp h5, 
    .stApp h6, 
    .stApp li, 
    .stApp label,
    .stApp div[data-testid="stMarkdownContainer"] {
        color: #2E2842 !important;
    }
    
    /* Hide Default Header & Footer */
    header, footer {
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #F4F0F9 !important;
        border-right: 1px solid #E3DCEF !important;
        padding-top: 0.5rem;
    }
    
    section[data-testid="stSidebar"] * {
        color: #2E2842 !important;
    }
    
    /* FORCE ALL TEXT INPUTS, SELECTBOXES, POPOVERS & MENUS TO LIGHT PURPLE / WHITE */
    .stTextInput input,
    .stTextInput > div,
    .stTextInput > div > div,
    .stSelectbox,
    .stSelectbox > div,
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"],
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] *,
    ul[role="listbox"],
    ul[role="listbox"] *,
    li[role="option"],
    li[role="option"] * {
        background-color: #FFFFFF !important;
        color: #2E2842 !important;
        border-color: #E5DEF0 !important;
    }
    
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #F3EFFB !important;
        color: #6A56BC !important;
    }
    
    /* Expander Container */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5DEF0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(139, 123, 200, 0.05) !important;
        margin-bottom: 0.75rem !important;
    }
    
    div[data-testid="stExpander"] summary {
        background-color: #FAF7FD !important;
        color: #2E2842 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stExpander"] summary * {
        color: #2E2842 !important;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .status-badge.status-active {
        background-color: #E8F5E9 !important;
        color: #2E7D32 !important;
        border: 1px solid #C8E6C9 !important;
    }
    
    .status-badge.status-inactive {
        background-color: #FFEBEE !important;
        color: #C62828 !important;
        border: 1px solid #FFCDD2 !important;
    }
    
    /* Primary Buttons */
    .stButton > button {
        background-color: #8B7BC8 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.48rem 0.95rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(139, 123, 200, 0.18) !important;
    }
    
    .stButton > button * {
        color: #FFFFFF !important;
    }
    
    .stButton > button:hover {
        background-color: #7664BD !important;
        box-shadow: 0 4px 10px rgba(139, 123, 200, 0.28) !important;
    }
    
    .stButton > button:active {
        background-color: #5E4CA6 !important;
    }
    
    /* Clean Avatar Circles */
    div[data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessageAvatarAssistant"],
    div[data-testid="chatAvatarIcon-user"],
    div[data-testid="chatAvatarIcon-assistant"] {
        background-color: #EFE8F8 !important;
        border: 1px solid #DED6ED !important;
        border-radius: 50% !important;
        color: #6A56BC !important;
    }
    
    /* Chat Message Cards */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5DEF0 !important;
        border-radius: 16px !important;
        padding: 1.1rem 1.25rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 8px rgba(139, 123, 200, 0.04) !important;
    }
    
    /* User Chat Bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]),
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #F6F2FB !important;
        border: 1px solid #E1D6ED !important;
    }
    
    /* Chat Input Bar Fixed Dock */
    div[data-testid="stBottom"],
    div[data-testid="stBottom"] > div,
    div[data-testid="stBottom"] * {
        background-color: #FAF9FD !important;
    }
    
    div[data-testid="stChatInput"] {
        background-color: transparent !important;
        margin-bottom: 12px !important;
    }
    
    div[data-testid="stChatInput"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #DED6ED !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(139, 123, 200, 0.1) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #8B7BC8 !important;
        box-shadow: 0 0 0 3px rgba(139, 123, 200, 0.18) !important;
    }
    
    textarea[data-testid="stChatInputTextArea"],
    div[data-testid="stChatInput"] textarea {
        color: #2E2842 !important;
        background-color: #FFFFFF !important;
        font-size: 0.95rem !important;
    }
    
    textarea[data-testid="stChatInputTextArea"]::placeholder,
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #8C84A6 !important;
        opacity: 1 !important;
    }
    
    /* Horizontal Divider */
    .custom-hr {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, rgba(229, 222, 240, 0) 0%, #E5DEF0 50%, rgba(229, 222, 240, 0) 100%);
        margin: 1.1rem 0;
    }
    
    /* Interactive Clinical Capabilities Grid Cards */
    .capability-grid {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 12px;
    }
    
    .capability-box {
        background-color: #FFFFFF;
        border: 1px solid #E5DEF0;
        border-left: 3px solid #8B7BC8;
        border-radius: 8px;
        padding: 8px 10px;
        transition: all 0.2s ease;
    }
    
    .capability-box:hover {
        background-color: #F9F7FD;
        border-color: #8B7BC8;
        transform: translateX(2px);
    }
    
    .capability-title {
        font-size: 0.83rem;
        font-weight: 700;
        color: #2E2842;
        margin-bottom: 2px;
    }
    
    .capability-desc {
        font-size: 0.78rem;
        color: #6E6685;
        line-height: 1.3;
    }
    
    /* Clinical Safety Disclaimer Banner */
    .clinical-disclaimer-banner {
        background-color: #F4F0F9;
        border: 1px solid #E1D8F0;
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 0.82rem;
        color: #5E4CA6;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Retrieved Sources Evidence Box */
    .retrieval-evidence-card {
        background-color: #FAF8FD;
        border: 1px solid #E7DFEF;
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.83rem;
    }
    
    .retrieval-header {
        font-weight: 700;
        color: #4E3F8A;
        margin-bottom: 6px;
        text-transform: uppercase;
        font-size: 0.76rem;
        letter-spacing: 0.5px;
    }
    
    .retrieval-item {
        color: #2E2842;
        margin-bottom: 4px;
        line-height: 1.35;
    }
    
    .retrieval-relevance {
        display: inline-block;
        background-color: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #C8E6C9;
        border-radius: 12px;
        padding: 1px 7px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 6px;
    }
    
    /* Emergency Alert Card */
    .emergency-alert-card {
        background-color: #FFF0F0 !important;
        border: 1.5px solid #D87878 !important;
        color: #9B1C1C !important;
        padding: 14px 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 3px 10px rgba(216, 120, 120, 0.12);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
