import streamlit as st  # pyrefly: ignore[missing-import]
import serpapi  # pyrefly: ignore[missing-import]
import os
import requests
import json
from dotenv import load_dotenv  # pyrefly: ignore[missing-import]

# 1. 初始設定 (設定網頁標題與排版)
st.set_page_config(
    page_title="Google Lens 以圖搜圖", 
    layout="wide", # 寬螢幕模式才能展現精美網格
    page_icon="",
    initial_sidebar_state="expanded"
)

# 2. 載入 .env 檔案中的環境變數
load_dotenv()


st.markdown("""
<style>
    /* 全域字體優化 */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #262730;
    }
    
    /* 專業標題顏色 */
    .big-title {
        color: #262730;
        font-weight: 800 !important;
        margin-bottom: 0px !important;
    }
    .sub-title {
        color: #556b2f;
        font-size: 1.2rem;
        margin-bottom: 2rem !important;
    }

    /* 上傳區塊樣式優化 */
    [data-testid="stFileUploader"] {
        border: 2px dashed #008080;
        border-radius: 10px;
        padding: 1rem;
        background-color: #f0f2f6;
    }
    
    /* 側邊欄優化 */
    [data-testid="stSidebar"] {
        background-color: #f7f9fc;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #008080;
        font-size: 1.4rem;
        font-weight: 700;
        border-bottom: 2px solid #008080;
        padding-bottom: 5px;
    }

    /* 商品卡片核心樣式 */
    .product-card {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); /* 淡淡的立體陰影 */
        padding: 20px;
        margin-bottom: 25px;
        transition: transform 0.3s ease, box-shadow 0.3s ease; /* 平滑過場動畫 */
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        height: 100%; /* 確保所有卡片等高 */
    }
    
    /* 滑鼠懸停時卡片放大與加深陰影 */
    .product-card:hover {
        transform: translateY(-5px); /* 向上微調 */
        box-shadow: 0 8px 25px rgba(0,0,0,0.15); /* 陰影加深 */
    }

    /* 商品圖片 */
    .product-img-container {
        height: 180px; /* 固定圖片高度 */
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
    }
    .product-img {
        max-height: 100%;
        max-width: 100%;
        border-radius: 8px;
    }

    /* 商品標題 */
    .product-title {
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
        text-decoration: none !important;
        color: #262730 !important;
        display: -webkit-box;
        -webkit-line-clamp: 2; /* 標題最多兩行，多餘省略 */
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* 來源標籤 */
    .source-badge {
        background-color: #e6f7f7;
        color: #008080;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
        display: inline-block;
    }

    /* 價格 */
    .price-tag {
        color: #228b22;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        margin-top: auto; /* 將價格推到底部對齊 */
    }

    /* 按鈕顏色優化 */
    div.stButton > button:first-child {
        background-color: #008080;
        color: white;
        border: none;
        border-radius: 20px;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #006666;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 側邊欄：設定與篩選
# ==========================================
with st.sidebar:
    st.header("搜尋設定")
    
    # API Key 設定區
    # 優先從 Streamlit Secrets 讀取，其次從環境變數
    api_key = st.secrets.get("serpapi_api_key", None) or os.getenv("serpapi_api_key")
    if not api_key:
        api_key = st.text_input("載入您的 SerpAPI Key", type="password")
        if not api_key:
            st.warning("請在 .env 檔案中設定 serpapi_api_key，或在這裡輸入。")
    else:
        st.success("已載入")

    # 搜尋進階設定
    st.markdown("---")
    st.header("語言與地區")
    col_lang, col_country = st.columns(2)
    with col_lang:
        hl = st.selectbox("語言 (hl)", ["zh-TW", "en"], index=0)
    with col_country:
        gl = st.selectbox("地區 (gl)", ["tw", "us"], index=0)

    # 平台篩選區 (搬移到這裡更符合工具性)
    st.markdown("---")
    st.header("平台篩選")
    platform_filter = st.text_input(
        "輸入平台關鍵字...", 
        value="", 
        placeholder="例如: Amazon, 蝦皮, PChome"
    )

# ==========================================
# 主畫面：上傳與結果
# ==========================================
st.markdown("<h1 class='big-title'>視覺化以圖搜圖系統</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>基於 Google Lens 技術，一鍵尋找全球相似產品</p>", unsafe_allow_html=True)

# 使用容器包裝上傳與按鈕，讓排版更整齊
with st.container():
    uploaded_file = st.file_uploader("請選擇一張 JPG 或 PNG 圖片上傳...", type=["jpg", "jpeg", "png"])
    
    # 初始化一個容器用來顯示「開始搜尋」按鈕和搜尋完成狀態
    status_cols = st.columns([1, 1, 10])
    with status_cols[0]:
        search_button = st.button("搜尋", type="primary", use_container_width=True)

# 圖片上傳後的邏輯
def upload_to_temporary_host(file_bytes, file_name):
    """將圖片暫存至雲端取得 URL"""
    try:
        files = {'file': (file_name, file_bytes, 'image/jpeg')}
        response = requests.post("https://tmpfiles.org/api/v1/upload", files=files, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            url = data['data']['url']
            raw_url = url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
            return raw_url
    except requests.exceptions.Timeout:
        st.error("圖片上傳暫存伺服器逾時，請再試一次。")
    except Exception as e:
        st.error(f"圖片暫存至雲端時失敗: {e}")
    return None

if uploaded_file is not None:
    # 畫面左右切分成兩欄：左邊顯示原圖，右邊顯示篩選後的結果數量
    pre_col_left, pre_col_right = st.columns([1, 2.5])
    
    with pre_col_left:
        st.image(uploaded_file, caption="您上傳的原圖", width=250, use_container_width=False)
        st.markdown("<br>", unsafe_allow_html=True)

    # 處理 API Key 檢查
    if search_button:
        if not api_key:
            st.error("請先在左側邊欄輸入或在 .env 檔案中設定您的 SerpAPI Key！")
        else:
            with st.spinner("⏳ 正在上傳圖片並請求 Google Lens 進行視覺辨識..."):
                file_bytes = uploaded_file.getvalue()
                public_url = upload_to_temporary_host(file_bytes, uploaded_file.name)
                
                if public_url:
                    try:
                        client = serpapi.Client(api_key=api_key)
                        results = client.search({
                          "engine": "google_lens",
                          "url": public_url,
                          "type": "products", 
                          "hl": hl,      
                          "country": gl,    
                          "auto_crop": "true",
                          "safe": "off"
                        })
                        
                        # 儲存結果到快取
                        st.session_state["search_results"] = results
                                
                    except Exception as e:
                        st.error(f"呼叫 SerpAPI 發生錯誤: {e}")
                else:
                    st.error("無法將本地圖片轉換為雲端暫存網址，這通常是臨時空間異常，請稍後再試。")

    # ==========================================
    # 視覺化搜尋結果展示區
    # ==========================================
    if "search_results" in st.session_state:
        results = st.session_state["search_results"]
        visual_matches = results.get("visual_matches", [])
        
        if visual_matches:
            # 平台篩選邏輯
            if platform_filter:
                filtered_matches = [
                    item for item in visual_matches
                    if platform_filter.lower() in item.get("source", "").lower()
                ]
                # 用專業一點的文字更新結果數量
                with pre_col_right:
                    st.success(f"找到包含 「{platform_filter}」 的商品共 {len(filtered_matches)} 筆。")
            else:
                filtered_matches = visual_matches
                with pre_col_right:
                    st.success(f"搜尋完成，Google Lens 共識別出 {len(filtered_matches)} 筆相似產品。")

            # 顯示結果 (改為寬網格排版，每排 4 個商品)
            if filtered_matches:
                st.markdown("---")
                # 計算需要多少欄位 (這裡設為 4)
                num_columns = 4
                for i in range(0, len(filtered_matches), num_columns):
                    cols = st.columns(num_columns)
                    
                    for j in range(num_columns):
                        if i + j < len(filtered_matches):
                            item = filtered_matches[i + j]
                            title = item.get("title", "無標題")
                            link = item.get("link", "#")
                            source = item.get("source", "未知來源")
                            thumbnail = item.get("thumbnail")
                            price_info = item.get("price", {})
                            
                            # 使用 markdown + HTML/CSS 畫出卡片
                            with cols[j]:
                                html_content = f"""
                                <div class="product-card">
                                    <div class="product-img-container">
                                        <img src="{thumbnail if thumbnail else '#'}" class="product-img" alt="{title}">
                                    </div>
                                    <a href="{link}" target="_blank" class="product-title">{title}</a>
                                    <span class="source-badge">🏪 {source}</span>
                                """
                                
                                # 只有有價格才顯示
                                if price_info:
                                    price_str = price_info.get("extracted_value", "未標價")
                                    currency = price_info.get("currency", "$")
                                    html_content += f"<p class='price-tag'>{currency} {price_str}</p>"
                                
                                html_content += "</div>"
                                
                                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.warning(f"找不到來源包含「{platform_filter}」的商品，請嘗試在側邊欄修改關鍵字。")
        else:
            st.markdown("---")
            st.warning("Google Lens 沒有辨識出具體的相似產品。")
            with st.expander("🔍 檢視完整 API JSON 回傳原始資料"):
                st.json(results)