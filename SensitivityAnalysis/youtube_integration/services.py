import logging
import os
from urllib.error import HTTPError

from dotenv import load_dotenv
import googleapiclient.discovery
from deep_translator import GoogleTranslator
import pycld2 as cld2

load_dotenv()

CONFIDENCE_THRESHOLD = 0.90

def get_yt_comments(video_id, max_results_total=500):
    comments_list = []

    try:
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
        )

        while request and len(comments_list) < max_results_total:
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                top_comment = snippet.get("topLevelComment", {})
                comment_snippet = top_comment.get("snippet", {})
                text = comment_snippet.get("textOriginal")

                if not text:  # Skip empty comments
                    continue

                # Detect language using CLD2 and translate to English if needed
                try:
                    reliable, textBytesFound, details = cld2.detect(text)
                    # details[0] = (language_name, language_code, percent, score)
                    lang_code = details[0][1]
                    percent = details[0][2]
                    prob = percent / 100.0

                    if lang_code == "en" and reliable and prob >= CONFIDENCE_THRESHOLD:
                        lang = "en"
                    else:
                        lang = lang_code or "unknown"

                except Exception:
                    lang = "unknown"

                if lang != "en":
                    try:
                        translated_text = GoogleTranslator(source='auto', target='en').translate(text)
                        if translated_text:
                            text = translated_text
                    except Exception as e:
                        logging.warning(f"Translation failed: {text[:50]}... Error: {e}")

                # Add only non-empty text
                if text:
                    comments_list.append(text)

            # Next comments page
            request = youtube.commentThreads().list_next(
                previous_request=request,
                previous_response=response
            )

        logging.info(f"Fetched and translated {len(comments_list)} comments for video_id: {video_id}")

        # Print comments in the console
        print("\n--- TRANSLATED COMMENTS ---")
        for c in comments_list:
            print(c)
        print("\n--- END ---\n")

        return comments_list

    except HTTPError as e:
        logging.error(f"YouTube API error (HTTPError): {e.reason}")
        raise

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


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

