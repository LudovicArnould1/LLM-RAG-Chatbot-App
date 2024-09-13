import requests
import streamlit as st

from config_front import Config

# Retrieve the API_URL from the configuration
QUERY_URL = Config.get_backend_url() + "/query"
FEEDBACK_URL = Config.get_backend_url() + "/feedback"

st.title("Training Recommendation Assistant")

# Initialize session state if not already done
if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = ""
if "documents" not in st.session_state:
    st.session_state["documents"] = []
if "feedback" not in st.session_state:
    st.session_state["feedback"] = ""
if "selected_document" not in st.session_state:
    st.session_state["selected_document"] = ""

# Function to fetch recommendations
def fetch_recommendations() -> None:
    """Fetch recommendations based on the user query."""
    if st.session_state["user_query"]:
        # Prepare the request payload
        payload = {"query": st.session_state["user_query"]}

        # Send the request to the FastAPI backend
        with st.spinner("Fetching recommendations..."):
            try:
                response = requests.post(QUERY_URL, json=payload, timeout=90)
                response.raise_for_status()  # Raise an error for bad responses
                data = response.json()
                st.session_state["recommendations"] = data.get("answer",
                                                               "No answer received")
                st.session_state["documents"] = data.get("documents", [])
                st.session_state["document_titles"] = extract_titles(
                    st.session_state["documents"],
                )
                st.session_state["selected_document"] = ""
                st.success("Recommendations fetched successfully!")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
    else:
        st.warning("Please enter a query.")


def extract_titles(documents : list[str]) -> list[str]:
    """Extract titles from the given documents."""
    titles = []
    for doc in documents:
        lines = doc.split("\n")
        for line in lines:
            if line.startswith("Title: "):
                title = line.replace("Title: ", "").strip()
                titles.append(title)
                break
    return titles


# User input for query
user_query = st.text_input("Enter your query:", st.session_state["user_query"])

if st.button("Get Recommendations"):
    st.session_state["user_query"] = user_query
    fetch_recommendations()

# Display recommendations and documents
if st.session_state["recommendations"]:
    st.subheader("Recommendations")
    st.write(st.session_state["recommendations"])

    st.subheader("Related Documents")

    doc_titles = [""] + st.session_state["document_titles"]

    selected_title = st.selectbox("Select a document to view its content",
                                  doc_titles)

    if selected_title:
        selected_index = doc_titles.index(selected_title) -1
        st.session_state["selected_document"] = (
            st.session_state["documents"][selected_index]
        )

        if st.session_state["selected_document"]:
            st.markdown(st.session_state["selected_document"].replace("\n",
                                                                      "\n\n"))

    st.subheader("Feedback")
    feedback = st.radio("How would you rate this answer?", ("positive",
                                                            "neutral", "negative"))

    if st.button("Submit Feedback"):
        feedback_payload = {"query": st.session_state["user_query"],
                            "feedback": feedback}
        try:
            feedback_response = requests.post(FEEDBACK_URL,
                                              json=feedback_payload, timeout=10)
            feedback_response.raise_for_status()  # Raise an error for bad responses
            st.success("Feedback submitted successfully!")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
