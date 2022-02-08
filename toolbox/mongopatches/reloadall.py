from shared.db import init_connection
from shared.documents import VerificationRequest

init_connection()


def reload():
    vrs = VerificationRequest.objects.all()
    for vr in vrs:
        print(vr.id, vr.photo)
        vr.save()


if __name__ == '__main__':
    reload()
