# RedditMine Project README

This project consists of a Next.js frontend and a Python Flask backend for analyzing Reddit subreddits.

## Prerequisites

- Node.js (version 14 or higher)
- Python (version 3.10 or higher)
- Poetry (for Python dependency management)
- Reddit API credentials

## Backend Setup

1. Navigate to the backend directory:
   ```
   cd redditmine
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Set up your environment variables:
   Create a `.env` file in the redditmine directory and add your Reddit API credentials:
   ```
   YOUR_CLIENT_ID=your_client_id_here
   YOUR_CLIENT_SECRET=your_client_secret_here
   YOUR_USER_AGENT=your_user_agent_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Run the backend server:
   ```
   poetry run python src/crew/main.py
   ```

   The backend server will start running on `http://192.168.1.91:8000`.

## Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend/redditmine
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`.

## Usage

1. Open your browser and go to `http://localhost:3000`.
2. You'll see a list of popular subreddits.
3. Use the search bar to find specific subreddits.
4. Click on a subreddit to view its detailed analysis.

## Important Files

### Backend

`src/crew/main.py`:

```python
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

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
                'posts_per_day': 0,
                'upvote_ratio': 0.95,
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
                "posts_per_day": 0,
                "upvote_ratio": 0,
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

    crew = RedditResearchCrew()
    
    inputs = {'subreddit': subreddit_name}
    
    result = crew.run(inputs=inputs)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
```

This file contains the Flask server setup and API endpoints.

### Frontend

`app/page.tsx`:

```typescript
import { SubredditInfoComponent } from "@/components/subreddit-info"

export default function Page() {
  return <SubredditInfoComponent />
}
```

This is the main page component of the frontend.

`components/subreddit-info.tsx`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  ArrowUpIcon,
  MessageSquareIcon,
  CalendarIcon,
  SearchIcon,
  UsersIcon,
} from "lucide-react";
import axios from "axios";
import Link from "next/link";

interface Subreddit {
  name: string;
  title?: string;
  description?: string;
  members: number;
  online: number;
  created: string;
  posts_per_day: number;
  upvote_ratio: number;
}

export function SubredditInfoComponent() {
  const [searchTerm, setSearchTerm] = useState("");
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [searchResults, setSearchResults] = useState<Subreddit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchSubreddits();
  }, []);

  const fetchSubreddits = async () => {
    try {
      setLoading(true);
      const response = await axios.get("http://192.168.1.91:8000/subreddits");
      setSubreddits(response.data);
      setLoading(false);
    } catch (err) {
      setError("Failed to fetch subreddits");
      if (axios.isAxiosError(err)) {
        console.log("Error message: ", err.message);
        console.log("Response data: ", err.response?.data);
        console.log("Response status: ", err.response?.status);
      } else {
        console.log("Unexpected error: ", err);
      }
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (searchTerm.trim()) {
      try {
        setLoading(true);
        const response = await axios.get(
          `http://192.168.1.91:8000/search_subreddits?q=${encodeURIComponent(
            searchTerm
          )}`
        );
        setSearchResults(response.data);
        setLoading(false);
      } catch (err) {
        console.error("Error searching subreddits:", err);
        setError("Failed to search subreddits");
        setLoading(false);
      }
    } else {
      setSearchResults([]);
    }
  };
  const displayedSubreddits =
    searchResults.length > 0 ? searchResults : subreddits;

  console.log({ subreddits });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4 space-y-8">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">
            Popular Subreddits
          </h1>
          <p className="text-xl text-muted-foreground">
            Discover and explore Reddit&apos;s most engaging communities
          </p>
        </header>
        <div className="flex items-center space-x-2 max-w-lg mx-auto">
          <div className="relative flex-grow">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search subreddits..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2"
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch}>Search</Button>
        </div>
        {displayedSubreddits.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-xl text-muted-foreground">
              No subreddits found matching your search.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedSubreddits.map((subreddit) => (
              <Link
                href={`/subreddit/${encodeURIComponent(subreddit.name)}`}
                key={subreddit.name}
              >
                <Card className="overflow-hidden transition-shadow hover:shadow-lg cursor-pointer">
                  <CardHeader className="bg-primary text-primary-foreground">
                    <CardTitle className="flex justify-between items-center">
                      <span>{subreddit.name}</span>
                      <Badge variant="secondary" className="ml-2">
                        {subreddit?.online?.toLocaleString()} online
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4">
                    <p className="text-sm text-muted-foreground">
                      {subreddit?.description}
                    </p>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold flex items-center gap-2">
                          <UsersIcon className="w-4 h-4" />
                          Members
                        </span>
                        <span>{subreddit?.members?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-semibold flex items-center gap-2">
                          <CalendarIcon className="w-4 h-4" />
                          Created
                        </span>
                        <span>{subreddit?.created}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-semibold flex items-center gap-2">
                          <MessageSquareIcon className="w-4 h-4" />
                          Posts per day
                        </span>
                        <span>{subreddit?.posts_per_day}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="font-semibold flex items-center gap-2">
                          <ArrowUpIcon className="w-4 h-4" />
                          Upvote ratio
                        </span>
                        <span>
                          {(subreddit?.upvote_ratio * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

This component handles the display of subreddit information and search functionality.

`app/subreddit/[name]/page.tsx`:

```typescript
"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SubredditAnalysis {
  content: string;
}

export default function SubredditDetailPage() {
  const params = useParams();
  const name = params.name as string;
  const [analysis, setAnalysis] = useState<SubredditAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `http://192.168.1.91:8000/subreddit_detail?name=${encodeURIComponent(
            name
          )}`
        );
        setAnalysis(response.data);
      } catch (error) {
        console.error("Error fetching subreddit analysis:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [name]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <h1 className="text-3xl font-bold mb-6">Analysis of r/{name}</h1>
      <Card>
        <CardHeader>
          <CardTitle>{name} Subreddit Analysis Report</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px]">
            {analysis && <ReactMarkdown>{analysis}</ReactMarkdown>}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
```

This file handles the detailed view of a specific subreddit.

## Troubleshooting

- If you encounter CORS issues, make sure your backend is running on the correct
