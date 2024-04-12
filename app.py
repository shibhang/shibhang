from flask import Flask, render_template, request, jsonify
from movie_recommender import MovieRecommender
import logging

app = Flask(__name__, static_url_path='/static', static_folder='static')
recommender = MovieRecommender()

logging.basicConfig(level=logging.DEBUG)

# Function to get user's location
def get_user_location(location=None):
    if location:
        return location
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        # Use a different IP geolocation service if needed
        response = requests.get(f'https://ipapi.co/{ip}/json/')
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('country', '')  
            return country_code
        else:
            return None
    except Exception as e:
        logging.error("Error getting user location: %s", e)
        return None

# Home route to render index.html with automatic recommendations
@app.route('/')
def index():
    location = get_user_location()
    automatic_recommendations = recommender.get_auto_recommendations(location)
    return render_template('index.html', automatic_recommendations=automatic_recommendations)

# Route to get recommendations for a specific movie title
@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    try:
        movie_title = request.form.get('movieTitle')
        location = get_user_location()
        recommendations = recommender.get_recommendations_with_trailer(movie_title, location)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logging.exception("An error occurred: %s", e)
        return jsonify({"error": "Failed to fetch recommendations."}), 500


# Route to provide autocomplete suggestions for movie titles
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    term = request.args.get('term')
    if term:
        movie_titles = recommender.data['movie_title'].tolist()
        suggestions = [title for title in movie_titles if term.lower() in title.lower()]
    else:
        suggestions = []
    return jsonify({"titles": suggestions})

# Route to fetch automatic recommendations based on location
@app.route('/auto_recommendations', methods=['GET'])
def get_auto_recommendations():
    try:
        location = request.args.get('location')
        num_recommendations = int(request.args.get('num_recommendations', 12))
        recommendations = recommender.get_auto_recommendations(location, num_recommendations)
        return jsonify({"automatic_recommendations": recommendations})
    except Exception as e:
        logging.exception("An error occurred: %s", e)
        return jsonify({"error": "Failed to fetch automatic recommendations."}), 500

# Route to fetch filtered recommendations based on genre, country, or year
@app.route('/filtered_recommendations', methods=['GET'])
def get_filtered_recommendations():
    try:
        filter_type = request.args.get('filterType')
        filter_value = request.args.get('filterValue')
        recommendations = recommender.get_filtered_recommendations(filter_type, filter_value)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logging.exception("An error occurred: %s", e)
        return jsonify({"error": "Failed to fetch filtered recommendations."}), 500


# Route to fetch filtered recommendations by year
@app.route('/filtered_recommendations_by_year', methods=['GET'])
def get_filtered_recommendations_by_year():
    try:
        year = request.args.get('year')
        recommendations = recommender.get_filtered_recommendations_by_year(year)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logging.exception("An error occurred: %s", e)
        return jsonify({"error": "Failed to fetch filtered recommendations by year."}), 500

# Route to fetch trailer
@app.route('/fetch_trailer', methods=['POST'])
def fetch_trailer():
    try:
        if request.method == 'POST':
            movie_title = request.form.get('movie_title')
            movie_details = recommender.fetch_trailer(movie_title)
            if movie_details:
                return jsonify({"movie_details": movie_details})
            else:
                return jsonify({"error": "Movie details not found."}), 404
        else:
            return jsonify({"error": "Unsupported HTTP method"}), 405
    except Exception as e:
        logging.exception("An error occurred: %s", e)
        return jsonify({"error": "Failed to fetch movie trailer."}), 500


if __name__ == '__main__':
    recommender.load_data('movie_metadata.csv')
    recommender.preprocess_data()
    recommender.train_model()
    recommender.save_model('content_based_vectorizer.pkl')
    app.run(debug=True)

