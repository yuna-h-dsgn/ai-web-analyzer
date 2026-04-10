import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# ---------------------------
# 기본 설정
# ---------------------------
st.set_page_config(page_title="AI Design Analyzer", layout="wide")

# ---------------------------
# URL 분석
# ---------------------------
def analyze_url(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        text = soup.get_text().lower()

        layout = "Grid" if "grid" in text else "Single"

        length = len(text)
        if length < 5000:
            complexity = "Low"
        elif length < 20000:
            complexity = "Medium"
        else:
            complexity = "High"

        style = "Minimal" if "white" in text else "Visual"

        return {
            "URL": url,
            "Layout": layout,
            "Complexity": complexity,
            "Style": style
        }

    except:
        return None

# ---------------------------
# URL 자동 수집
# ---------------------------
def collect_urls(keyword):
    urls = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        url = f"https://www.google.com/search?q={keyword}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a"):
            link = a.get("href")
            if link and "http" in link and "google" not in link:
                urls.append(link)

    except:
        pass

    return list(set(urls))[:10]

# ---------------------------
# 자동 파이프라인
# ---------------------------
def auto_pipeline(keyword):
    urls = collect_urls(keyword)
    results = []

    for u in urls:
        r = analyze_url(u)
        if r:
            results.append(r)

    return pd.DataFrame(results)

# ---------------------------
# 사이드바
# ---------------------------
st.sidebar.title("설정")

mode = st.sidebar.radio("분석 방식", ["URL 분석", "자동 수집"])

if mode == "URL 분석":
    url = st.sidebar.text_input("URL 입력")

if mode == "자동 수집":
    keyword = st.sidebar.text_input("키워드 입력")

run = st.sidebar.button("분석 시작")

# ---------------------------
# 메인 화면
# ---------------------------
st.title("AI 디자인 분석기")
st.write("웹사이트 디자인을 자동 분석합니다.")

# ---------------------------
# 실행
# ---------------------------
if run:

    with st.spinner("분석 중입니다..."):

        if mode == "URL 분석":
            result = analyze_url(url)
            if result:
                df = pd.DataFrame([result])
            else:
                df = pd.DataFrame()

        else:
            df = auto_pipeline(keyword)

    # ---------------------------
    # 결과 표시
    # ---------------------------
    if df.empty:
        st.warning("결과가 없습니다.")
    else:
        st.subheader("분석 결과")

        style = df["Style"].iloc[0]
        layout = df["Layout"].iloc[0]
        complexity = df["Complexity"].iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric("Style", style)
        col2.metric("Layout", layout)
        col3.metric("Complexity", complexity)

        st.subheader("데이터")
        st.dataframe(df)

        # ---------------------------
        # 차트
        # ---------------------------
        st.subheader("차트")

        fig, ax = plt.subplots()
        df["Layout"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)

        # ---------------------------
        # 클러스터링
        # ---------------------------
        st.subheader("클러스터")

        df["Complexity_num"] = df["Complexity"].map({
            "Low": 1,
            "Medium": 2,
            "High": 3
        })

        if len(df) >= 3:
            kmeans = KMeans(n_clusters=3, n_init=10)
            df["Cluster"] = kmeans.fit_predict(df[["Complexity_num"]])
            st.dataframe(df)

        # ---------------------------
        # 다운로드
        # ---------------------------
        st.subheader("다운로드")

        st.download_button(
            "CSV 다운로드",
            df.to_csv(index=False),
            "result.csv"
        )
