import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser
from vo.CurrentDate import CurrentDate
from vo.Constrains import Constrains
from vo.Exceptions import NotFoundTargetUrl
from vo.Exceptions import NotFoundPastTable
from vo.TargetTableUrl import TargetTableUrl


def getCurrentTime() -> CurrentDate:
    now = datetime.datetime.now()

    return CurrentDate(now.year, now.month)


def fetchTargetUrl(browser: Browser, url: str) -> BeautifulSoup:
    print(f"{url}のリクエスト")
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state()
    html = page.content()

    return BeautifulSoup(html, "html.parser")


def getTargetTable(currentUrl: str, target: BeautifulSoup) -> TargetTableUrl:
    detailUrls = [currentUrl]
    simpleUrls = []

    body = target.find_all("tbody", class_="section__table-body")

    if len(body) != 2:
        raise NotFoundPastTable

    detailBody = body[0]
    simpleBody = body[1]

    for tag in detailBody.find_all("a", string="ロト6"):
        detailUrls.append(tag.get("href"))

    rows = simpleBody.find_all("tr", class_="section__table-row js-backnumber-temp-b")
    for row in rows:
        simpleUrls.append(row.find_all("td", class_="section__table-data")[1].find("a").get("href"))

    return TargetTableUrl(detailUrls, simpleUrls)


if __name__ == '__main__':
    # ブラウザの起動
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(channel="chrome", headless=False)

    # 西暦、月を取得
    date = getCurrentTime()

    # 最新情報を取得
    currentUrl = f"{Constrains.LOTO6_TOP_URL}?year={date.year}&month={date.month}"

    # 過去情報を取得
    table = getTargetTable(currentUrl, fetchTargetUrl(browser, Constrains.LOTO6_BACK_NUMBER_URL))

    print(len(table.detailTableUrls))
    print(len(table.simpleTableUrls))

    # ブラウザの終了
    playwright.stop()

