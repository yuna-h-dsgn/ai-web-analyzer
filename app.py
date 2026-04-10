import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from fpdf import FPDF

# ---------------------------
# 기본 설정
# ---------------------------
st.set_page_config(page_title="AI Design Analyzer", layout="wide")

# ---------------------------
# 스타일 (SaaS 느낌)
# ---------------------------
st.markdown("""
<style>
body {
    background-color: #ffffff;
}
.block {
    padding:16px;
    border-radius:10px;
    border:1px solid #e5e7eb;
    margin-bottom:10px;
    background:white;
}
.small {
    font-size:13px;
    color:gray;
}
.big {
    font-size:22px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# 블록 UI
# ---------------------------
def block(title, value):
    st.markdown(f"""
    <div class="block">
        <div class="small">{title}</div>
        <div class="big">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# URL 크롤링
# ---------------------------
def analyze_url(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        texts = soup.get_text().lower()

        # 간단 룰 기반 분석
        layout = "Grid" if "grid" in texts else "Single"
        complexity = len(texts)

        if complexity < 5000:
            complexity_label = "Low"
        elif complexity < 20000:
            complexity_label = "Medium"
        else:
            complexity_label = "High"

        style = "Minimal" if "white" in texts else "Visual"

        return {
            "URL": url,
            "Layout": layout,
            "Complexity": complexity_label,
            "Style": style
        }

    except:
        return None

# ---------------------------
# URL 자동 수집
# ---------------------------
def collect_urls(keyword, num=10):
    urls = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        search_url = f"https://www.google.com/search?q={keyword}"
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a"):
            link = a.get("href")
            if link and "http" in link and "google" not in link:
                urls.append(link)

    except:
        pass

    return list(set(urls))[:num]

# ---------------------------
# 데이터 생성
# ---------------------------
def auto_pipeline(keyword):
    urls = collect_urls(keyword)
    data = []

    for u in urls:
        result = analyze_url(u)
        if result:
            data.append(result)

    df = pd.DataFrame(data)
    return df

# ---------------------------
# PDF 생성
# ---------------------------
def make_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for i, row in df.iterrows():
        pdf.cell(200, 8, txt=str(row.values), ln=True)

    pdf.output("report.pdf")

# ---------------------------
# 사이드바
# ---------------------------
with st.sidebar:
    st.title("🎨 Design AI")

    mode = st.radio("Mode", ["URL 분석", "자동 수집"])

    if mode == "URL 분석":
        url = st.text_input("URL 입력")

    if mode == "자동 수집":
        keyword = st.text_input("키워드 입력")

    run = st.button("🚀 분석 시작")

# ---------------------------
# 메인 UI
# ---------------------------
st.title("AI Design Analyzer Dashboard")
st.markdown("디자인을 자동 분석하고 인사이트를 제공합니다.")

# ---------------------------
# 실행
# ---------------------------
if run:
    with st.spinner("분석 중..."):

        if mode == "URL 분석":
            result = analyze_url(url)
            df = pd.DataFrame([result])

        else:
            df = auto_pipeline(keyword)

    # ---------------------------
    # Insight
    # ---------------------------
    st.markdown("## 🧠 Insight")

    if not df.empty:
        style = df["Style"].iloc[0]
        layout = df["Layout"].iloc[0]
        complexity = df["Complexity"].iloc[0]

        st.write(f"""
        이 디자인은 **{style} 스타일**이며  
        **{layout} 레이아웃** 구조를 가지고 있습니다.  
        복잡도는 **{complexity} 수준**입니다.
        """)

    # ---------------------------
    # 요약 블록
    # ---------------------------
    st.markdown("## 📊 Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        block("Style", df["Style"].iloc[0] if not df.empty else "-")

    with col2:
        block("Layout", df["Layout"].iloc[0] if not df.empty else "-")

    with col3:
        block("Complexity", df["Complexity"].iloc[0] if not df.empty else "-")

    # ---------------------------
    # 데이터 테이블
    # ---------------------------
    st.markdown("## 📄 Data")
    st.write(df)

    # ---------------------------
    # 차트
    # ---------------------------
    st.markdown("## 📈 Visualization")

    if not df.empty:
        fig, ax = plt.subplots()
        df["Layout"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)

    # ---------------------------
    # 클러스터링
    # ---------------------------
    st.markdown("## 🧩 Clustering")

    if not df.empty:
        df["Complexity_num"] = df["Complexity"].map({
            "Low": 1,
            "Medium": 2,
            "High": 3
        })

        if len(df) >= 3:
            kmeans = KMeans(n_clusters=3, n_init=10)
            df["Cluster"] = kmeans.fit_predict(df[["Complexity_num"]])
            st.write(df)

    # ---------------------------
    # 다운로드
    # ---------------------------
    st.markdown("## 📥 Export")

    st.download_button(
        "CSV 다운로드",
        df.to_csv(index=False),
        "result.csv"
    )

    if st.button("PDF 생성"):
        make_pdf(df)
        st.success("PDF 생성 완료")
