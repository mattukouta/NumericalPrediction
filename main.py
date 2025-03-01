import csv
import datetime
import operator
import re
import time
import traceback

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser
from vo.CurrentDate import CurrentDate
from vo.Constrains import Constrains
from vo.WinningNumberInfo import WinningNumberInfo
from vo.Exceptions import NotFoundTargetUrl
from vo.Exceptions import NotFoundPastTable
from vo.TargetTableUrl import TargetTableUrl


def getCurrentTime() -> CurrentDate:
    now = datetime.datetime.now()

    return CurrentDate(now.year, now.month)


def fetchTargetUrl(browser: Browser, url: str) -> BeautifulSoup:
    try:
        print(f"{url}のリクエスト")
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state()
        time.sleep(3)
        html = page.content()

        page.close()

        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(e)


def getTargetTable(currentUrl: str, target: BeautifulSoup) -> TargetTableUrl:
    detailUrls = [currentUrl]
    simpleUrls = []

    body = target.find_all("tbody", class_="section__table-body")

    if len(body) != 2:
        raise NotFoundPastTable

    detailBody = body[0]
    simpleBody = body[1]

    for tag in detailBody.find_all("a", string="ロト6"):
        detailUrls.append("https://www.mizuhobank.co.jp" + tag.get("href"))

    rows = simpleBody.find_all("tr", class_="section__table-row js-backnumber-temp-b")
    for row in rows:
        simpleUrls.append(
            "https://www.mizuhobank.co.jp" + row.find_all("td", class_="section__table-data")[1].find("a").get("href"))

    return TargetTableUrl(detailUrls, simpleUrls)


def getDetailTable(browser: Browser, urls: list[str]):
    for url in urls:
        rows = (
            fetchTargetUrl(browser, url)
            .find("div", class_="pc-only section__table-wrap")
            .find_all("tbody", class_="section__table-body")
        )

        for row in rows:
            try:
                idStr = row.find("th",
                                 class_="section__table-head section__table-cell--center js-lottery-issue-pc").text
                id = int(re.findall(r"\d+", str(idStr))[0])

                dateStr = row.find("p", class_="section__text js-lottery-date-pc").text
                lotteryDateTime = datetime.datetime.strptime(dateStr, "%Y年%m月%d日")

                numberStr = row.find_all("b", class_="section__text--bold js-lottery-number-pc")

                winningNumber = [int(number.text) for number in numberStr]

                bonusStr = row.find(
                    "b",
                    class_="section__text--bold section__text--important js-lottery-bonus-pc"
                ).text
                bonusNumber = int(re.findall(r"\d+", str(bonusStr))[0])

                yield WinningNumberInfo(
                    id=id,
                    year=lotteryDateTime.year,
                    month=lotteryDateTime.month,
                    day=lotteryDateTime.day,
                    winningNumber=winningNumber,
                    bonusNumber=bonusNumber
                )
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                number = tb[-1][1]
                print(f"{e}: {number}")
                print(row)


def getSimpleTable(browser: Browser, urls: list[str]):
    for url in urls:
        rows = (
            fetchTargetUrl(browser, url)
            .find("table", class_="section__table pc-only")
            .find_all("tr", class_="section__table-row")
        )

        for row in rows:
            try:
                idSection = row.find("th", class_="section__table-head")
                idParagraph = idSection.find("p")
                id: int = 0
                idStr: list[str] = []
                if idParagraph is not None:
                    idStr = re.findall(r"\d+", str(idParagraph.text))
                else:
                    idStr = re.findall(r"\d+", str(idSection.text))
                if idStr:
                    id = int(idStr[0])

                lotteryDateTime: datetime = None
                dateSection = row.find("td", class_="section__table-data section__table-cell--right")
                if dateSection is not None:
                    dateParagraph = dateSection.find("p")
                    lotteryDateTime = datetime.datetime.strptime(dateParagraph.text, "%Y年%m月%d日")
                else:
                    lotteryDateTime = datetime.datetime.strptime(
                        row.find("td", class_="section__table-data section__table-cell--right js-lottery-date").text,
                        "%Y年%m月%d日"
                    )

                winningNumber: list[int] = []
                numbersSection = row.select('td[class="section__table-data"]')
                if numbersSection and numbersSection[0].find("p") is not None:
                    winningNumber = [int(number.find("p").text) for number in numbersSection]
                else:
                    winningNumber = [int(number.text) for number in numbersSection]

                bonusNumber = 0
                bonusNumberParagraph = row.find("p", class_="section__text section__text--important")
                if bonusNumberParagraph is not None:
                    bonusNumber = int(bonusNumberParagraph.text)
                else:
                    bonusNumber = int(
                        row.find("td", class_="section__table-data aln-center section__text--important").text)

                yield WinningNumberInfo(
                    id=int(id),
                    year=lotteryDateTime.year,
                    month=lotteryDateTime.month,
                    day=lotteryDateTime.day,
                    winningNumber=winningNumber,
                    bonusNumber=bonusNumber
                )

            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                number = tb[-1][1]
                print(f"{e}: {number}")
                print(row)


def outputWinningNumberResult(tables: list[WinningNumberInfo]):
    with open("outputs/WinningNumber.csv", mode="w") as f:
        writer = csv.writer(f)

        for table in tables:
            writer.writerow(
                [
                    table.id,
                    table.year,
                    table.month,
                    table.day,
                    table.winningNumber,
                    table.bonusNumber
                ]
            )


# if __name__ == '__main__':
#     detailTables = [
#         WinningNumberInfo(
#             id=0,
#             year=2025,
#             month=2,
#             day=1,
#             winningNumber=[1,2],
#             bonusNumber=3,
#         )
#     ]
#     simpleTables = [
#         WinningNumberInfo(
#             id=1,
#             year=2025,
#             month=2,
#             day=1,
#             winningNumber=[1,2],
#             bonusNumber=3,
#         )
#     ]
#     tables = sorted(simpleTables + detailTables, key=lambda x: x.id)
#
#     print(tables)

if __name__ == '__main__':
    # ブラウザの起動
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(channel="chrome", headless=False)

    # 西暦、月を取得
    date = getCurrentTime()

    # 最新情報を取得
    # currentUrl = f"{Constrains.LOTO6_TOP_URL}?year={date.year}&month={date.month}"
    currentUrl = f"{Constrains.LOTO6_TOP_URL}?year=2025&month=2"

    # 過去情報を取得
    table = getTargetTable(currentUrl, fetchTargetUrl(browser, Constrains.LOTO6_BACK_NUMBER_URL))

    print("detailTableUrls")
    print(len(table.detailTableUrls))
    print("simpleTableUrls")
    print(len(table.simpleTableUrls))

    # 直近１年分の情報を取得
    detailTables = list(getDetailTable(browser, table.detailTableUrls))
    print(len(detailTables))

    # １年以上の情報を取得
    simpleTables = list(getSimpleTable(browser, table.simpleTableUrls))
    print(len(simpleTables))
    tables = sorted(detailTables + simpleTables, key=lambda x: x.id)

    # CSVファイルに出力
    outputWinningNumberResult(tables)

    # ブラウザの終了
    playwright.stop()
