'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================

singleton class for memory bitmap data management and sharing 

'''


from PIL import Image , ImageSequence


try:
    import gfx
except:
    pass


import wx
from fpdf import FPDF
import tempfile
#import sys
import os.path
import algorithms.words
import gui.utilities
import logging
import Resources

class imageData(object):
    val = None
    pil_images = []
    current_image = 0
    image_changed = True
    current_file=None
    nb_pages=0
    title=None
    subject=None
    keywords=None
    def __init__(self):
        void_file = os.path.join(Resources.get_resource_dir(),'no_preview.png')
        self.image_void = Image.open(void_file)
    def change_image(self,delta):
        " change the current page by delta"
        self.current_image += delta
        if self.current_image<0 or self.current_image>len(self.pil_images):
            self.current_image -= delta
        else:
            self.image_changed = True
            
    def get_image(self,image_num=None):
        "get a given image (current image if not specified)"
        self.image_changed = False
        if len(self.pil_images)<1 : return self.image_void
        if not image_num : image_num = self.current_image
        if image_num>=0 and image_num<len(self.pil_images) :
            return self.pil_images[image_num]
        else:
            return self.image_void
    def apply_transposition(self,image_num,mode):
        "apply the mode transposition to asked image or all if not image specified"
        if image_num is None:
            for image_num in range(len(self.pil_images)):
                self.pil_images[image_num] = self.pil_images[image_num].transpose(mode)
        else:
            if image_num>=0 and image_num<len(self.pil_images):
                self.pil_images[image_num] = self.pil_images[image_num].transpose(mode)
        self.image_changed = True
    def swap_x(self,image_num=None):
        "swap the image along the x axis (or all images is image_num is not given)"
        self.apply_transposition(image_num,Image.FLIP_LEFT_RIGHT )
    def swap_y(self,image_num=None):
        "swap the image along the y axis (or all images is image_num is not given)"
        self.apply_transposition(image_num,Image.FLIP_TOP_BOTTOM )
    def rotate(self,image_num=None , nbRot=1):
        "rotate the image by nbRot*90 degrees"
        mode = None
        if nbRot==1 : 
            mode = Image.ROTATE_90
        elif nbRot==2 :
            mode = Image.ROTATE_180
        elif nbRot==3 :
            mode = Image.ROTATE_270
        else :
            return
        self.apply_transposition(image_num, mode)
    def rescale_all(self):
        # first find the highest width/height
        wD=0
        hD=0
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            w=min(ww,hh)
            h=max(ww,hh)
            wD=max(wD,w)
            hD=max(hD,h)
        # then rescale any smaller page to the max
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            if ww<hh:
                self.pil_images[i] = self.pil_images[i].resize((wD, hD), Image.BICUBIC)
            else:
                self.pil_images[i] = self.pil_images[i].resize((hD, wD), Image.BICUBIC)
    def clear_all(self):
        "clear the image data"
        self.pil_images=[]
        self.image_changed = True
        self.current_file=None
        self.title=None
        self.subject=None
        self.keywords=None
    def add_image(self,img):
        "add an image to the cache"
        if img: self.pil_images.append(img)
    def save_file(self,filename,title=None,description=None,keywords=None):
        "save the image data to a PDF file"
        if len(self.pil_images)<1 : return False
        
        (fname,ext) = os.path.splitext(filename)
        ext=ext.lower()
        if ext in ['.jpg'  , '.jpeg'  ,  '.png',  '.bmp' , '.gif']:
            if len(self.pil_images)>1 :
                gui.utilities.show_message(_('Unable to save multipage document with the asked extension'))
                return False
            try:
                self.pil_images[0].save(filename)
                return True
            except Exception as E:
                logging.exception('Saving file ' + filename + ':' + str(E))
                return False
        if ext in ['.tif' , '.tiff'] :
            if len(self.pil_images)>1 :
                gui.utilities.show_message(_('Unable to save multipage tiff document for the time being'))
                return False
            try:
                self.pil_images[0].save(filename)
                return True
            except Exception as E:
                logging.exception('Saving file ' + filename + ':' + str(E))
                return False
        if ext!='.pdf' :
            gui.utilities.show_message(_('Extension unknown'))
            return False
        wD=0
        hD=0
        for i in range(len(self.pil_images)):
            (ww,hh) = self.pil_images[i].size
            w=min(ww,hh)
            h=max(ww,hh)
            wD=max(wD,w)
            hD=max(hD,h)
        try:
            doc = FPDF(unit='pt',format=(wD,hD))
            doc.SetAuthor('Generated by MALODOS')
            if title is not None : doc.SetTitle(title.encode('utf-8'))
            if description is not None : doc.SetSubject(description.encode('utf-8'))
            if keywords is not None : doc.SetKeywords(keywords.replace(',',' ').encode('utf-8'))
            list_files=[]
            for i in range(len(self.pil_images)):
                fle_tmp_tuple = tempfile.mkstemp(suffix='.png')
                fle_tmp = fle_tmp_tuple[1];
                os.close(fle_tmp_tuple[0]);
                fle_tmp=os.path.abspath(os.path.normpath(fle_tmp))
                list_files.append(fle_tmp)
                IIm=self.pil_images[i]
                (w,h) = IIm.size
                if w<h :
                    orient='P'
                else:
                    orient='L'
                IIm.save(fle_tmp)
                doc.AddPage(orient)
                doc.Image(fle_tmp, 0, 0 )
            doc.Output(filename)
            for f in list_files : os.remove(f)
            return True
        except Exception,E:
            logging.debug('Saving file ' + str(E))
            return False
    def get_content(self,newProgression=True):
        content = {}
        pd = gui.utilities.getGlobalProgressDialog(_('Character recognition'), '')
        if newProgression : pd.clear()
        n = len(self.pil_images)
        for i in range(n):
            pd.new_sub_step(1.0/n)
            page_words = algorithms.words.ocr_image(self.pil_images[i])
            content = algorithms.words.merge_words(content, page_words)
            pd.finish_current_step()
        gui.utilities.closeGlobalProgressDialog()
        #for w in content: print w
        return content
    def load_file(self,filename,page=None,do_clear=True):
        "Load a given file into memory (only the asked page if given, all the pages otherwise)"
        
        self.current_file=filename
        if do_clear : self.clear_all()
        
        try_pdf = filename.lower().endswith('.pdf')
        old_log_level = wx.Log.GetLogLevel()
        wx.Log.SetLogLevel(0)
        if wx.Image.CanRead(filename):
            nmax = wx.Image.GetImageCount(filename)
            if page:
                if page>=nmax: return
                R = [page]
            else :
                R = range(nmax)
            progressor = gui.utilities.ProgressDialog('MALODOS',_('Reading image data, please wait...'))
            for idx in R:
                try:
                    progressor.add_to_current_step(1.0/nmax)
                    wxi = wx.Image(filename,index=idx)
                    img = Image.new('RGB', (wxi.GetWidth(), wxi.GetHeight()))
                    img.fromstring(wxi.GetData())
                    self.nb_pages = nmax
                    self.add_image(img)
                    try_pdf=False
                except:
                    pass
            progressor.destroy()
        
        wx.Log.SetLogLevel(old_log_level)
        
        if not try_pdf:
            self.current_image=0
            return
        # This is executed only is try_pdf is TRUE --> loading file was not possible via wx
        progressor = gui.utilities.ProgressDialog('MALODOS',_('Reading image data, please wait...'))
        try:
            import locale
            l = locale.getdefaultlocale()
            doc = gfx.open("pdf", filename.encode(l[1]))
            #doc = gfx.open("pdf", filename)
            self.title=doc.getInfo("title")
            self.subject=doc.getInfo("subject")
            self.keywords=doc.getInfo("keywords")
            nmax = doc.pages
            if page:
                if page>=nmax: return
                R = [page]
            else :
                R = range(nmax)
            for pagenr in range(nmax):
                progressor.add_to_current_step(1.0/nmax)
                page = doc.getPage(pagenr+1)
                bm = page.asImage(page.width,page.height)
                I = Image.fromstring("RGB",(page.width,page.height),bm)
                self.nb_pages = nmax
                self.add_image(I)
            self.current_image=0
        except Exception,E:
            logging.exception("Unable to open the file " + str(filename) + " because " + str(E))
        finally:
            progressor.destroy()
