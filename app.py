import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

st.title("AI 웹사이트 분석기")

# 파일 업로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

def simple_label(url):
    try:
        html = requests.get(url, timeout=5).text
    except:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    layout = "Grid"
    if len(soup.find_all("div")) > 50:
        layout = "Modular"
    
    text = html.lower()
    visual = []
    
    if "gradient" in text:
        visual.append("Gradient")
    if "blur" in text:
        visual.append("Glassmorphism")
    if not visual:
        visual.append("Minimalism")
    
    return layout, ",".join(visual)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    st.write("데이터 미리보기", df.head())
    
    if st.button("자동 라벨링 시작"):
        results = []
        
        for url in df["URL"]:
            result = simple_label(url)
            results.append(result)
        
        df["Layout"] = [r[0] if r else None for r in results]
        df["Visual"] = [r[1] if r else None for r in results]
        
        st.success("라벨링 완료!")
        
        # 그래프
        st.subheader("Layout 분포")
        st.bar_chart(df["Layout"].value_counts())
        
        # AI 학습
        X = pd.get_dummies(df["Visual"])
        y = pd.get_dummies(df["Layout"])
        
        X_train, X_test, y_train, y_test = train_test_split(X, y)
        
        model = RandomForestClassifier()
        model.fit(X_train, y_train)
        
        acc = model.score(X_test, y_test)
        
        st.write("모델 정확도:", acc)
        
        # 다운로드
        st.download_button(
            "결과 CSV 다운로드",
            df.to_csv(index=False),
            "result.csv"
        )