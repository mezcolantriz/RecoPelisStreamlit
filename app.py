import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración inicial de la página
st.set_page_config(
    page_title="🎬 Recomendador de Películas",
    page_icon="🎥",
    layout="wide"
)

# Estilos personalizados con animaciones y fuentes
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-image: url('https://images.unsplash.com/photo-1524985069026-dd778a71c7b4');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #ffffff;
        }
        .recommendation-box {
            background-color: rgba(0, 0, 0, 0.8);
            border-radius: 15px;
            padding: 20px;
            margin: 10px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeIn 1s ease-in-out;
        }
        .recommendation-box:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(255, 165, 0, 0.8);
        }
        .recommendation-box img {
            border-radius: 10px;
            transition: transform 0.2s ease;
        }
        .recommendation-box img:hover {
            transform: scale(1.1);
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .stButton > button {
            background-color: #ffa500;
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            padding: 10px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #ff6347;
            transform: scale(1.05);
            box-shadow: 0px 4px 8px rgba(255, 99, 71, 0.6);
        }
        .title {
            color: #ffa500;
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
            text-align: center;
        }
        .movie-title {
            color: #ffa500;
            font-size: 1.2em;
            margin-top: 10px;
        }
        .movie-links a {
            color: #ffa500;
            text-decoration: none;
            font-size: 1em;
        }
        .movie-links a:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# Título de la app
st.markdown("<h1 class='title'>🎬 Recomendador de Películas 🎥</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Encuentra tu próxima película favorita</p>", unsafe_allow_html=True)

# Cargar dataset
df = pd.read_csv("src/movies_cleaned.csv")

# Configurar el vectorizador y la matriz de similitud
vectorizer = CountVectorizer(max_features=5000, stop_words="english")
vectors = vectorizer.fit_transform(df["tags"])
similarity_matrix = cosine_similarity(vectors)

# Función para obtener póster, enlace TMDB y tráiler
def get_poster_link_and_trailer(title):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": title}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                poster_path = data["results"][0].get("poster_path")
                movie_id = data["results"][0].get("id")
                tmdb_url = f"https://www.themoviedb.org/movie/{movie_id}?language=es"
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=es"
                video_response = requests.get(video_url)
                if video_response.status_code == 200:
                    video_data = video_response.json()
                    if video_data["results"]:
                        trailer_key = video_data["results"][0].get("key")
                        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}"
                        return poster_url, tmdb_url, trailer_url
                return poster_url, tmdb_url, None
    except Exception as e:
        print(f"Error al obtener el póster: {e}")
    return None, None, None

# Función para obtener recomendaciones
def recommend(movie_title):
    movie_index = df[df['title'].str.lower() == movie_title.lower()].index
    if not movie_index.empty:
        movie_list = similarity_matrix[movie_index[0]]
        movie_list = sorted(list(enumerate(movie_list)), reverse=True, key=lambda x: x[1])[1:6]
        recommendations = []
        for i in movie_list:
            title = df.iloc[i[0]].title
            poster, link, trailer = get_poster_link_and_trailer(title)
            recommendations.append((title, poster, link, trailer))
        return recommendations
    return [("No encontrado", None, None, None)]

# Manejar estado persistente para la película seleccionada
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# Input de búsqueda con autocompletado
movie_query = st.text_input("Busca una película para empezar 🎥:")

# Mostrar sugerencias debajo del buscador
if movie_query:
    suggestions = df[df["title"].str.contains(movie_query, case=False, na=False)].head(5)["title"].tolist()
    if suggestions:
        st.markdown("### Sugerencias: Elige la tuya")
        for suggestion in suggestions:
            if st.button(suggestion):
                st.session_state.selected_movie = suggestion
    else:
        st.warning("Mezcosorrys, no he encontrado nada, quizás no tenga la película en mi base :( Recuerda buscar siempre en inglés.")

# Determinar qué película usar para recomendaciones
selected_movie = st.session_state.selected_movie or movie_query

# Mostrar recomendaciones basadas en la película seleccionada
if selected_movie and selected_movie in df["title"].values:
    recommendations = recommend(selected_movie)

    if recommendations[0][0] == "No encontrado":
        st.warning("No se encontraron resultados. Intenta con otro título.")
    else:
        st.markdown(f"<h3 style='color: #ffa500;'>Recomendaciones para: {selected_movie}</h3>", unsafe_allow_html=True)
        cols = st.columns(5)
        for idx, (title, poster, link, trailer) in enumerate(recommendations):
            with cols[idx]:
                if st.button(f"Ver recomendaciones de: {title}"):
                    st.session_state.selected_movie = title  # Actualiza la película seleccionada
                if poster:
                    st.markdown(
                        f"""
                        <div class="recommendation-box">
                            <img src="{poster}" alt="{title}" style="width: 100%; height: auto;">
                            <h4 class="movie-title">{title}</h4>
                            <div class="movie-links">
                                <a href="{link}" target="_blank">Ver ficha en TMDB</a><br>
                                <a href="{trailer}" target="_blank">🎥 Ver tráiler</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
