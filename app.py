import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
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
# 크롤링 (텍스트 + 이미지)
# =========================
def crawl(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()

        # 이미지 URL 수집
        imgs = [img.get("src") for img in soup.find_all("img") if img.get("src")]

        return text[:2000], imgs[:5]
    except:
        return "", []

# =========================
# 고급 라벨링 (텍스트 기반)
# =========================
def labeling(text):
    text = text.lower()

    layout = "Grid" if any(k in text for k in ["grid", "column", "flex", "layout"]) else "Single"

    visual = "Gradient" if any(k in text for k in ["gradient", "rgb", "color", "background"]) else "Minimal"

    tone = "Dark" if any(k in text for k in ["dark", "black", "#000"]) else "Light"

    return layout, visual, tone

# =========================
# HTML 구조 분석
# =========================
def analyze_html(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        divs = len(soup.find_all("div"))
        imgs = len(soup.find_all("img"))

        complexity = "Complex" if divs > 100 else "Simple"
        media = "Image-heavy" if imgs > 20 else "Text-heavy"

        return complexity, media
    except:
        return "Unknown", "Unknown"

# =========================
# 이미지 분석
# =========================
def analyze_image(img_url):
    try:
        if not img_url.startswith("http"):
            return "Unknown"

        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))

        colors = img.getcolors(1000000)

        if colors and len(colors) > 200:
            return "Rich"
        else:
            return "Minimal"
    except:
        return "Unknown"

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
st.title("AI 디자인 분석기 (고급 버전)")

urls = st.text_area("URL 여러개 입력 (줄바꿈)")

if "report" not in st.session_state:
    st.session_state.report = None

if st.button("분석 시작"):
    url_list = urls.split("\n")

    data = []

    for url in url_list:
        text, imgs = crawl(url)

        layout, visual, tone = labeling(text)
        complexity, media = analyze_html(url)

        img_result = "Unknown"
        if imgs:
            img_result = analyze_image(imgs[0])

        data.append([layout, visual, tone, complexity, media, img_result])

    df = pd.DataFrame(data, columns=["Layout", "Visual", "Tone", "Complexity", "Media", "Image"])

    df = clustering(df)

    st.write(df)

    fig = px.scatter(df, x="Layout", y="Visual", color="Cluster")
    st.plotly_chart(fig)

    cluster_summary = interpret_cluster(df)
    trend = analyze_trend(df)

    report = "AI 디자인 분석 리포트 (고급)\n\n"

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

    st.session_state.report = report

if st.session_state.report:
    st.text(st.session_state.report)

    if st.button("PDF 생성"):
        pdf_file = create_pdf(st.session_state.report)

        with open(pdf_file, "rb") as f:
            st.download_button("PDF 다운로드", f, "report.pdf")
