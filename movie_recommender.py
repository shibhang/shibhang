import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import requests

class MovieRecommender:
    def __init__(self):
        self.tfidf_matrix = None
        self.tfidf_vectorizer = None
        self.data = None
        
    def load_data(self, file_path):
        self.data = pd.read_csv(file_path)
        
    def preprocess_data(self):
        if self.data is not None:
            self.data.dropna(subset=['plot_keywords'], inplace=True)  
            self.data.drop_duplicates(inplace=True)
            selected_columns = ['movie_title', 'director_name', 'actor_1_name', 'actor_2_name', 'actor_3_name', 'genres', 'country', 'plot_keywords', 'title_year', 'imdb_score', 'movie_imdb_link','duration']
            self.data = self.data[selected_columns]
            self.data['combined_features'] = self.data.apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
            
    def train_model(self):
        if self.data is not None:
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.data['combined_features'])
            
    def save_model(self, vectorizer_file):
        if self.tfidf_vectorizer:
            joblib.dump(self.tfidf_vectorizer, vectorizer_file)
            
    def load_model(self, vectorizer_file):
        self.tfidf_vectorizer = joblib.load(vectorizer_file)
    
    def fetch_youtube_trailer(self, movie_title):
        try:
            query = f"{movie_title} official trailer"
            response = requests.get("https://www.googleapis.com/youtube/v3/search", params={
                "q": query,
                "part": "snippet",
                "type": "video",
                "key": "AIzaSyBq699wuEgooivSg57hd8WF2pIYlP_sYls",  
            })
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    # Extract video ID of the first search result
                    return data['items'][0]['id']['videoId']
            return None
        except requests.RequestException as e:
            print("Error fetching YouTube trailer:", e)
            return None

        
    def fetch_imdb_details(self, imdb_link):
        try:
            imdb_id = imdb_link.split('/')[-2]  
            omdb_api_url = f'http://www.omdbapi.com/?i={imdb_id}&apikey=5305d87f'  
            response = requests.get(omdb_api_url)
            if response.status_code == 200:
                movie_data = response.json()
                poster_url = movie_data.get('Poster', '')
                return poster_url
            else:
                print("Failed to fetch movie information from OMDB API.")
                return ''
        except requests.RequestException as e:
            print("Error fetching data:", e)
            return ''

        
    def get_recommendation_details(self, movie_title):
        imdb_link = self.data[self.data['movie_title'] == movie_title]['movie_imdb_link'].iloc[0]
        poster_url = self.fetch_imdb_details(imdb_link)
        if not poster_url:
            trailer_id = self.fetch_youtube_trailer(movie_title)
            return None, trailer_id
        return poster_url, None


    def recommend_movies(self, movie_title, location=None, num_recommendations=12):
        if self.tfidf_matrix is not None and self.tfidf_vectorizer:
            input_vector = self.tfidf_vectorizer.transform([movie_title])
            cosine_similarities = cosine_similarity(input_vector, self.tfidf_matrix)
            related_indices = cosine_similarities.argsort()[0][-num_recommendations - 1:][::-1]
            recommended_movies = self.data.iloc[related_indices]
            
            if location:
                location_lower = location.lower()  
                recommended_movies = recommended_movies[recommended_movies['country'].str.lower() == location_lower]
                
            searched_movie_row = recommended_movies[recommended_movies['movie_title'] == movie_title]
            recommended_movies = recommended_movies[recommended_movies['movie_title'] != movie_title]
            recommended_movies = recommended_movies.head(num_recommendations - 1)
            recommended_movies = pd.concat([searched_movie_row, recommended_movies])
            
            # Sort recommended movies by IMDb score
            recommended_movies = recommended_movies.sort_values(by=['imdb_score'], ascending=[False])
            
            return recommended_movies[['movie_title']].to_dict('records')
        else:
            print("Model has not been trained or loaded yet.")
            return []

    def get_recommendations_with_trailer(self, movie_title, location=None, num_recommendations=12):
        recommendations = self.recommend_movies(movie_title, location, num_recommendations)
        for movie in recommendations:
            poster_url, trailer_id = self.get_recommendation_details(movie['movie_title'])
            movie['poster'] = poster_url
            movie['trailer_id'] = trailer_id if trailer_id else ''  
        return recommendations

    
    def get_auto_recommendations(self, location=None, num_recommendations=12):
        if self.data is not None:
            if location:
                location_lower = location.lower()  
                auto_recommendations = self.data[self.data['country'].str.lower() == location_lower].head(num_recommendations)
            else:
                auto_recommendations = self.data.head(num_recommendations)
            
            auto_recommendations_with_posters = []
            for _, row in auto_recommendations.iterrows():
                poster_url, trailer_id = self.get_recommendation_details(row['movie_title'])
                if not trailer_id:
                    trailer_id = self.fetch_youtube_trailer(row['movie_title'])
                if poster_url:
                    movie_details = {
                        'movie_title': row['movie_title'],
                        'poster': poster_url,
                        'trailer_id': trailer_id,
                        'imdb_score': row.get('imdb_score', 0)  
                    }
                    auto_recommendations_with_posters.append(movie_details)
            
            # Sort auto-recommended movies by IMDb score if it exists
            auto_recommendations_with_posters = sorted(auto_recommendations_with_posters, key=lambda x: x.get('imdb_score', 0), reverse=True)
            
            return auto_recommendations_with_posters
        else:
            print("Data has not been loaded yet.")
            return []

    def get_filtered_recommendations(self, filter_type, filter_value, num_recommendations=24):
        if self.data is not None:
            filtered_movies = None
            if filter_type == "genre":
                filtered_movies = self.data[self.data['genres'].str.contains(filter_value, case=False)]
            elif filter_type == "country":
                filtered_movies = self.data[self.data['country'].str.lower() == filter_value.lower()]
            
            if filtered_movies is not None:
                recommendations = filtered_movies.head(num_recommendations)
                recommendations_with_posters = []
                for _, row in recommendations.iterrows():
                    poster_url, trailer_id = self.get_recommendation_details(row['movie_title'])
                    if not trailer_id:
                        trailer_id = self.fetch_youtube_trailer(row['movie_title'])
                    if poster_url:
                        movie_details = {
                            'movie_title': row['movie_title'],
                            'poster': poster_url,
                            'trailer_id': trailer_id,
                            'imdb_score': row.get('imdb_score', 0)  
                        }
                        recommendations_with_posters.append(movie_details)
                    
                # Sort filtered recommendations by IMDb score
                recommendations_with_posters = sorted(recommendations_with_posters, key=lambda x: x.get('imdb_score', 0), reverse=True)
                
                return recommendations_with_posters
            else:
                return []
        else:
            print("Data has not been loaded yet.")
            return []

    def get_filtered_recommendations_by_year(self, year, num_recommendations=24):
        if self.data is not None:
            year = int(year)
            filtered_movies = self.data[self.data['title_year'] == year].head(num_recommendations)
        
            filtered_recommendations_with_posters = []
            for _, row in filtered_movies.iterrows():
                poster_url, trailer_id = self.get_recommendation_details(row['movie_title'])
                if not trailer_id:
                    trailer_id = self.fetch_youtube_trailer(row['movie_title'])
                if poster_url:
                    movie_details = {
                        'movie_title': row['movie_title'],
                        'poster': poster_url,
                        'trailer_id': trailer_id,
                        'imdb_score': row.get('imdb_score', 0)  
                    }
                    filtered_recommendations_with_posters.append(movie_details)
                
            # Sort filtered recommendations by IMDb score
            filtered_recommendations_with_posters = sorted(filtered_recommendations_with_posters, key=lambda x: x.get('imdb_score', 0), reverse=True)
                
            return filtered_recommendations_with_posters
        else:
            print("Data has not been loaded yet.")
            return []

    def fetch_trailer(self, movie_title):
        try:
            imdb_link = self.data[self.data['movie_title'] == movie_title]['movie_imdb_link'].iloc[0]
            poster_url = self.fetch_imdb_details(imdb_link)
            trailer_id = self.fetch_youtube_trailer(movie_title)
            top_cast = "Top Cast: " + self.data[self.data['movie_title'] == movie_title]['actor_1_name'].iloc[0] + ", " + self.data[self.data['movie_title'] == movie_title]['actor_2_name'].iloc[0] + ", " + self.data[self.data['movie_title'] == movie_title]['actor_3_name'].iloc[0]
            director = "Director: " + self.data[self.data['movie_title'] == movie_title]['director_name'].iloc[0]
            country = "Country: " + self.data[self.data['movie_title'] == movie_title]['country'].iloc[0]
            genre = "Genre: " + self.data[self.data['movie_title'] == movie_title]['genres'].iloc[0]
            
            # Convert duration to hours and minutes
            duration_minutes = int(self.data[self.data['movie_title'] == movie_title]['duration'].iloc[0])
            duration_hours = duration_minutes // 60
            duration_minutes %= 60
            runtime = "Runtime: {} hr {} min".format(duration_hours, duration_minutes)
            
            imdb_score = "IMDB Score: " + str(self.data[self.data['movie_title'] == movie_title]['imdb_score'].iloc[0])
            
            movie_details = {
                'movie_title': movie_title,
                'top_cast': top_cast,
                'director': director,
                'country': country,
                'genre': genre,
                'runtime': runtime,
                'imdb_score': imdb_score,
                'poster': poster_url,
                'trailer_id': trailer_id  
            }
            return movie_details
        except IndexError:
            print("Movie not found in the dataset.")
            return None

