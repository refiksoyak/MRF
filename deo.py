# -*- coding: utf-8 -*-
"""deo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1hYkAGFUw-nS2yo7lDLYZ95l_L5D-uVmU
"""

#First import libraries
import numpy as np 
import h5py as h5
import scipy.io as sio
import time
import os
import skimage.io as io
import skimage.transform as trans
import math
from sklearn.feature_extraction import image
import warnings
from skimage.util.shape import view_as_windows, view_as_blocks
from keras.models import load_model
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error

class StopExecution(Exception):
  def _render_traceback_(self):
    pass

class operations():

  def read_data(read_for, fold_number, signal_length = 2000, skip_size = 1): 
    #Here you have to choose one fold to load its data. 
    #Available data names: kl, tk, ir, ab, abd
    #In this project only kl, abd and ir subjest are used
    #read data. filepath is known, so input is just name of data
    #working with 2 data at the same time, so just load and return them
    #read_for: to return train data or test data. use read_for = 'train' or 'test'
    #signal_length: specifies length of signal, default = 2000
    #skip_size: specifies how many time point will be skipped. E.g: if skip_size =2, time points will get as 0,2,4,6.. so on

    if fold_number == 1:
      test1 = 'kl' 
      train1 = 'abd'
      train2 = 'ir'

    elif fold_number == 2:
      test1 = 'abd' 
      train1 = 'kl'
      train2 = 'ir'

    elif fold_number == 3:
      test1 = 'ir'
      train1 = 'abd'
      train2 = 'kl'

    filepath = '/content/drive/My Drive/KCL internship/Data/50_gb/'
    filepath2 = '/content/drive/My Drive/KCL internship/Data/50_gb/transposed_trials/transposed_trials_1/'

    if read_for == 'train': #for train data, 2 data will be returned

      f1 = sio.loadmat(filepath + train1 + '_t1_t2_ground_truths.mat')
      T1_ab = f1['T1_LRI']
      T2_ab = f1['T2_LRI']
      trial1_ab_signal = h5.File(filepath2 + train1 + '_trial1_transposed_1.mat','r')
      signal_ab = trial1_ab_signal['Noisy_tps'] #Complex | matlab([a,b,c,d]) python([d,c,b,a])
      signal_ab = signal_ab[:, :, 0:signal_length:skip_size]

      f2 = sio.loadmat(filepath + train2 + '_t1_t2_ground_truths.mat')
      T1_tk = f2['T1_LRI']
      T2_tk = f2['T2_LRI']
      trial1_tk_signal = h5.File(filepath2 + train2 + '_trial1_transposed_1.mat','r')
      signal_tk = trial1_tk_signal['Noisy_tps'] #Complex | matlab([a,b,c,d]) python([d,c,b,a])
      signal_tk = signal_tk[:, :, 0:signal_length:skip_size]

      return signal_ab, T1_ab, T2_ab, signal_tk, T1_tk, T2_tk

    elif read_for == 'test': #for test data, only 1 data will be return 

      f1 = sio.loadmat(filepath + test1 + '_t1_t2_ground_truths.mat')
      T1_ab = f1['T1_LRI']
      T2_ab = f1['T2_LRI']
      trial1_ab_signal = h5.File(filepath2 + test1 + '_trial1_transposed_1.mat','r')
      signal_ab = trial1_ab_signal['Noisy_tps'] #Complex | matlab([a,b,c,d]) python([d,c,b,a])
      signal_ab = signal_ab[:, :, 0:signal_length:skip_size]

      return signal_ab, T1_ab, T2_ab

    print(read_for + 'data is OK')
    print('Signal shape:' + signal_ab.shape)
    print('T1 shape:' + T1_ab.shape)
    print('T2 shape:' + T2_ab.shape)

  def handle_complexity(signal, out_type = 'magnitude'):
    #type: 'magnitude' or 'real&im' (split into channels) 
    real=[]
    real=signal['real']
    im=[]
    im=signal['imag']

    if out_type == 'magnitude':
      
      mag = []
      mag = np.square(real**2+im**2)
      return mag

    elif out_type == 'real&im':
      real_im = np.array([real,im])
      return real_im
    
    print(out_type + 'is OK')

  
  def patch_extracter(signal, patch_size, get_center = False):

    if len(signal.shape) == 2: #this means data is 2D
      patches = image.extract_patches_2d(signal, (patch_size, patch_size))

    elif len(signal.shape) == 3: #this means data is 3D

      patches = []
      for i in range(signal.shape[2]):
        c_signal = signal[:,:,i]
        patches.append(image.extract_patches_2d(c_signal, (patch_size, patch_size)))

    if get_center == True:
  
      if patch_size % 2 == 0: #patch size is even like 4,6,8...
        center_point = 0
        warnings.warn("Patch size is not odd! Center point is 0,0 pixel of the patch.")

      elif patch_size % 2 == 1: #patch size is odd like 3,5,7
        center_point = patch_size // 2 + 1

      patch_centers = []
      for k in range(len(patches)):
        patch_centers.append(patches[i, center_point, center_point])
      
      return np.array(patches), np.array(patch_centers)

    return patches

  def block_extracter(signal, block_size = 16):

    if len(signal.shape) == 2: #this means data is 2D
      blocks = view_as_blocks(signal, ((block_size, block_size)))
      blocks = np.array(blocks).reshape(-1, block_size, block_size)

    elif len(signal.shape) == 3: #this means data is 3D
      blocks = view_as_blocks(signal, ((block_size, block_size, 1)))
      blocks = np.array(blocks).reshape(-1, block_size, block_size, signal.shape[2])
    
    return blocks

  def crop_image(signal):
    signal = (signal[55:275,60:260]).astype('float32')
    return signal
  
  def normalize(signal):
    signal_normed = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
    return signal_normed
  
  def denormalize(signal_normed, original_signal):
    signal_denormed = signal_normed*(np.max(original_signal) - np.min(original_signal)) + np.min(original_signal)
    return signal_denormed

  def attention_channel_analyzing(attention_score, channel_length, true_image, input_shape, pixel=None, patch=None, patch_size=None):
    """Function for channel attention analysis.

      Args:
          attention_score: Score that got from model. Shape must be: (-1, channel_length).
          true_image: The part of image, which is analyzing, will be marked.
          input_shape (str): "patch" or "pixel".
          pixel ('tuple', optional): Pixel index that will be analyzing. 
                                    Input example: pixel=(5,5) 
          patch (int, optional): Patch index that will be analyzing. 
          patch_size(int, optional): Patch size of patch input.

    """
    #Visualize region and its channel attention analysis
    fig=plt.figure(figsize=(20, 7))
    fig.suptitle("Channel Attention Analysis", fontsize=20, fontweight='bold')
    

    if input_shape == 'pixel' and pixel is not None:

      """
      attention_score = attention_score.reshape(-1, channel_length)
      attn_score_channel_values = attention_score[pixel, pixel, :]
      """
      im_row = pixel[0]
      im_col = pixel[1]

      true_image_pix_remarked = np.copy(true_image)
      true_image_pix_remarked[im_col, im_row] = np.max(true_image)*3
      
      plt.subplot(1, 2, 1)
      plt.imshow(true_image_pix_remarked, vmin=0, vmax=np.max(true_image), cmap='hot')
      plt.axis('off')
      plt.annotate("", xy=(im_row-1, im_col-1), xytext=(im_row-15, im_col-15),
                arrowprops=dict(width = 5.,
                                headwidth = 15.,
                                headlength = 5,
                                shrink = 0.05,
                                linewidth = 2, color = 'cyan'))
      plt.subplot(1,2,2)
      plt.plot(attention_score[im_row*im_col])
      plt.title("["+str(im_row)+","+str(im_col)+"]" + " pixels' attention scores for each channel")
      
      plt.show()
      
    elif input_shape == 'patch' and patch is not None and patch_size is not None:
      
      max_patch_for_a_row = (200-(patch_size - 1))
      patch_row = patch//max_patch_for_a_row
      patch_col = patch%(max_patch_for_a_row)
      #print("patch_row:"+ str(patch_row)+ " patch_col:"+ str(patch_col))

      plt.subplot(1, 2, 1)
      plt.imshow(true_image, vmin=0, vmax=np.max(true_image), cmap='hot')
      rectangle = plt.Rectangle((patch_col, patch_row), patch_size, patch_size, linewidth=3, edgecolor='w', facecolor='none')
      plt.gca().add_patch(rectangle)
      plt.colorbar()

      plt.subplot(1, 2, 2)
      plt.plot(attention_score[patch])
      plt.axis('off')
      plt.title(str(patch)+"th patch attention scores for each channel")
      
    
    else:
      print("Error: Check input type and required index: pixel or patch (and patch size)")
