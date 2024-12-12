import json
import boto3
import requests

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PostsTable')

def search_posts(query):
    try:
        # Build the request URL
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
        
        # Send the search request using requests
        response = requests.get(
            url,
            params={
                "q": query,  
                "sort": "latest",  
                "limit": 2,  
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Error fetching posts: {response.text}")

        # Parse the response as JSON
        posts_data = response.json()
        return posts_data
    
    except Exception as e:
        raise Exception(f"Error searching posts: {str(e)}")

def lambda_handler(event, context):
    try:
        # Define the search query
        query = "outage" 

        # Fetch posts based on the query
        post_data = search_posts(query)

        posts = post_data.get("posts", [])
        if not posts:
            raise Exception("No posts found in the API response.")

        with table.batch_writer() as batch:
            for post in posts:
                post_id = f"{post['record']['createdAt']}_{hash(post['uri'])}"
                uri = post['uri']
                content = post['record']['text']
                author = post['author']['displayName']
                timestamp = post['record']['createdAt']
                keywords = extract_keywords(content)  # Function to extract keywords

                # Store the post and its keywords
                batch.put_item({
                    'post_id': post_id,
                    'uri': uri,
                    'content': content,
                    'author': author,
                    'timestamp': timestamp,
                    'keywords': keywords,  # Save the keywords
                })

        return {"statusCode": 200, "body": "Posts saved successfully"}
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

stopwords = {
    "the", "is", "in", "on", "at", "and", "to", "of", "a", "an", "for", "with", "as", "that", "there", "it", "this", "be", "by", "are", "was"
    
}

def extract_keywords(content):
    # Split content into words
    words = content.split()

    # Filter out stopwords and keep meaningful words
    meaningful_words = [word for word in words if word.lower() not in stopwords]

    # Convert to a set to remove duplicates
    keywords = set(meaningful_words)
    keywords = " ".join(keywords)

    return keywords
    