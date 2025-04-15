import streamlit as st
import pandas as pd
from database import init_db, get_user, save_dataset, load_dataset
from data_cleaning import clean_data
from data_visualization import generate_visualizations
from ai_assistant import AIChatAssistant
from utils import generate_summary_statistics

def main():
    st.set_page_config(page_title="DataBot: Data Cleaning & Visualization Assistant", layout="wide")
    st.title("DataBot: Data Cleaning & Visualization Assistant")

    # Initialize database
    init_db()

    # User login
    username = st.sidebar.text_input("Enter your username", key="username")
    if not username:
        st.sidebar.warning("Please enter a username to continue.")
        return

    user = get_user(username)
    if not user:
        st.sidebar.info(f"New user detected. Creating profile for '{username}'.")
        user = get_user(username, create=True)

    st.sidebar.write(f"Logged in as: **{username}**")

    # Dataset upload or load
    st.sidebar.header("Upload or Load Dataset")
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    saved_datasets = load_dataset(user.id, list_only=True)
    selected_dataset = st.sidebar.selectbox("Or select saved dataset", options=[""] + saved_datasets)

    df = None
    dataset_name = None

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        dataset_name = uploaded_file.name
        st.sidebar.success(f"Loaded dataset from file: {dataset_name}")
    elif selected_dataset:
        df = load_dataset(user.id, dataset_name=selected_dataset)
        dataset_name = selected_dataset
        st.sidebar.success(f"Loaded saved dataset: {dataset_name}")

    if df is None:
        st.info("Please upload a CSV file or select a saved dataset to begin.")
        return

    # Show data overview tab
    tab1, tab2, tab3 = st.tabs(["Data Overview", "Data Cleaning Report", "Visualizations & AI Assistant"])

    with tab1:
        st.header("Data Overview")
        st.write("Raw Data")
        st.dataframe(df)
        st.write("Data Types")
        st.write(df.dtypes)
        st.write("Summary Statistics")
        summary_stats = generate_summary_statistics(df)
        st.write(summary_stats)

    # Data cleaning
    with tab2:
        st.header("Data Cleaning Report")
        if st.button("Run Automated Data Cleaning"):
            cleaned_df, cleaning_report = clean_data(df)
            st.write("Cleaning Report")
            st.json(cleaning_report)
            st.write("Cleaned Data")
            st.dataframe(cleaned_df)
            # Save cleaned dataset
            save_dataset(user.id, dataset_name + "_cleaned.csv", cleaned_df)
        else:
            st.info("Click the button to run automated data cleaning.")

    # Visualizations and AI assistant
    with tab3:
        st.header("Visualizations & AI Assistant")
        cleaned_df = None
        if st.button("Load Cleaned Dataset for Visualization"):
            cleaned_df = load_dataset(user.id, dataset_name=dataset_name + "_cleaned.csv")
            if cleaned_df is not None:
                st.success("Loaded cleaned dataset.")
            else:
                st.warning("No cleaned dataset found. Please run data cleaning first.")
        if cleaned_df is not None:
            st.subheader("Automatic Visualizations")
            generate_visualizations(cleaned_df)
            st.subheader("AI Assistant Chat")
            assistant = AIChatAssistant(user.id, cleaned_df)
            assistant.chat_interface()

if __name__ == "__main__":
    main()
