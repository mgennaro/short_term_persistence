'''
A set of utilities to subtract an exposure from an other one,
using the astrodrizzle and blot functions.

It can be used to create the difference image between a first,
supposedly "persistence-free" image and subsequent exposures.
The resulting image should only be showing the residual
persistence
'''

from drizzlepac import astrodrizzle, ablot
from astropy.io import fits
import os, shutil

def driz_all(fltlist, ad_dict):

    '''
    Function to create the individual drizzled images using
    one image as reference

    :fltlist:
        List of flt files to be processed. Processing
        will happen in the provided order. The first
        image of the list will be used as reference

    :dict:
        Dictionary of parameters to pass to astrodrizzle
    '''

    ref = fltlist[0].replace('flt', 'drz')

    for im in fltlist:

        if os.path.exists(ref):
            astrodrizzle.AstroDrizzle(im,final_refimage=ref, **ad_dict)
        else:
            astrodrizzle.AstroDrizzle(im, **ad_dict)



def blot_back(drz, inp, out, extdrz, extflt):

    '''
    Function that blots back a drizzled image

    :drz:
        file name of the image to be blotted back

    :inp:
        file name of the destination reference frame flt

    :out:
        file name of the output

    :extdrz:
        extension number of the image to be blotted back (int type)

    :extflt:
        extension number of the destination reference image (int type)

    '''

    #Set the sky values to 0
    #fits.setval(inp,'MDRIZSKY',value=0.0,ext=extflt)
    #fits.setval(drz,'MDRIZSKY',value=0.0,ext=extdrz)

    print('Running blot_back on:')
    print (drz, inp, out)

    ablot.blot(drz+'['+str(extdrz)+']',inp+'['+str(extflt)+']',out, out_units='cps')

    return out



def subtract(im1, im2):

    '''
    Function that takes the difference of 2 images and saves the difference image.
    Both input images must be the same kind (drz/drz or flt/flt etc)

    :im1:
        image to be subtracted

    :im2:
        image from which to subtract
    '''

    d1 = fits.getdata(im1)
    d2 = fits.getdata(im2)
    root1 = im1.split('_')[0]
    root2 = im2.split('_')[0]
    delta = d2-d1
    suffix = im2.split('_')[-1]
    out = '_'.join([root1,root2,'diff',suffix])
    shutil.copy(im2,out)
    hdu = fits.open(out,mode='update')
    hdu[1].data=delta
    hdu.close()

    return out

def make_high_masks(master, thresh, inp, out=None, extdrz=1, extflt=1):
    # Not sure how sky works with blot in this case.
    # Perhaps converting coordinate positions is better (astropy WCS)
    '''
    Function that masks high pixel values from deep mosaic and
        produces masks in flt frame

    :master:
        file name of the deep image to generate mask from

    :thresh:
        Threshold over which to flag pixel values as high

    :inp:
        file name of the destination reference frame flt

    :out:
        file name of the output

    :extdrz:
        extension number of the image to be blotted back (int type)

    :extflt:
        extension number of the destination reference image (int type)

    '''

    master_mask = master.replace('_drz.fits', '_mastermask_{}.fits'.format(thresh))

    # Make mask in sky frame
    if not os.path.exists(master_mask):
        shutil.copy(master,master_mask)
        hdu = fits.open(master_mask, mode='update')
        hdu[extdrz].data[hdu[extdrz].data>=thresh] = 1.
        hdu[extdrz].data[hdu[extdrz].data<=thresh] = 0.
        hdu.close()

    if out == None:
        out = inp.replace('flt.fits', '_mask_{}.fits'.format(thresh))
    # Blot back sky space mask to flt frames
    mask = blot_back(master_mask, inp, out, extdrz, extflt)
    return mask
