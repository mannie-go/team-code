
import streamlit as st
import json
import pandas as pd
from collections import defaultdict, Counter
import random

st.title("Markov Chain Prediction")
st.write("ระบบทำนายคำถัดไปด้วย Markov Chain")


# อ่านข้อมูลจากไฟล์ raw_data.json
def load_data():
    try:
        with open("data/raw_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    except FileNotFoundError:
        try:
            with open("raw_data.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return None


# แปลงข้อมูลให้อยู่ในรูปแบบข้อความ
def get_text(data):
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        result = []
        for item in data:
            result.append(get_text(item))
        return " ".join(result)

    if isinstance(data, dict):
        if "text" in data:
            return get_text(data["text"])

        result = []
        for value in data.values():
            result.append(get_text(value))
        return " ".join(result)

    return ""


# สร้าง Transition Probability Matrix
def build_matrix(text):
    words = text.split()
    transitions = defaultdict(Counter)

    for i in range(len(words) - 1):
        current = words[i]
        next_word = words[i + 1]
        transitions[current][next_word] += 1

    matrix = {}

    for current, next_words in transitions.items():
        total = sum(next_words.values())

        matrix[current] = {}

        for word, count in next_words.items():
            matrix[current][word] = count / total

    return matrix


# หาคำที่มีโอกาสเป็นคำถัดไปมากที่สุด
def predict_word(matrix, word):
    if word not in matrix:
        return []

    result = sorted(
        matrix[word].items(),
        key=lambda x: x[1],
        reverse=True
    )

    return result


# สร้างประโยคจากคำเริ่มต้น
def generate_text(matrix, start, amount):
    words = start.split()

    for i in range(amount):
        current = words[-1]

        predictions = predict_word(matrix, current)

        if not predictions:
            break

        next_words = [x[0] for x in predictions]
        probabilities = [x[1] for x in predictions]

        next_word = random.choices(
            next_words,
            weights=probabilities,
            k=1
        )[0]

        words.append(next_word)

    return " ".join(words)


# ส่วนแสดงผลหน้าเว็บ
data = load_data()

if data is not None:

    st.subheader("เลือกชุดข้อมูล")

    if isinstance(data, dict):
        dataset_names = list(data.keys())

        selected = st.selectbox(
            "เลือก Dataset",
            dataset_names
        )

        text = get_text(data[selected])

    else:
        text = get_text(data)

    st.text_area(
        "ข้อมูลที่เลือก",
        text[:1000],
        height=120
    )

    if st.button("สร้าง Matrix"):

        if text.strip():
            st.session_state.matrix = build_matrix(text)
            st.success("สร้าง Matrix เรียบร้อยแล้ว")
        else:
            st.warning("ไม่พบข้อมูลใน Dataset")

else:
    st.warning("ไม่พบไฟล์ raw_data.json")
    text = st.text_area("กรอกข้อความเพื่อใช้เป็นข้อมูล")

    if st.button("สร้าง Matrix"):
        if text.strip():
            st.session_state.matrix = build_matrix(text)
            st.success("สร้าง Matrix เรียบร้อยแล้ว")
        else:
            st.warning("กรุณากรอกข้อมูลก่อน")


# แสดง Matrix และทำนายคำ
if "matrix" in st.session_state:

    matrix = st.session_state.matrix

    st.subheader("Transition Probability Matrix")

    df = pd.DataFrame(matrix).T.fillna(0)

    st.dataframe(
        df.style.format("{:.3f}"),
        use_container_width=True
    )

    st.divider()

    st.subheader("ทำนายคำถัดไป")

    start = st.text_input(
        "กรอกคำเริ่มต้น",
        placeholder="เช่น I love"
    )

    amount = st.slider(
        "จำนวนคำที่ต้องการทำนาย",
        1, 20, 5
    )

    if st.button("ทำนาย"):

        if start.strip():

            current = start.split()[-1]
            result = predict_word(matrix, current)

            if result:

                st.write("คำที่มีโอกาสเป็นคำถัดไป")

                prediction_df = pd.DataFrame(
                    result,
                    columns=["คำถัดไป", "Probability"]
                )

                prediction_df["Probability (%)"] = (
                    prediction_df["Probability"] * 100
                ).round(2)

                st.dataframe(
                    prediction_df[
                        ["คำถัดไป", "Probability (%)"]
                    ],
                    use_container_width=True
                )

                sentence = generate_text(
                    matrix,
                    start,
                    amount
                )

                st.write("ประโยคที่ระบบทำนายได้")
                st.success(sentence)

            else:
                st.warning("ไม่พบคำนี้ในชุดข้อมูล")

        else:
            st.warning("กรุณากรอกคำเริ่มต้น")
