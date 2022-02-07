from starlette.datastructures import UploadFile
from starlette.templating import Jinja2Templates

from shared.consts import data_path
from shared.documents import VerificationRequest

templates = Jinja2Templates(directory="webpanel/templates")


def save_picture(vr: VerificationRequest, photo_file: UploadFile, prefix: str):
    filename = f'verification-{prefix}-{photo_file.filename}'
    filedir = data_path.joinpath('pictures').joinpath(str(vr.id))
    filedir.mkdir(parents=True, exist_ok=True)
    filename = filedir.joinpath(filename)

    with open(filename, 'wb') as f:
        f.write(photo_file.file.read())

    return str(filename.absolute())
