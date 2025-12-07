"""
python manage.py shell
from youtube_integration.benchmark_lang_filters import test_all_filters
test_all_filters("ID_FILMU")

Benchmark of language filtering methods on YouTube comments.
"""

from youtube_integration.services import get_yt_comments
from youtube_integration.language_filtering import (
    filter_lang_langdetect,
    filter_lang_langid,
    filter_lang_cld2,
)


def test_all_filters(video_id):
    comments = get_yt_comments(video_id)
    print(f"Pobrano {len(comments)} komentarzy.\n")

    results = []

    tests = [
        filter_lang_langdetect,
        filter_lang_langid,
        filter_lang_cld2,
    ]

    for i, f in enumerate(tests, 1):
        print(f"Test {i}/{len(tests)} — {f.__name__}")
        en, non_en, stats = f(comments)
        print(stats)
        results.append(stats)

    print("\n")

    for r in results:
        print(
            f"{r['method']:10} | EN: {r['english']:4} | "
            f"NON-EN: {r['non_english']:4} | time: {r['time']}s"
        )

    return results
