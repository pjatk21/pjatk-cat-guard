from pathlib import Path

from dotenv import load_dotenv

from shared.db import init_connection
from shared.documents import VerificationRequest

load_dotenv()
init_connection()


def dump_images():
    vrs = VerificationRequest.objects(photo_front__ne=None, photo_back__ne=None)

    for vr in vrs:
        vr: VerificationRequest = vr  # Just for typing
        path = Path('./data/pictures').joinpath(str(vr.id))
        if not path.exists():
            path.mkdir(parents=True)

        with open(path.joinpath('photoFront.' + vr.photo_front.content_name.split('.')[-1]), 'wb') as f:
            f.write(vr.photo_front.photo)

        print('💾', f.name)

        with open(path.joinpath('photoBack.' + vr.photo_front.content_name.split('.')[-1]), 'wb') as f:
            f.write(vr.photo_back.photo)

        print('💾', f.name)
        print('✅', vr.id)


if __name__ == '__main__':
    dump_images()
