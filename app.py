import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from sklearn.cluster import KMeans
import plotly.express as px

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# =========================
# 한글 폰트 등록
# =========================
pdfmetrics.registerFont(TTFont("KoreanFont", "NotoSansKR-Regular.ttf"))

# =========================
# 크롤링 함수
# =========================
def crawl(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        return text[:1000]
    except:
        return ""

# =========================
# 간단 라벨링
# =========================
def labeling(text):
    layout = "Grid" if "grid" in text.lower() else "Single"
    visual = "Gradient" if "gradient" in text.lower() else "Minimal"
    tone = "Dark" if "dark" in text.lower() else "Light"
    return layout, visual, tone

# =========================
# 클러스터링
# =========================
def clustering(df):
    df_encoded = pd.get_dummies(df)
    model = KMeans(n_clusters=3, random_state=42)
    df["Cluster"] = model.fit_predict(df_encoded)
    return df

# =========================
# 클러스터 해석
# =========================
def interpret_cluster(df):
    summary = {}
    for c in df["Cluster"].unique():
        subset = df[df["Cluster"] == c]
        summary[c] = {
            "Layout": subset["Layout"].mode()[0],
            "Visual": subset["Visual"].mode()[0],
            "Tone": subset["Tone"].mode()[0]
        }
    return summary

# =========================
# 트렌드 분석
# =========================
def analyze_trend(df):
    return {
        "Layout": df["Layout"].value_counts().idxmax(),
        "Visual": df["Visual"].value_counts().idxmax(),
        "Tone": df["Tone"].value_counts().idxmax()
    }

# =========================
# PDF 생성
# =========================
def create_pdf(report_text):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "KoreanFont"

    content = []
    for line in report_text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)
    return "report.pdf"

# =========================
# UI
# =========================
st.title("AI 디자인 분석기")

urls = st.text_area("URL 여러개 입력 (줄바꿈)")

if st.button("분석 시작"):
    url_list = urls.split("\n")

    data = []

    for url in url_list:
        text = crawl(url)
        layout, visual, tone = labeling(text)
        data.append([layout, visual, tone])

    df = pd.DataFrame(data, columns=["Layout", "Visual", "Tone"])

    df = clustering(df)

    st.write(df)

    # 시각화
    fig = px.scatter(df, x="Layout", y="Visual", color="Cluster")
    st.plotly_chart(fig)

    # 분석
    cluster_summary = interpret_cluster(df)
    trend = analyze_trend(df)

    st.write("클러스터 분석", cluster_summary)
    st.write("트렌드", trend)

    # 리포트 생성
    report = "AI 디자인 분석 리포트\n\n"

    report += "[클러스터 분석]\n"
    for k, v in cluster_summary.items():
        report += f"Cluster {k}\n"
        report += f"Layout: {v['Layout']}\n"
        report += f"Visual: {v['Visual']}\n"
        report += f"Tone: {v['Tone']}\n\n"

    report += "[트렌드]\n"
    report += f"Layout: {trend['Layout']}\n"
    report += f"Visual: {trend['Visual']}\n"
    report += f"Tone: {trend['Tone']}\n"

    st.text(report)

    # PDF 버튼
    if st.button("PDF 생성"):
        pdf_file = create_pdf(report)
        with open(pdf_file, "rb") as f:
            st.download_button("PDF 다운로드", f, "report.pdf")
