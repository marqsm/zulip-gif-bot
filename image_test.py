import opc
from PIL import Image, ImageFilter


ADDRESS = '10.0.5.184:7890'
# Create a client object
client = opc.Client(ADDRESS)
matrixWidth = 64
matrixHeight = 16
imageWidth = 0
imageHeight = 0


class ImageSequence:
    def __init__(self, im):
        self.im = im

    def __getitem__(self, ix):
        try:
            if ix:
                self.im.seek(ix)
            return self.im
        except EOFError:
            raise IndexError  # end of sequence


def showImage(ledImage, client):
    # Test if it can connect
        my_pixels = []
        for i in xrange(0, matrix_size):
            x = i % 64
            y = int(i / 64)
            if (x < imageWidth) and (y < imageHeight):
                r, g, b, a = ledImage.getpixel((x, y))
                if a == 0:
                    r, g, b = 0, 0, 0
                my_pixels.append((b, g, r))
            else:
                my_pixels.append((0, 0, 0))

        # dump data to LED display
        client.put_pixels(my_pixels, channel=0)


try:
    original = Image.open("megaman.png")
    # original = Image.open("megaman_run.gif")
except:
    print "unable to load image"

print "The size of the image is: "
print(original.format, original.size, original.mode)
print(original.getpixel((16, 5)))
imageWidth, imageHeight = original.size
ledImage = original.point(lambda p: p)
# ledImage = original

if client.can_connect():
    print 'connected to %s' % ADDRESS
    frame = 0
    matrix_size = matrixWidth * matrixHeight
    showImage(ledImage, client)
    # for frame in ImageSequence(original):
    #     print(frame)
    #     print(frame.format, frame.size, frame.mode)
    #     print(frame.getpixel((16, 15)))
    #     showImage(frame, client)
        # ...do something to frame..
