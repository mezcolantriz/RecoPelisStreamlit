import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googletrans import Translator
import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# Cargar el dataset limpio
df = pd.read_csv("src/movies_cleaned.csv")

# Configurar vectorizador
vectorizer = CountVectorizer(max_features=5000, stop_words="english")
vectors = vectorizer.fit_transform(df["tags"])  # Matriz dispersa (usando 'tags')

# Matriz de similitud
similarity_matrix = cosine_similarity(vectors)

# Configurar traducción
translator = Translator()

# Obtener póster
def get_poster(title):
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return None
    base_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": title}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            poster_path = data["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None

# Recomendador
def recommend(movie_title):
    try:
        translated_title = translator.translate(movie_title, src="es", dest="en").text.lower()
    except:
        translated_title = movie_title.lower()

    movie_index = df[df['title'].str.lower() == translated_title].index
    if not movie_index.empty:
        movie_list = similarity_matrix[movie_index[0]]
        movie_list = sorted(list(enumerate(movie_list)), reverse=True, key=lambda x: x[1])[1:6]
        recommendations = [(df.iloc[i[0]].title, get_poster(df.iloc[i[0]].title)) for i in movie_list]
    else:
        recommendations = [("No encontrado", None)]
    return recommendations

# Interfaz de Streamlit
st.title("Recomendador de Películas")

# Input del usuario
movie_title = st.text_input("Introduce el título de una película:", "")

if movie_title:
    recommendations = recommend(movie_title)

    if recommendations[0][0] == "No encontrado":
        st.warning("No he encontrado la película.")
        st.video("https://www.youtube.com/embed/xesksy_X7Lw?si=4_inSBeJ39yDMesm")
    else:
        st.subheader(f"Recomendaciones para '{movie_title}':")
        for title, poster in recommendations:
            if poster:
                st.image(poster, caption=title)
            else:
                st.write(f"🎬 {title}")

