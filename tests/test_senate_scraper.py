import os
from src.senate.helpers import load_dotenv_with_env


def test_dotenv():
    load_dotenv_with_env("prod")
    print(os.environ.get('SENATE_SEARCH_URL', '*************poop'))
    assert os.getenv(
        "SENATE_SEARCH_URL") == 'https://efdsearch.senate.gov/search/home'


# def test_texto():
#     load_dotenv_with_env("prod")
#     t = Texto()
#     messages = t.send_text("look at me")
#     print(messages[0].sid, messages[0].status)
#     assert messages[0].status == "Undelivered"
