import random
import numpy as np
import os
import torch
from torch.utils.data import Dataset
import glob
import imageio
import cv2
def define_weights(num):
    weights = np.float32((np.logspace(0,num,127, endpoint=True, base=10.0)))
    weights = weights/np.max(weights)
    weights = np.flipud(weights).copy()    
    return weights

def get_na(bins,weights,img_loww,amp=1.0):
    H,W = img_loww.shape
    arr = img_loww*1
    selection_dict = {weights[0]: (bins[0]<=arr)&(arr<bins[1])}
    for ii in range(1,len(weights)):
        selection_dict[weights[ii]] = (bins[ii]<=arr)&(arr<bins[ii+1])
    mask = np.select(condlist=selection_dict.values(), choicelist=selection_dict.keys())
   
    mask_sum1 = np.sum(mask,dtype=np.float64)
    
    na1 = np.float32(np.float64(mask_sum1*0.01*amp)/np.sum(img_loww*mask,dtype=np.float64))

    if na1>300.0:
        na1 = np.float32(300.0)
    if na1<1.0:
        na1 = np.float32(1.0)
    
    selection_dict.clear()

    return na1


def part_init(train_files):

    # bins = np.float32((np.logspace(0,8,128, endpoint=True, base=2.0)-1))/255.0
    # weights5 = define_weights(5)
    train_list = []
    
    for i in range(len(train_files)):
        
        # raw = rawpy.imread(train_files[i])
        # img = raw.raw_image_visible.astype(np.float32).copy()
        # raw.close()
        img = cv2.imread(train_files[i])[:,:,::-1] / 255.0
        img = img.astype(np.float32).copy()

        h,w = img.shape[:1]
        if h%32!=0:
            # print('Image dimensions should be multiple of 32. Correcting the 1st dimension.')
            h = (h//32)*32
            img = img[:h,:]
        
        if w%32!=0:
            # print('Image dimensions should be multiple of 32. Correcting the 2nd dimension.')
            w = (w//32)*32
            img = img[:,:w]        
        
        # img_loww = (np.maximum(img - 512,0)/ (16383 - 512))       
        
        # na5 = get_na(bins,weights5,img_loww)   
        
        # img_loww = img_loww*na5
            
        train_list.append(img)

        # print('Image No.: {}, Amplification_m=1: {}'.format(i+1,na5))
    return train_list
    
def read_one_im(p):
  img = cv2.imread(p)
  assert img is not None, p
#   img = cv2.resize(img, (960, 960), interpolation = cv2.INTER_AREA)
  img = img[:,:,::-1] / 255.0
  img = img.astype(np.float32).copy()

  h,w = img.shape[:-1]
  if h%32!=0:
      # print('Image dimensions should be multiple of 32. Correcting the 1st dimension.')
      h = (h//32)*32
      img = img[:h,:]
  
  if w%32!=0:
      # print('Image dimensions should be multiple of 32. Correcting the 2nd dimension.')
      w = (w//32)*32
      img = img[:,:w] 
  return img
################ DATASET CLASS
class load_data(Dataset):
    """Loads the Data."""
    
    def __init__(self, train_files, gts, return_path=False):    
        print('\n...... Loading all files to CPU RAM\n')
        self.train_list = train_files
        self.gts = gts
        self.return_path = return_path
        # self.train_list = part_init(train_files)        
        print('\nFiles loaded to CPU RAM......\n')
        
    def __len__(self):
        return len(self.train_list)

    def __getitem__(self, idx):    
        img_low = read_one_im(self.train_list[idx])
        img_low = torch.from_numpy(img_low).float().permute(2,0,1)
        gt = read_one_im(self.gts[idx])
        gt = torch.from_numpy(gt).float().permute(2,0,1)
        # print('item', img_low.shape, gt.shape)
        if self.return_path:
            return img_low, gt, self.train_list[idx]
        return img_low, gt

def run_test(model, dataloader_test, save_images):    
    with torch.no_grad():
        model.eval()
        for image_num, low in enumerate(dataloader_test):
            p = low[-1][0]
            low = low[0].to(next(model.parameters()).device)            
            # for amp in [1.0,5.0,8.0]:
            pred = model(low)
            pred = (np.clip(pred[0].detach().cpu().numpy().transpose(1,2,0),0,1)*255).astype(np.uint8)
            p = p.replace('/home/ubuntu/dataset/sice_paired_small/', 'demo_restored_images/')
            if not os.path.exists(os.path.split(p)[0]):
                os.makedirs(os.path.split(p)[0])
            imageio.imwrite(p, pred)
            # break
    return
    
    

        
