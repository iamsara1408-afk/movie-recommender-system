

import pickle
import requests
import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)

# --------------------------------------------------
# Load the trained model files
# --------------------------------------------------
@st.cache_resource
def load_data():
    with open("model/movie_list.pkl", "rb") as file:
        movies = pickle.load(file)

    with open("model/similarity.pkl", "rb") as file:
        similarity = pickle.load(file)

    return movies, similarity


movies, similarity = load_data()


# --------------------------------------------------
# Fetch a movie poster from Wikimedia Commons
# --------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_poster(movie_title):
    try:
        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f'"{movie_title}" movie poster',
            "gsrnamespace": 6,
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 300,
            "format": "json"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "MovieRecommenderStudentProject/1.0"
            }
        )
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", {})

        # Return the first image result available
        for page in pages.values():
            image_info = page.get("imageinfo", [{}])[0]
            image_url = (
                image_info.get("thumburl")
                or image_info.get("url")
            )

            if image_url:
                return image_url

    except (requests.RequestException, ValueError, KeyError):
        pass

    return None


# --------------------------------------------------
# Recommend five similar movies
# --------------------------------------------------
def recommend(movie_title):
    matching_movies = movies[
        movies["title"] == movie_title
    ]

    if matching_movies.empty:
        return []

    movie_index = matching_movies.index[0]

    distances = sorted(
        list(enumerate(similarity[movie_index])),
        key=lambda x: x[1],
        reverse=True
    )

    recommendations = []

    # Skip the selected movie itself
    for index, score in distances[1:6]:
        recommended_title = movies.iloc[index]["title"]

        poster_url = fetch_poster(recommended_title)

        recommendations.append(
            (recommended_title, poster_url)
        )

    return recommendations


# --------------------------------------------------
# Streamlit website
# --------------------------------------------------
st.title("🎬 Movie Recommender System")
st.write("Select a movie you like to discover five similar movies.")

movie_list = movies["title"].dropna().tolist()

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button("Show Recommendation", type="primary"):
    with st.spinner("Finding movies and searching for posters..."):
        recommendations = recommend(selected_movie)

    if not recommendations:
        st.error("No recommendations found. Please select another movie.")
    else:
        st.subheader("Recommended Movies")

        columns = st.columns(5)

        for column, (title, poster_url) in zip(
            columns, recommendations
        ):
            with column:
                st.markdown(f"**{title}**")

                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.caption("Poster unavailable")



