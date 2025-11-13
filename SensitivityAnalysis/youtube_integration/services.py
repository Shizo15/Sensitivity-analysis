import logging
import os
from urllib.error import HTTPError

from dotenv import load_dotenv
import googleapiclient.discovery

load_dotenv()

def get_yt_comments(video_id, max_results_total=500):

    try:
        comments_list = []

        api_service_name = "youtube"
        api_version = "v3"
        api_key = os.getenv("API_KEY")

        youtube = googleapiclient.discovery.build(
            api_service_name,
            api_version,
            developerKey=api_key
        )

        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            #order = "time"
        )

        #Limited to 500 comments to prevent API limits from being exceeded
        while request and len(comments_list) < max_results_total:

            response = request.execute()

            for item in response.get("items", []):

                snippet = item.get("snippet", {})
                top_level_comment = snippet.get("topLevelComment", {})
                comment_snippet = top_level_comment.get("snippet", {})

                text = comment_snippet.get("textOriginal")

                if text:
                    comments_list.append(text)

            #Next comments page (if exists)
            request = youtube.commentThreads().list_next(
                previous_request=request,
                previous_response=response
            )

        logging.info(f"Pomyślnie pobrano {len(comments_list)} komentarzy dla video_id: {video_id}")

        #ile = len(comments_list)
        #return ile, comments_list
        return comments_list

    except HTTPError as e:
        error_message = f"Błąd API YouTube (HTTPError): {e.reason})"
        logging.error(error_message)
        raise Exception(error_message)

    except Exception as e:
        error_message = f"Wystąpił nieoczekiwany błąd podczas pobierania komentarzy: {e}"
        logging.error(error_message)
        raise Exception(error_message)


#print(get_yt_comments("b0MnmShVLv8"))

def get_yt_video_meta(video_id):

    try:
        api_service_name = "youtube"
        api_version = "v3"
        api_key = os.getenv("API_KEY")

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=api_key
        )

        resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return None, None, None, None, None, None

        item = items[0]
        snippet = item.get("snippet", {}) or {}
        stats = item.get("statistics", {}) or {}

        title = snippet.get("title")
        channel_title = snippet.get("channelTitle")
        published_at = snippet.get("publishedAt")

        thumbs = snippet.get("thumbnails", {}) or {}
        best = (thumbs.get("maxres") or thumbs.get("standard")
                or thumbs.get("high") or thumbs.get("medium")
                or thumbs.get("default") or {})
        thumb_url = best.get("url")

        view_count = stats.get("viewCount")
        like_count = stats.get("likeCount")

        return title, thumb_url, channel_title, published_at, view_count, like_count

    except Exception:
        return None, None, None, None, None, None



