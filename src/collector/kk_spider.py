"""
Created by fre123 at 2024-09-11.
Description: http://z.kkkob.com/app/index.html 抓取数据
    pipenv run python src/collector/kk_spider.py
Changelog: all notable changes to this file will be documented
"""

import concurrent.futures
import random

from src.collector import REQ_SESSION, data_config
from src.common.remote import send_get_request, send_post_request
from src.config import LOGGER, Config


def get_token(token_url: str, proxy_model: int = 0) -> str:
    """
    获取token
    """
    headers = {
        **data_config.SPIDER_CONFIG["REQUEST_HEADERS"],
        **{"Content-Type": "application/json"},
    }
    if proxy_model:
        proxy = {
            "http": data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_URL"],
            "https": data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_URL"],
        }
        headers.update(
            data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_HEADERS"]
        )
        LOGGER.info("KK Spider 使用代理获取 token")
    else:
        proxy = {}
    resp = send_get_request(
        url=f"{token_url}/v/api/getToken",
        headers=headers,
        req_session=REQ_SESSION,
        timeout=3,
        proxies=proxy,
    )
    if resp["resp_status"]:
        token = resp["resp_data"]["token"]
    else:
        token = ""
    return token


def get_kk_data(kw: str, kk_url, kk_channel: str, proxy_model: int = 0) -> dict:
    """
    获取kk数据
    """
    token = get_token(token_url=kk_url)
    if proxy_model:
        token = token or get_token(token_url=kk_url, proxy_model=1)

    kk_channel_map = {
        "jz": f"{kk_url}/v/api/getJuzi",
        "tt": f"{kk_url}/v/api/getTTZJB",
        "df": f"{kk_url}/v/api/getDyfx",
    }
    headers = {
        **data_config.SPIDER_CONFIG["REQUEST_HEADERS"],
        **{
            "Origin": kk_url,
            "Content-Type": "application/json",
        },
    }
    if proxy_model:
        proxy = {
            "http": data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_URL"],
            "https": data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_URL"],
        }
        headers.update(
            data_config.SPIDER_CONFIG["SPIDER_PROXY_CONFIG"]["PROXY_HEADERS"]
        )
        LOGGER.info(f"KK Spider 使用代理获取 {kk_channel} 数据")
    else:
        proxy = {}
    data = {"name": kw, "token": token}
    LOGGER.info(f"KK Spider 请求 {kk_channel} 资源通道: {kk_channel_map[kk_channel]}")
    resp = send_post_request(
        url=kk_channel_map[kk_channel],
        headers=headers,
        data=data,
        req_session=REQ_SESSION,
        timeout=3,
        proxies=proxy,
    )
    if resp["resp_status"]:
        if resp["resp_data"].get("list", []):
            result = {kk_channel: resp["resp_data"]["list"]}
        else:
            # 抓取成功，但是目标服务器返回失败，考虑使用代理抓取
            result = {}
            LOGGER.error(
                f"KK Spider 请求 {kk_channel} 资源通道成功，但结果不对: {resp['resp_data']}"
            )
    else:
        result = {}
        LOGGER.error(f"KK Spider 请求 {kk_channel} 资源通道失败: {resp['resp_data']}")
    return result


def start(kw: str, host_url: str = "", proxy_model: int = 0) -> dict:
    """
    启动 KK 爬虫
    """
    # 抓取 kk_channel 为 kk 和 xy 的数据
    result = {}
    kk_url_list = Config.SOURCE_CONFIG["kk"]
    if host_url:
        kk_url_list = [host_url]
    # kk_url_list = ["http://m.kkqws.com"]
    # 对 kk_url_list 随机打乱
    random.shuffle(kk_url_list)
    for kk_url in kk_url_list:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            LOGGER.info(f"KK Spider 请求 {kk_url} 资源通道")
            for kk_channel in ["jz", "tt", "df"]:
                futures.append(
                    executor.submit(get_kk_data, kw, kk_url, kk_channel, proxy_model)
                )
            for future in concurrent.futures.as_completed(futures):
                spider_data = future.result()
                if spider_data:
                    result.update(spider_data)

            if result:
                break

    return result


if __name__ == "__main__":
    res = start(kw="北上", proxy_model=0)
    print(res)
