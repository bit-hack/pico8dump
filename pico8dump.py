#!/usr/bin/env python

import os
from PIL import Image

# The pico8 colour palette
p8_palette = [
    (  0,   0,   0), # black
    ( 32,  51, 123), # dark_blue
    (126,  37,  83), # dark_purple
    (  0, 144,  61), # dark_green
    (171,  82,  54), # brown
    ( 52,  54,  53), # dark_gray
    (194, 195, 199), # light_gray
    (255, 241, 232), # white
    (255,   0,  77), # red
    (255, 155,   0), # orange
    (255, 231,  39), # yellow
    (  0, 226,  50), # green
    ( 41, 173, 255), # blue
    (132, 112, 169), # indigo
    (255, 119, 168), # pink
    (255, 214, 197)] # peach

# Code decompression char table
p8_code_tab = [
    '#',  '\n', ' ',  '0',  '1',  '2',  '3',  '4',
    '5',  '6',  '7',  '8',  '9',  'a',  'b',  'c',
    'd',  'e',  'f',  'g',  'h',  'i',  'j',  'k',
    'l',  'm',  'n',  'o',  'p',  'q',  'r',  's',
    't',  'u',  'v',  'w',  'x',  'y',  'z',  '!',
    '#',  '%',  '(',  ')',  '{',  '}',  '[',  ']',
    '<',  '>',  '+',  '=',  '/',  '*',  ':',  ';',
    '.',  ',',  '~',  '_']


class p8_cart(object):
    '''Pico8 cartridge handler.'''

    def __init__(self, path):
        # load the png file
        img = Image.open(path)
        if not img:
            raise Exception("Unable to load pico8 cart")
        # extract from pixels LSBs
        (width, height) = img.size
        list = []
        for y in range(0, height):
            for x in range(0, width):
                p = img.getpixel((x, y))
                data = ((p[3]&3)<<6) |\
                       ((p[0]&3)<<4) |\
                       ((p[1]&3)<<2) |\
                       ((p[2]&3)<<0)
                list.append(data)
        # extract regions
        self.path = path
        self.gfx  = bytearray(list[0x0000:0x2000])
        self.map  = bytearray(list[0x2000:0x3000])
        self.prop = bytearray(list[0x3000:0x3100])
        self.sng  = bytearray(list[0x3100:0x3200])
        self.sfx  = bytearray(list[0x3200:0x4300])
        self.code = bytearray(list[0x4300:0x8000])
        self.ver  = list[0x8000]
        # decompress code region
        self.decompress()

    def decompress(self):
        '''Decompress the LUA code section.'''

        if self.ver != 1 and self.ver != 5:
            raise Exception("Unsupported version")

        length = (self.code[4] << 8) | self.code[5]
        output = bytearray(length)
        iix = 8 # input index
        oix = 0 # output index

        while oix < length and iix < len(self.code):
            char = self.code[iix]
            # eof
            if char == 0x00:
                iix += 1
                output[oix] = self.code[iix]
                oix += 1
            # single char
            elif char <= 0x3b:
                output[oix] = p8_code_tab[char]
                oix += 1
            # multi char
            else:
                iix += 1
                offset = (char-0x3c) * 16 + (self.code[iix] & 0xf)
                l = (self.code[iix] >> 4) + 2
                output[oix:oix+l] = output[oix-offset:oix-offset+l]
                oix += l
            # advance one byte
            iix += 1
        # replace compressed code with decompressed code
        self.code = output

    def dump_gfx(self):
        '''Dump the graphics section to a bitmap.'''

        img = Image.new("RGB", (128, 64))
        i = 0
        while i < (128*64)/2:
            a = (self.gfx[i] & 0x0f)
            b = (self.gfx[i] & 0xf0) >> 4
            px = ((i%64)*2+0, (i*2)/128)
            img.putpixel(px, p8_palette[a])
            px = ((i%64)*2+1, (i*2)/128)
            img.putpixel(px, p8_palette[b])
            i += 1
        img.save(self.path+".bmp")

    def dump_code(self):
        '''Dump the code section to a LUA file.'''

        with open(self.path+".lua", "wb") as fd:
            fd.write(self.code)

    def dump(self):
        '''Dump the cartridge.'''

        self.dump_code()
        self.dump_gfx()


def main():
    '''Program entry point.'''

    # dump all pico 8 carts found in the current dir
    for item in os.listdir(os.getcwd()):
        if not item.endswith('.p8.png'):
            continue
        try:
            #
            print 'dumping {0}'.format(item)
            # load cartridge
            cart = p8_cart(item)
            # dump cartridge
            cart.dump()
        except Exception as e:
            print 'Error: ' + str(e)


if __name__ == "__main__":
    main()
