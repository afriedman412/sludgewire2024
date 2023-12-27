from .senate_no_download import SenateDownloader
from .helpers import load_dotenv_with_env

load_dotenv_with_env("prod")

if __name__ == "__main__":
    try:
        snd = SenateDownloader()
        snd.search()
    except Exception as e:
        try:
            print("closing driver...")
            snd.driver.quit()
        except AttributeError:
            pass
        print(e)
    # snd.send()
