#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2015-11-01 12:54
# Python Version :  %PYVER%
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
wiyn.py

Utilities for handling WIYN ODI data
"""

import os


class WIYNLayout(object):

    def __init__(self, binning=11.0):

        self.NCX = 8
        self.NCY = 8
        self.NOX = 8
        self.NOY = 8

        self.CW = 480 / binning   # cell width
        self.CH = 494 / binning   # cell height
        self.CGW = 28 / binning   # cell gap width
        self.CGH = 11 / binning   # cell gap height

        self.OW = self.CW * self.NCX + self.CGW * (self.NCX - 1)  # ota width
        self.OH = self.CH * self.NCY + self.CGH * (self.NCY - 1)  # ota height
        self.OG = 200 / binning   # ota gap (width and height)
        self.ps = 0.11 * binning  # pixel scale

    def get_xy_from_oxy(self, ox, oy, x, y):
        '''Return global x and y with given ota id and ota x and y'''
        gx = ox * (self.OW + self.OG) + x
        gy = oy * (self.OH + self.OG) + y
        return gx, gy

    def get_ota_rect(self, ox, oy):
        '''Return rect (in global x and y: l, r, b, t) of ota with given id'''
        left, bottom = self.get_xy_from_oxy(ox, oy, 0, 0)
        right, top = self.get_xy_from_oxy(ox, oy, self.OW, self.OH)
        return (left, right), (bottom, top)

    def get_cell_rect(self, ox, oy, cx, cy):
        '''Return rect of (in global x and y: l, r, b, t) of cell with
        given ota id and cell id'''
        left, bottom = self.get_xy_from_oxy(ox, oy, cx * (self.CW + self.CGW),
                                            cy * (self.CH + self.CGH))
        right = left + self.CW
        top = bottom + self.CH
        return (left, right), (bottom, top)

    def get_ota_bins(self):
        '''Return two list of tuples, for x and y direction, respectively.
        The each tuple in each list is the bound left and right global
        coordinates for that ota'''
        xbin = []
        ybin = []
        for o in range(max(self.NOX, self.NOY)):
            rect = self.get_ota_rect(o, o)
            xbin.append(rect[0])
            ybin.append(rect[1])
        return xbin[:self.NOX], ybin[:self.NOY]

    def get_cell_bins(self):
        '''Return two list of tuples, for x and y direction, respectively.
        The each tuple in each list is the bound left and right global
        coordinates for that cell'''
        xbin = []
        ybin = []
        for o in range(max(self.NOX, self.NOY)):
            _xbin = []
            _ybin = []
            for c in range(max(self.NCX, self.NCY)):
                rect = self.get_cell_rect(o, o, c, c)
                _xbin.append(rect[0])
                _ybin.append(rect[1])
            xbin += _xbin[:self.NCX]
            ybin += _ybin[:self.NCY]
        return xbin[:self.NOX], ybin[:self.NOY]


class WIYNFact(object):
    broken_cells = {
        #
        # Original pODI OTAs
        # pODI ODI5
        '13838': [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6),
                  (7, 7)],                                           # 00   55
        '13880': [(7, 0)],                                           # 16   25
        '13835': [(0, 0)],                                           # 22   26
        '13901': [(6, 6)],                                           # 23   14
        '13968': [(7, 0)],                                           # 24   11
        '13974': [],                                                 # 32   12
        '13879': [],                                                 # 33   45
        '13923': [(1, 7), (3, 1)],                                   # 34   13
        '13792': [],                                                 # 42   46
        '13902': [(1, 5), (7, 0)],                                   # 43   36
        '13947': [],                                                 # 44   35
        '13946': [(7, 0)],                                           # 55   16
        '13837': [(1, 3), (3, 1)],                                   # 61   15
        #
        # Additions for ODI 5x6
        #
        '17189': [(4, 0),
                  (0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7),
                  (6, 7), (7, 7), ],                                 # --   21
        '17187': [(1, 1), (6, 1)],                                   # --   31
        '17234': [(0, 0), (0, 1), (1, 0), (1, 1), (6, 0),
                  (0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7),
                  (6, 7), (7, 7), ],                                 # --   41
        '17253': [(0, 7),
                  (6, 0), (6, 1), (6, 2), (6, 3)],                   # --   51
        '17297': [],                                                 # --   22
        '17231': [],                                                 # --   32
        '17277': [(0, 1), (0, 2), (1, 1)],                           # --   42
        '17190': [(1, 5),
                  (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5),
                  (7, 6), (7, 7), ],                                 # --   52
        '17144': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 6),
                  (0, 7), (1, 7)],                                   # --   23
        '17121': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
                  (0, 7), (1, 7), (7, 3)],                           # --   33
        '17341': [],                                                 # --   43
        '17278': [(7, 6)],                                           # --   53
        '17275': [(0, 0), (0, 1), (0, 2), (1, 1)],                   # --   24
        '17166': [(3, 0), (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
                  (6, 6), (6, 7)],                                   # --   34
        '17167': [(6, 0)],                                           # --   44
        '17122': [(5, 0), (6, 0), (7, 0)],                           # --   54
        '8101': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
                 (0, 6), (0, 7)],                                    # --   56
        }
    ota_id = {11: 13968, 12: 13974, 13: 13923, 14: 13901, 15: 13837, 16: 13946,
              21: 17189, 22: 17297, 23: 17144, 24: 17275, 25: 13880, 26: 13835,
              31: 17278, 32: 17231, 33: 17121, 34: 17166, 35: 13947, 36: 13902,
              41: 17234, 42: 17277, 43: 17341, 44: 17167, 45: 13879, 46: 13792,
              51: 17253, 52: 17190, 53: 17187, 54: 17122, 55: 13838, 56: 8101,
              }
    ota_order = [33, 34, 43, 44, 32,
                 23, 24, 42, 35, 53,
                 45, 54, 22, 25, 52,
                 55, 31, 13, 41, 14,
                 36, 46, 21, 12, 15,
                 51, 26, 56, 11, 16]
    ota_order_podi = [33, 34, 44,
                      43, 42, 32,
                      22, 23, 24]

    @classmethod
    def get_broken_cells(cls, ox, oy):
        '''Return a list of broken cell id (cx and cy) with given OTA id'''
        return cls.broken_cells.get(
            str(cls.ota_id.get(int(ox * 10 + oy), 'null')), [])

    @classmethod
    def get_ota_xy(cls, ext):
        return cls.ota_order[ext - 1]

    @classmethod
    def get_ota_xy_podi(cls, ext):
        return cls.ota_order_podi[ext - 1]

    @classmethod
    def get_bbox(cls):
        '''return range of ra and dec for image'''
        e = 19. / 60.
        w = 26. / 60.
        n = s = 27. / 60.
        return (-w, e), (-s, n)

    @classmethod
    def get_guide_ota_checker(cls):
        return os.path.join(os.path.dirname(__file__),
                            'odi_guide_ota_checker.fits')

if __name__ == '__main__':

    from astropy.io import fits
    from astropy import wcs
    import numpy as np

    wl = WIYNLayout()
    # full range 8 OTAs
    (_, right), (_, top) = wl.get_ota_rect(7, 7)
    blank = np.ones((right + 1, top + 1)) * np.NAN
    for ox in range(0, 8):
        for oy in range(0, 8):
            flag = 0  # not used flag 0
            if (ox in range(1, 6)) and (oy in range(1, 7)):
                flag += 1   # ODI flag 1
            if (ox in range(2, 5)) and (oy in range(2, 5)):
                flag += 2   # pODI flag 2
            list_of_broken_cells = WIYNFact.get_broken_cells(ox, oy)
            for cx in range(8):
                for cy in range(8):
                    (cell_left, cell_right), (cell_bottom, cell_top) = \
                            wl.get_cell_rect(ox, oy, cx, cy)
                    # here need to flip y
                    if (cx, 7 - cy) in list_of_broken_cells:
                        _flag = -flag
                    else:
                        _flag = flag
                    blank[cell_bottom:cell_top, cell_left:cell_right] = _flag
    # east to the left
    # blank = np.fliplr(blank)
    # import matplotlib.pyplot as plt
    # plt.imshow(blank, aspect='equal', interpolation='none')
    # plt.show()
    # add wcs
    w = wcs.WCS(naxis=2)
    # w.wcs.crpix = [blank.shape[0] / 2, blank.shape[1] / 2]
    ccol, crow = wl.get_xy_from_oxy(3, 3, wl.OW / 2.0, wl.OH / 2.0)
    w.wcs.crpix = [blank.shape[1]-ccol, crow]
    # crval
    tra = 14.79625
    tdec = -1.23363888889
    w.wcs.crval = [tra,  tdec]
    w.wcs.cd = [(wl.ps / 3600., 0), (0, wl.ps / 3600.)]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    header = w.to_header()
    # create fits file
    outfname = 'wiyn_skeleton.fits'
    hdu = fits.PrimaryHDU(blank, header=header)
    hdulist = fits.HDUList([hdu])
    hdulist.writeto(outfname, clobber=True)
