import logging
import os
import time
from urllib.error import HTTPError

from dotenv import load_dotenv
import googleapiclient.discovery
from deep_translator import GoogleTranslator
import pycld2 as cld2

load_dotenv()

CONFIDENCE_THRESHOLD = 0.90
PRO_COMMENT_LIMIT = 10000


def check_video_limit(video_id):
    """
    check if video comment count is within free tier limit
    Returns (is_within_limit: bool, error_message: str|None)
    """
    try:
        api_service_name = "youtube"
        api_version = "v3"
        api_key = os.getenv("API_KEY")

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=api_key
        )

        response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        if not response.get("items"):
            return False, "Nie znaleziono wideo o podanym ID lub jest prywatne."

        stats = response["items"][0]["statistics"]
        comment_count = int(stats.get("commentCount", 0))

        # If video has more comments than free limit, return False with message
        if comment_count > PRO_COMMENT_LIMIT:
            msg = (f"The film has {comment_count} comments. "
                   f"The free version supports up to {PRO_COMMENT_LIMIT}. "
                   "Purchase the PRO package to analyze such large channels.")
            return False, msg

        return True, None

    except Exception as e:
        return False, f"Błąd weryfikacji wideo: {str(e)}"


def get_yt_comments(video_id, max_results_total=PRO_COMMENT_LIMIT):
    """
    Download comments from a YouTube video, detect their language,
    translate non-English comments to English, and return a list of comments in English.
    1. video_id: str - YouTube video ID
    2. max_results_total: int - maximum number of comments to retrieve
    Returns: List of comments in English
    """
    comments_list = []

    try:
        # TIMER ON TOTAL PROCESS
        total_start = time.time()

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

        # TIMERS
        filter_time_total = 0.0
        translation_time_total = 0.0

        # Download comments in pages of max 100 until reaching max_results_total
        while request and len(comments_list) < max_results_total:
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                top_comment = snippet.get("topLevelComment", {})
                comment_snippet = top_comment.get("snippet", {})
                text = comment_snippet.get("textOriginal")

                if not text:
                    continue

                # TIMER FIND LANGUAGE
                f_start = time.time()
                try:
                    reliable, textBytesFound, details = cld2.detect(text)
                    lang_code = details[0][1]
                    prob = details[0][2] / 100.0

                    if lang_code == "en" and reliable and prob >= CONFIDENCE_THRESHOLD:
                        lang = "en"
                    else:
                        lang = lang_code or "unknown"
                except Exception:
                    lang = "unknown"
                filter_time_total += (time.time() - f_start)

                # TIMER TRANSLATING
                if lang != "en":
                    t_start = time.time()
                    try:
                        translated_text = GoogleTranslator(source='auto', target='en').translate(text)
                        if translated_text:
                            text = translated_text
                    except Exception as e:
                        logging.warning(f"Translation failed: {text[:50]}... Error: {e}")
                    translation_time_total += (time.time() - t_start)

                if text:
                    comments_list.append(text)

                if len(comments_list) >= max_results_total:
                    break

            if len(comments_list) >= max_results_total:
                break

            request = youtube.commentThreads().list_next(
                previous_request=request,
                previous_response=response
            )

        total_end = time.time()
        total_time = total_end - total_start


        print("\n================ TIMER REPORT ================\n")
        print(f"Czas wykrywania języka: {filter_time_total:.2f} s")
        print(f"Czas tłumaczenia komentarzy: {translation_time_total:.2f} s")
        print(f"Łączny czas:{total_time:.2f} s")
        print("\n==============================================\n")



        return comments_list

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

