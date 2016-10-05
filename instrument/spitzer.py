#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2015-10-05 22:04
# Python Version :  %PYVER%
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
spitzer.py

utility classes for handling spitzer data
"""

import os
import sys
import glob
import copy
from astropy.io import fits
import re


class SpitzerBCD(object):

    dkey = {'image': ('_cbcd.fits', '_bcd.fits'),
            'sigma': ('_cbunc.fits', '_bunc.fits'),
            'dmask': ('_bimsk.fits', '_bbmsk.fits')
            }

    pdkey = {'image': '_maic.fits',
             'sigma': '_munc.fits',
             'cover': '_mcov.fits'
             }

    def __init__(self, aor, rootdir, **dkey):
        self.aor = int(aor)
        self.rootdir = os.path.abspath(rootdir)
        self.datadir = os.path.abspath(os.path.join(self.rootdir,
                                                    'r{0:d}'.format(self.aor)))
        self.dkey.update(dkey)

    def get_imlist(self, chan, key):
        for glob_key in self.dkey[key]:
            imlist = glob.glob(
                os.path.join(self.datadir, chan, 'bcd', 'S*' + glob_key))
            if len(imlist) > 0:
                break
        else:
            print "[!] image list is empty, abort"
            sys.exit(1)
        return imlist

    def get_pbcd(self, chan, key):
        imlist = glob.glob(os.path.join(
            self.datadir, chan, 'pbcd', 'S*' + self.pdkey[key]))
        if len(imlist) > 0:
            return imlist[0]
        else:
            return None

    def get_imlists(self, chan):
        print "collect files from", self.datadir
        for key in self.dkey['image']:
            images = glob.glob(
                os.path.join(self.datadir, chan, 'bcd', 'S*' + key))
            if len(images) > 0:
                break
        else:
            print "[!] image list is empty, abort"
            sys.exit(1)
        imgkey = key
        for key in self.dkey['sigma']:
            if os.path.isfile(images[0].replace(imgkey, key)):
                sigmas = [i.replace(imgkey, key) for i in images]
                break
        else:
            print "[!] sigma list is empty, abort"
            sys.exit(1)
        for key in self.dkey['dmask']:
            if os.path.isfile(images[0].replace(imgkey, key)):
                dmasks = [i.replace(imgkey, key) for i in images]
                break
        else:
            print "[!] dmask list is empty, abort"
            sys.exit(1)
        return images, sigmas, dmasks


def resolve_bcddir(rootdir):
    # get aors:
    subdirs = [d for d in os.listdir(rootdir)
               if os.path.isdir(os.path.join(rootdir, d)) and d[0] == 'r']
    aors = []
    for d in subdirs:
        try:
            aors.append(int(d[1:]))
        except ValueError:
            pass
    return aors


def isscan(fname):
    '''
     check whether an image is in scan mode
    '''
    hdulist = fits.open(fname)
    if 'Phot' in hdulist[0].header['AOT_TYPE']:
        print hdulist[0].header['AOT_TYPE']
        hdulist.close()
        return False
    else:
        print hdulist[0].header['AOT_TYPE']
        hdulist.close()
        return True


class SpitzerOBS(object):
    '''
    manage a group of BCDs
    '''
    dband = {'ch1': ('IRAC', 'ch1'),
             'ch2': ('IRAC', 'ch2'),
             'ch3': ('IRAC', 'ch2'),
             'ch4': ('IRAC', 'ch3'),
             'mips24': ('MIPS', 'ch1'),
             'mips70': ('MIPS', 'ch2'),
             'mips160': ('MIPS', 'ch3'),
             }

    def __init__(self, bcds, band):

        self.band = band
        self.instru, self.chan = self.dband[band]
        self.images = []
        self.sigmas = []
        self.dmasks = []
        self.bcds = bcds
        for bcd in self.bcds:
            images, sigmas, dmasks = bcd.get_imlists(self.chan)
            self.images.extend(images)
            self.sigmas.extend(sigmas)
            self.dmasks.extend(dmasks)

    def get_imlists(self, exclude=None):
        if exclude is None:
            filt = re.compile(r'laskdjfkljasdfkjlasdfjl')
        else:
            filt = re.compile(exclude)
        imglist = [i for i in self.images if not filt.search(i)]
        siglist = [i for i in self.sigmas if not filt.search(i)]
        msklist = [i for i in self.dmasks if not filt.search(i)]
        return imglist, siglist, msklist


class MopexConf(object):
    '''
    Helper class for preparing MOPEX job
    '''

    def __init__(self, obs, mopexroot=None):
        self.mopexroot = os.environ.get('MOPEX_INSTALLATION', None) \
                if mopexroot is None else mopexroot
        if self.mopexroot is None:
            raise RuntimeError("unable to find MOPEX installation")
        self.obs = obs
        self.pmask = self.get_pmask()

    def get_pmask(self):

        pmaskdir = os.path.join(self.mopexroot, 'cal')
        if self.obs.instru == 'MIPS':
            pmask = os.path.join(pmaskdir, self.obs.chan + "_pmask.fits")
        else:
            print "Auto-pmask for IRAC is not implemented yet."
            pmask = None
        return pmask

    def compose_imglist(self, outdir, exclude=None, extra=None):
        '''
        extra parameter helps generate additional files:
            (subdir, listname, prefix, surfix)
        '''
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
            print ' + {0:s}'.format(outdir)
        images, sigmas, dmasks = self.obs.get_imlists(exclude=exclude)
        # write lists
        with open(os.path.join(outdir, 'imageList.txt'), 'w') as fo:
            for i in images:
                fo.write(i + '\n')
        with open(os.path.join(outdir, 'sigmaList.txt'), 'w') as fo:
            for i in sigmas:
                fo.write(i + '\n')
        with open(os.path.join(outdir, 'dmaskList.txt'), 'w') as fo:
            for i in dmasks:
                fo.write(i + '\n')
        if extra is not None:
            for subdir, listname, prefix, suffix in extra:
                exdir = os.path.join(outdir, subdir)
                if not os.path.isdir(exdir):
                    os.makedirs(exdir)
                    print ' + {0:s}'.format(exdir)
                with open(os.path.join(exdir, listname), 'w') as fo:
                    for i in images:
                        basename = os.path.basename(i).rstrip('.fits')
                        fo.write(os.path.join(
                            exdir,
                            prefix + basename + suffix + '.fits\n'))
        return images, sigmas, dmasks


class MopexNameList(object):
    def __init__(self, template):
        with open(template, 'r') as fo:
            nl_orig = fo.readlines()
        # parse name_list
        comments = []
        parameters = {}
        indices = {}
        in_module = False
        for i, ln in enumerate(nl_orig):
            ln = ln.strip()
            if ln.startswith('#'):
                comments.append((i, ln))
            elif ln.startswith('&'):
                if ln.startswith('&END'):
                    in_module = False
                else:
                    in_module = ln.lstrip('&')
            elif len(ln) < 1:
                continue
            else:
                kv = [s.strip() for s in ln.split('=', 1)]
                if len(kv) > 1:
                    key, value = kv
                else:
                    key = kv[0]
                    value = ''
                if in_module:
                    parameters[in_module] = parameters.get(in_module, {})
                    parameters[in_module][key] = value
                    indices[in_module] = indices.get(in_module, {})
                    indices[in_module][key] = i
                else:
                    parameters[key] = value
                    indices[key] = i
        self.nl_orig = nl_orig
        self.comments = comments
        self.parameters = parameters
        self._indices = indices

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                self.parameters[k].update(v)
            else:
                self.parameters[k] = str(v)

    def dump(self, output, **kwargs):
        parameters = copy.deepcopy(self.parameters)
        for k, v in kwargs.items():
            if isinstance(v, dict):
                parameters[k].update(v)
            else:
                parameters[k] = str(v)
        nl = self.nl_orig[:]
        for k, v in parameters.items():
            if isinstance(v, dict):
                for nk, nv in v.items():
                    i = self._indices[k][nk]
                    nl[i] = ' = '.join([nk, nv]) + '\n'
            else:
                i = self._indices[k]
                nl[i] = ' = '.join([k, v]) + '\n'
        with open(output, 'w') as fo:
            fo.write(''.join(nl))
        return output
