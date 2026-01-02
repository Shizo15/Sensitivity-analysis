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
    try:
        api_key = os.getenv("API_KEY")
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        response = youtube.videos().list(part='statistics', id=video_id).execute()
        if not response.get("items"):
            return False, "Video with the given ID was not found or is private."
        stats = response["items"][0]["statistics"]
        comment_count = int(stats.get("commentCount", 0))
        if comment_count > PRO_COMMENT_LIMIT:
            msg = (f"The film has {comment_count} comments. Support up to {PRO_COMMENT_LIMIT}.")
            return False, msg
        return True, None
    except Exception as e:
        return False, f"Verification error: {str(e)}"


def get_yt_comments(video_id, max_results_total=PRO_COMMENT_LIMIT):
    print(f"\n--- STARTING YOUTUBE DOWNLOAD ---")
    start_time = time.time()
    comments_list = []
    to_translate_index = []
    to_translate_text = []

    try:
        api_key = os.getenv("API_KEY")
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        request = youtube.commentThreads().list(part='snippet', videoId=video_id, maxResults=100)

        while request and len(comments_list) < max_results_total:
            response = request.execute()
            for item in response.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
                if not text: continue
                try:
                    reliable, _, details = cld2.detect(text)
                    lang = details[0][1] if (reliable and details[0][2] / 100.0 >= CONFIDENCE_THRESHOLD) else "unknown"
                except:
                    lang = "unknown"

                curr_idx = len(comments_list)
                comments_list.append(text)
                if lang != "en":
                    to_translate_index.append(curr_idx)
                    to_translate_text.append(text)
                if len(comments_list) >= max_results_total: break

            print(f"Downloaded: {len(comments_list)} comments...")
            request = youtube.commentThreads().list_next(request, response)

        print(f"Download took: {time.time() - start_time:.2f} s")

        if to_translate_text:
            print(f"Starting translation of {len(to_translate_text)} comments...")
            t_start = time.time()
            try:
                translator = GoogleTranslator(source="auto", target="en")
                translated_texts = translator.translate_batch(to_translate_text)
                for i, translated_text in enumerate(translated_texts):
                    if translated_text:
                        comments_list[to_translate_index[i]] = translated_text
            except Exception as e:
                logging.warning(f"Translation error: {e}")
            print(f"Translation took: {time.time() - t_start:.2f} s")

        print(f"--- YOUTUBE SERVICE FINISHED: {time.time() - start_time:.2f} s ---\n")
        return comments_list
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def get_yt_video_meta(video_id):
    try:
        api_key = os.getenv("API_KEY")
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        item = resp["items"][0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        thumbs = snippet.get("thumbnails", {})
        best = (thumbs.get("maxres") or thumbs.get("high") or {}).get("url")
        return snippet.get("title"), best, snippet.get("channelTitle"), snippet.get("publishedAt"), stats.get(
            "viewCount"), stats.get("likeCount")
    except Exception:
        return None, None, None, None, None, None