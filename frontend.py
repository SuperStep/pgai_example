import streamlit as st
import psycopg2

def connect_to_db():
    """Connect to PostgreSQL database and return connection and cursor"""
    conn = psycopg2.connect("host=localhost port=5432 dbname=postgres user=postgres password=postgres")
    cur = conn.cursor()
    return conn, cur

def query_rag_response(input_text):
    """Query the database to get RAG response using the PostgreSQL function"""
    conn, cur = connect_to_db()
    try:
        # Call the PostgreSQL function that generates RAG response
        cur.execute("SELECT query_impact(%s);", (input_text,))
        result = cur.fetchone()[0]  # Get the first column of the first row
        return result
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cur.close()
        conn.close()

def find_rag_documents(input_text):
    """Query the database to get RAG documents using the PostgreSQL function"""
    conn, cur = connect_to_db()
    try:
        # Call the PostgreSQL function that finds relevant content
        cur.execute("SELECT path, chunk FROM find_rag_content(%s);", (input_text,))
        # Fetch all rows instead of just the first one
        results = cur.fetchall()
        return results
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cur.close()
        conn.close()

# Set up the Streamlit app
st.title("База знаний SWTR")

# Create input field for the query
user_query = st.text_area("Задайте вопрос: ", height=100)

# Create button to submit the query
if st.button("Спросить"):
    if user_query:
        with st.spinner("Отвечаем..."):
            # Call the function to get response
            response = query_rag_response(user_query)
            
            # Display the response
            st.subheader("Ответ:")
            st.text_area("", value=response, height=300, disabled=True)
    else:
        st.error("Сначала введите запрос.")

# Create button to submit the query for finding files
if st.button("Найти файлы"):
    if user_query:
        with st.spinner("Ищем..."):
            # Call the function to get documents
            documents = find_rag_documents(user_query)
            
            # Display the results in a table
            st.subheader("Найденные документы:")
            if isinstance(documents, str) and documents.startswith("Error"):
                st.error(documents)
            else:
                # Create a DataFrame for better display
                import pandas as pd
                if documents:
                    df = pd.DataFrame(documents, columns=["Путь к файлу", "Фрагмент"])
                    st.dataframe(df)
                else:
                    st.info("Документы не найдены.")
    else:
        st.error("Сначала введите запрос.")

# Add some information about the application
st.sidebar.header("Что это такое?")
st.sidebar.info(
    "В это интефейс опроса модели обогощенной исходным кодобазой репозитория SWTR."
)