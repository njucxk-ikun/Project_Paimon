import requests
import pandas as pd
import time
import os

# 使用您提供的headers
headers = {
    'cookie': 'buvid3=3B17E9C5-9330-C0CB-096C-F9F4288FB6EF91063infoc; b_nut=1698650891; i-wanna-go-back=-1; b_ut=7; _uuid=4A8A9E48-6376-66FE-A138-FA1554710818D91524infoc; enable_web_push=DISABLE; buvid4=1A25D353-64CE-3B21-0134-A85EDED1A69992270-023103015-ToEVxC3BtTo5GSkOodJ2CQ%3D%3D; rpdid=|(klY~uuYkku0J\'uYm)Yl|muu; header_theme_version=CLOSE; DedeUserID=399491832; DedeUserID__ckMd5=06cf719a3ba1243d; buvid_fp_plain=undefined; LIVE_BUVID=AUTO1816990129683499; hit-dyn-v2=1; fingerprint=de101956ab8082422e245d503f726c85; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW2; CURRENT_QUALITY=64; buvid_fp=de101956ab8082422e245d503f726c85; PVID=5; SESSDATA=28af58fb%2C1732628549%2Ccb499%2A51CjAmNm3QFxefnxnH0H6TemFuxSB7L5BXOBYItxX0OxceG2KrIq_RYId3O7VMnkWyyAMSVlQ0dktQYVlJcFhHQmZCbjMzT0hmYlZCcWM0SG1MM0tLWUp6eFdFNld1ckhLSDg0b2lxbzhoNlNJaVhGRDktc1VfdnZDazNHVWloYjhXQ0YtbjNTQWxRIIEC; bili_jct=ef91fbd38d2c8f1770ef489ab28f54a3; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMw3',
    'referer': 'https://www.bilibili.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 SLBrowser/9.0.3.5211 SLBChan/111',
}

# 景区关键词配置 - 已移除"胡雪岩"关键词
SCENIC_SPOTS = {
    "长白山景区": ["长白山", "长白山旅游", "长白山天池"],
    "朝鲜族风俗园": ["朝鲜族风俗园", "朝鲜族民俗园"],
    "外滩": ["外滩", "北外滩", "外滩夜景", "上海外滩"],
    "胡雪岩故居": ["胡庆余堂", "胡雪岩故居", "胡雪岩旧居"],  # 移除了"胡雪岩"
    "龙坞茶镇，龙井村": ["龙坞茶镇", "龙井村"],
    "莫高窟": ["莫高窟", "敦煌莫高窟"],
    "鸣沙山月牙泉": ["鸣沙山", "月牙泉", "敦煌鸣沙山", "鸣沙山月牙泉"]
}


def search_scenic_videos(scenic_name, keywords, max_pages=3):
    """
    搜索指定景区的相关视频，合并所有关键词的结果
    """
    all_videos = []
    seen_bvids = set()  # 用于去重

    for keyword in keywords:
        print(f"正在搜索景区 '{scenic_name}' 的关键词: {keyword}")

        for page in range(1, max_pages + 1):
            print(f"  正在搜索第 {page} 页...")

            # 构造搜索URL
            search_url = "https://api.bilibili.com/x/web-interface/search/type"
            params = {
                'keyword': keyword,
                'search_type': 'video',
                'page': page,
                'page_size': 50,  # 每页最多50条结果
                'order': 'click',  # 按点击量排序
            }

            try:
                response = requests.get(search_url, params=params, headers=headers)
                response.raise_for_status()  # 检查请求是否成功

                data = response.json()
                if data['code'] != 0:
                    print(f"  请求失败: {data['message']}")
                    break

                videos = data['data']['result']
                if not videos:
                    print(f"  第 {page} 页没有找到结果")
                    break

                # 处理每个视频
                for video in videos:
                    bvid = video.get('bvid', '')

                    # 去重
                    if bvid in seen_bvids:
                        continue
                    seen_bvids.add(bvid)

                    # 处理播放量（可能是数字或带"万"的字符串）
                    play_count = video.get('play', 0)
                    if isinstance(play_count, str) and '万' in play_count:
                        play_count = float(play_count.replace('万', '')) * 10000
                    elif isinstance(play_count, str):
                        play_count = int(play_count) if play_count.isdigit() else 0

                    # 处理评论数
                    review_count = video.get('review', 0)
                    if isinstance(review_count, str) and '万' in review_count:
                        review_count = float(review_count.replace('万', '')) * 10000
                    elif isinstance(review_count, str):
                        review_count = int(review_count) if review_count.isdigit() else 0

                    video_info = {
                        'bvid': bvid,
                        '播放量': int(play_count),
                        '评论数': int(review_count),
                        '景区': scenic_name,
                        '搜索关键词': keyword
                    }
                    all_videos.append(video_info)

                print(f"  第 {page} 页，目前总共找到 {len(all_videos)} 个视频")

                # 添加延迟，避免请求过于频繁
                time.sleep(0.5)

            except Exception as e:
                print(f"  搜索第 {page} 页时出错: {e}")
                break

    # 按播放量排序并取前100个
    all_videos.sort(key=lambda x: x['播放量'], reverse=True)
    top_100_videos = all_videos[:100]

    return top_100_videos


def main():
    print("开始搜索各景区相关视频...")

    results = []

    # 搜索每个景区的视频
    for scenic_name, keywords in SCENIC_SPOTS.items():
        print(f"\n=== 正在处理景区: {scenic_name} ===")
        scenic_videos = search_scenic_videos(scenic_name, keywords)

        # 计算总播放量和总评论数
        total_play = sum(v['播放量'] for v in scenic_videos)
        total_review = sum(v['评论数'] for v in scenic_videos)

        results.append({
            '景区': scenic_name,
            '总播放量': total_play,
            '总评论数': total_review
        })

        print(f"景区 '{scenic_name}' 找到 {len(scenic_videos)} 个视频")
        print(f"总播放量: {total_play:,} | 总评论数: {total_review:,}")

        time.sleep(1)  # 景区间延迟

    if not results:
        print("没有找到相关视频")
        return

    # 保存结果
    df_results = pd.DataFrame(results)

    # 获取当前工作目录
    current_dir = os.getcwd()
    results_file_path = os.path.join(current_dir, '各景区视频统计结果.csv')

    df_results.to_csv(results_file_path, index=False, encoding='utf-8-sig')

    print(f"\n统计结果已保存到: {results_file_path}")

    # 打印统计结果
    print("\n=== 各景区视频统计结果 ===")
    for result in results:
        print(f"{result['景区']}: 总播放量 {result['总播放量']:,} | 总评论数 {result['总评论数']:,}")


if __name__ == '__main__':
    main()