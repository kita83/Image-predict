import os
import sys
import argparse
import time
import requests
import random
import configparser
from picamera import PiCamera
from google.cloud import automl_v1beta1

MODE_AUTO = 'auto'
MODE_MANUAL = 'manual'


def get_prediction(content):
    conf = get_predict_conf()

    prediction_client = automl_v1beta1.PredictionServiceClient()
    prediction_client = prediction_client.from_service_account_json(conf['key_file'])

    name = 'projects/{}/locations/us-central1/models/{}'.format(conf['project_id'], conf['model_id'])
    payload = {'image': {'image_bytes': content}}
    params = {}
    request = prediction_client.predict(name, payload, params)
    return request


def main(mode):
    while True:
        with PiCamera() as camera:
            camera.resolution = (800, 600)
            # 検証用にプレビュー画面を出す
            camera.start_preview(fullscreen=False, window=(50, 50, 200, 300))
            if mode == MODE_AUTO:
                time.sleep(5)
                camera.capture('image.jpg')
            elif mode == MODE_MANUAL:
                while True:
                    input_ = input('1:撮影 2:解析 3:終了 input: ')
                    if input_ == '1':
                        camera.capture('image.jpg')
                    elif input_ == '2':
                        break
                    elif input_ == '3':
                        sys.exit()
                    else:
                        print('1から3の整数を指定してください')
            else:
                print('Caputure mode is undefined')
                sys.exit(1)

        # キャプチャ画像を取得
        with open('image.jpg', 'rb') as f:
            content = f.read()

        # AutoMLで予測
        response = get_prediction(content)
        print(response)

        results = response.payload
        if len(results) != 0:
            labels = ['vongole']
            # 認識したいラベルに一致する結果を抽出
            matched_labels = [result for result in results if result.display_name in labels]
            for label in matched_labels:
                score = label.classification.score
                if score >= 0.9:
                    # 90%以上の予測結果ならSlack通知
                    slackPost(label.display_name, score)
        else:
            print('認識情報なし')


def slackPost(display_name, score):
    """Slackに画像付きで投稿する"""
    suffix = ['ボンゴレチャン ヲ ケンシュツ シマシタ', 'ボンゴレちゃん発見！']
    conf = get_slack_conf()
    comment = '[{}] {} ボンゴレちゃん度： {}'.format(display_name, random.choice(suffix), round(score, 2))
    files = {'file': open("image.jpg", 'rb')}
    param = {
        'token': conf['token'],
        'channels': conf['channel_id'],
        'filename': "raspi",
        'initial_comment': comment,
        'title': "検知！"
    }
    requests.post(url=conf['url'], params=param, files=files)


def get_slack_conf():
    ini_path = os.path.join(os.path.dirname(__file__), 'automl.ini')
    if not os.path.exists(ini_path):
        sys.stderr.write('{} 設定ファイルが見つかりません'.format(ini_path))
        sys.exit(1)
    conf = configparser.ConfigParser()
    conf.read(ini_path)
    params = {
        'url': conf.get('Slack', 'url'),
        'token': conf.get('Slack', 'token'),
        'channel_id': conf.get('Slack', 'channel_id')
    }
    return params


def get_predict_conf():
    ini_path = os.path.join(os.path.dirname(__file__), 'automl.ini')
    if not os.path.exists(ini_path):
        sys.stderr.write('{} 設定ファイルが見つかりません'.format(ini_path))
        sys.exit(1)
    conf = configparser.ConfigParser()
    conf.read(ini_path)
    params = {
        'project_id': conf.get('AutoML', 'PROJECT_ID'),
        'model_id': conf.get('AutoML', 'MODEL_ID'),
        'key_file': conf.get('AutoML', 'KEY_FILE')
    }
    return params


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", help="auto photo mode")
    args = parser.parse_args()
    mode = MODE_MANUAL
    if args.auto:
        mode = MODE_AUTO

    main(mode)
