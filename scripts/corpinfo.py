#!/usr/bin/env python

# 標準ライブラリ
from pathlib import Path
from re import search, sub
from sys import exit, argv
from xml.etree import ElementTree as ET
import csv

# サードパーティライブラリ
from requests import get
from requests.exceptions import Timeout, RequestException


# ローカルなライブラリ
from constants import ENC_API_KEY, NTA_API_URL
from crypt_string import decrypt_strings


def validate_number(corp_number: str) -> bool:
    """
    指定された法人番号の妥当性をチェックデジットを用いて検証する。

    Parameters
    ----------
    corp_number : str
        13桁の法人番号

    Returns
    -------
    bool
        指定された法人番号が正しい場合はtrue、誤っている場合はfalseを返す

    """
    tmp_corp_num_lst = list(corp_number)
    corp_num_lst = list(map(int, tmp_corp_num_lst))

    # 最上位1桁目のチェックデジットを取得
    check_degit = corp_num_lst[0]
    del corp_num_lst[0]

    # STEP1: 最下位から偶数桁の和 × 2 + 最下位から奇数桁の和 を求める。
    degit_step1 = sum(corp_num_lst[-2::-2]) * 2 + sum(corp_num_lst[-1::-2])

    # STEP2: STEP1で求めた数を9で割ったあまりを求める。
    degit_step2 = degit_step1 % 9

    # STEP3: 9から STEP2 で求めた数を引いた数
    degit = 9 - degit_step2

    if check_degit == degit:
        return True
    else:
        return False


def get_corp_info(api_key: str, corp_number: str) -> str:
    """
    [summary]

    Parameters
    ----------
    api_key : str
        [description]
    corp_number : str
        [description]

    Returns
    -------
    str
        [description]
    """

    # クエリーパラメータの作成
    # ------------------------------------------------------------------------------
    params = {
        'id': api_key,
        'number': corp_number,
        'type': '12',
        'history': '0',
    }

    # 法人情報の取得
    # ------------------------------------------------------------------------------
    try:
        response = get(NTA_API_URL, params=params, timeout=3.0)
        response.raise_for_status()

    except Timeout as err:
        # TODO: logging で出力するように変更する。要学習。
        print(err)
        print("タイムアウトしました。")
        exit(11)

    except RequestException as err:
        # TODO: logging で出力するように変更する。要学習。
        print(err)
        exit(12)

    # XMLの解析と出力
    # ------------------------------------------------------------------------------
    root = ET.fromstring(response.text)

    num = 4
    corp_info_list = [["法人番号", "最終更新年月日", "商号又は名称",
                       "本店又は主たる事務所の所在地", "郵便番号", "商号又は名称（フリガナ）"]]

    if num >= len(root):

        # TODO: logging で出力するように変更する。要学習。
        print("指定された法人番号(" + corp_number + ")のデータが存在しません。")

    else:

        while num < len(root):

            corp_info_list.append([root[num][1].text,
                                   root[num][4].text,
                                   root[num][6].text,
                                   root[num][9].text +
                                   root[num][10].text +
                                   root[num][11].text,
                                   sub(r'([0-9]{3})([0-9]{4})',
                                       r'\1-\2', root[num][15].text),
                                   root[num][28].text])
            num += 1

    for corp_info in corp_info_list[1:]:
        print("{0:　<14} : {1}".format(corp_info_list[0][0], corp_info[0]))
        print("{0:　<14} : {1}".format(corp_info_list[0][2], corp_info[2]))
        print("{0:　<14} : {1}".format(corp_info_list[0][5], corp_info[5]))
        print("{0:　<14} : {1}".format(corp_info_list[0][4], corp_info[4]))
        print("{0:　<14} : {1}".format(corp_info_list[0][3], corp_info[3]))
        print("{0:　<14} : {1}".format(corp_info_list[0][1], corp_info[1]))
        print("")

    try:

        with open('../log/corp_info.csv', 'w', encoding='utf-8') as csv_out:
            writer = csv.writer(csv_out, lineterminator='\n')
            writer.writerows(corp_info_list)

    except FileNotFoundError as err:
        # TODO: logging で出力するように変更する。要学習。
        print(err)

    except PermissionError as err:
        # TODO: logging で出力するように変更する。要学習。
        print(err)

    except csv.Error as err:
        # TODO: logging で出力するように変更する。要学習。
        print(err)


if __name__ == "__main__":

    # Web-API利用用アプリケーションIDの復号
    if Path(argv[-1]).is_file():

        api_key = decrypt_strings(ENC_API_KEY, argv[-1])
        del argv[-1]

    else:

        api_key = decrypt_strings(ENC_API_KEY)

    # 入力された法人番号の確認
    if not argv[1:]:
        # TODO: logging で出力するように変更する。要学習。
        print("法人番号が指定されてません。")
        exit(1)

    else:

        for corp_number in argv[1:]:

            if not search("^[1-9][0-9]{12}$", corp_number):
                # TODO: logging で出力するように変更する。要学習。
                print("法人番号は13桁で指定して下さい。")
                exit(2)

            elif not validate_number(corp_number):
                # TODO: logging で出力するように変更する。要学習。
                print("指定された法人番号(" + corp_number + ")は正しくありません。")
                exit(3)

    # 法人番号から情報を取得する。
    corp_numbers = ",".join(map(str, argv[1:]))
    get_corp_info(api_key, corp_numbers)

    exit(0)
