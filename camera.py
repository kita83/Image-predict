from picamera import PiCamera
from time import sleep


def main():
    with PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.start_preview()
        while True:
            input_ = input('1:撮影 2:終了 input: ')
            if input_ == '1':
                camera.capture('image.jpg')
            elif input_ == '2':
                break


if __name__ == '__main__':
    main()

