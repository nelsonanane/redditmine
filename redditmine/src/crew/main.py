#!/usr/bin/env python
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
import praw
from praw.exceptions import PRAWException
from prawcore.exceptions import PrawcoreException
from dotenv import load_dotenv
import requests
import os
import time
import prawcore
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from redditmine.src.crew.crew import RedditResearchCrew

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize the Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv("YOUR_CLIENT_ID"),
    client_secret=os.getenv("YOUR_CLIENT_SECRET"),
    user_agent=os.getenv("YOUR_USER_AGENT")
)

@app.route('/subreddits')
def get_subreddits():
    print("Received request for subreddits")
    try:
        subreddits = []
        for subreddit in reddit.subreddits.popular(limit=50):
            subreddits.append({
                'name': subreddit.display_name,
                'title': subreddit.title,
                'subscribers': subreddit.subscribers,
                'description': subreddit.public_description,
                'created': subreddit.created_utc,
                'online': subreddit.accounts_active,
                'posts_per_day': 0,  # You'll need to calculate this
                'upvote_ratio': 0.95,  # This is a placeholder value
            })
        print(f"Returning {len(subreddits)} subreddits")
        response = make_response(jsonify(subreddits))
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3001'
        return response
    except (PRAWException, PrawcoreException) as e:
        print(f"Error fetching subreddits: {str(e)}")
        return jsonify({"error": "Failed to fetch subreddits"}), 500
    
@app.get("/search_subreddits")
def search_subreddits():
    q = request.args.get('q')
    if q is None:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    
    try:
        subreddits = []
        for subreddit in reddit.subreddits.search(q, limit=50):
            subreddits.append({
                "name": subreddit.display_name_prefixed,
                "title": subreddit.title,
                "description": subreddit.public_description,
                "members": subreddit.subscribers,
                "online": subreddit.active_user_count,
                "created": subreddit.created_utc,
                "posts_per_day": 0,  # This data is not directly available through PRAW
                "upvote_ratio": 0,   # This data is not directly available through PRAW
            })
        
        return jsonify(subreddits)
    except praw.exceptions.PRAWException as e:
        print(f"Error fetching subreddits: {str(e)}")
        return jsonify({"error": "Failed to fetch subreddits"}), 500
    
@app.route('/subreddit_detail')
def subreddit_detail():
    subreddit_name = request.args.get('name')
    if not subreddit_name:
        return jsonify({"error": "Subreddit name is required"}), 400 

    # # Create RedditResearchCrew instance
    # crew_instance = RedditResearchCrew()
    # crew_instance.reddit = reddit  # Pass the reddit instance to the crew

    # # Create and run the crew
    # crew = crew_instance.crew()
    # result = crew.kickoff(inputs=subreddit_name)
    crew = RedditResearchCrew()
    
    # Create a dictionary with the subreddit name
    inputs = {'subreddit': subreddit_name}
    
    # Pass the dictionary to kickoff
    result = crew.run(inputs=inputs)

    # Process and return the result
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)