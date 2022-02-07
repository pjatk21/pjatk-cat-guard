import re
from pathlib import Path

from bson import ObjectId
from dotenv import load_dotenv
from mongoengine import DoesNotExist

from shared.db import init_connection
from shared.documents import VerificationRequest, VerificationPhotos

load_dotenv()
init_connection()


def fix():
    pictures = Path('./data/pictures')

    for pics_path in pictures.glob('*'):
        front, back = [None] * 2
        for pic in pics_path.glob('*'):
            if re.search(r'[bB]ack', pic.name):
                back = str(pic.absolute())
            if re.search(r'[fF]ront', pic.name):
                front = str(pic.absolute())
        print('🔧', front, back)

        try:
            vr: VerificationRequest = VerificationRequest.objects(id=ObjectId(pics_path.name)).get()
            photos = VerificationPhotos()
            photos.front = front
            photos.back = back
            vr.photos = photos
            vr.save()
        except DoesNotExist:
            print('❌', pics_path.name, 'does not exist')
            continue
        print('✅', vr.id, 'updated')


if __name__ == '__main__':
    fix()
