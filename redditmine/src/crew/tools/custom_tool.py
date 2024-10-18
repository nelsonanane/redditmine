from crewai_tools import BaseTool
from pydantic import BaseModel, Field
import praw
import prawcore
from flask import jsonify
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv("YOUR_CLIENT_ID"),
    client_secret=os.getenv("YOUR_CLIENT_SECRET"),
    user_agent=os.getenv("YOUR_USER_AGENT")
)


class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = "Clear description for what this tool is useful for, you agent will need this information to use it."

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
    
class SubredditDetailTool(BaseTool):
    name: str = "Subreddit Detail Tool"
    description: str = "Fetches detailed information about a specified subreddit, including top posts and comments."
    
    reddit: object = Field(description="Reddit API instance")

    def __init__(self, reddit):
        super().__init__(reddit=reddit) 

    def _run(self, subreddit_name: str) -> str:
        if not subreddit_name:
            return jsonify({"error": "Subreddit name is required"}), 400

        try:
            subreddit = reddit.subreddit(subreddit_name)
            subreddit_data = {
                "name": subreddit.display_name_prefixed,
                "title": subreddit.title,
                "description": subreddit.public_description,
                "members": subreddit.subscribers,
                "online": subreddit.active_user_count,
                "created": subreddit.created_utc,
            }

            # Fetch top posts
            top_posts = []
            for post in subreddit.top(limit=50, time_filter="month"):
                post_data = {
                    "title": post.title,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "author": post.author.name if post.author else "[deleted]",
                    "created_utc": post.created_utc,
                    "selftext": post.selftext,
                    "upvote_ratio": post.upvote_ratio,
                    "comments": []
                }

                # Fetch comments for each post
                post.comments.replace_more(limit=0)  # Remove MoreComments objects
                for comment in post.comments.list()[:10]:  # Get top 10 comments
                    comment_data = {
                        "body": comment.body,
                        "score": comment.score,
                        "author": comment.author.name if comment.author else "[deleted]",
                        "created_utc": comment.created_utc
                    }
                    post_data["comments"].append(comment_data)

                top_posts.append(post_data)

            subreddit_data["top_posts"] = top_posts
            return jsonify(subreddit_data)

        except praw.exceptions.InvalidSubreddit:
            return jsonify({"error": f"Invalid subreddit: {subreddit_name}"}), 400
        except praw.exceptions.Forbidden:
            return jsonify({"error": f"Access to subreddit {subreddit_name} is forbidden"}), 403
        except praw.exceptions.NotFound:
            return jsonify({"error": f"Subreddit {subreddit_name} not found"}), 404
        except (praw.exceptions.PRAWException, prawcore.PrawcoreException) as e:
            print(f"Error fetching subreddit data: {str(e)}")
            return jsonify({"error": f"Failed to fetch subreddit data: {str(e)}"}), 500
