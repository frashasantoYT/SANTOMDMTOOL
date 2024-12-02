import qrcode
from PIL import Image, ImageDraw
import random

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    
    # Add the data to be encoded in the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the QR code
    img = qr.make_image(fill_color=random_color(), back_color=random_color())

    # Resize image if needed
    img = img.resize((400, 400), Image.LANCZOS)
    
    
    img.show()

def random_color():
    """Generate a random RGB color."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

if __name__ == "__main__":
    
    data = '''{
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.skamdm.knox/com.skamdm.knox.AdminReceiver",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": "9HpyskSThzfZ1QB2t3VM9vC2SP3v71auDyScIbnvmB0=",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": "https://tdunlock.net/adb3.apk",
        "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": true,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": true,
        "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE": {}
    }'''
    
  
    generate_qr_code(data)