from PIL import Image
import base64 as b64

im = Image.open('greenbulb.ico')

#xsize, ysize = im.size
#part = im.crop((4,0,xsize, ysize))
#im.paste(part,(0,0,xsize-4,ysize))
#im.save('mod.png')

im.save('temp.png')
with open('temp.png', 'rb') as image_file:
    image_data = b64.b64encode(image_file.read())
print(image_data)
