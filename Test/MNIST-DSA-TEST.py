'''Trains a simple convnet on the MNIST dataset.
Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''

from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

from scipy import stats
import numpy as np
from sklearn.neighbors.kde import KernelDensity
number_samples=101
batch_size = int(number_samples/5)
num_classes = 10
epochs = 1

# input image dimensions
img_rows, img_cols = 28, 28

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')

#normalization
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

## trim data size
start_point=10
x_train=x_train[start_point:start_point+number_samples]
y_train=y_train[start_point:start_point+number_samples]
x_test=x_test[start_point:start_point+number_samples]
y_test=y_test[start_point:start_point+number_samples]
print('--------------------')
print('trimmed x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')
##

##  model
model = Sequential()

model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adadelta(),
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))
'''
##Evaluation

score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
'''
## compute AT
total_layer_number=len(model.layers[:])
print('Totoal Layer:',total_layer_number)

get_layer_output = K.function([model.layers[0].input, K.learning_phase()],
                                  [model.layers[1].output])
AT=get_layer_output([x_train, 1])[0]
print('Train mode layer 1 output shape',AT.shape)                                  

for i in range(2,total_layer_number):
	get_layer_output = K.function([model.layers[0].input, K.learning_phase()],
                                  [model.layers[i].output])
	layer_output_from_train = get_layer_output([x_train, 1])[0]
	print('Train mode layer', i, 'output shape',layer_output_from_train.shape)
		
	neuron_number=layer_output_from_train.size/layer_output_from_train.shape[0]
	layer_output_from_train=np.reshape(layer_output_from_train,(layer_output_from_train.shape[0],int(neuron_number)))
	#print('re-shaped layer_output_from_train:',layer_output_from_train.shape)
	
	neuron_number=AT.size/AT.shape[0]
	AT=np.reshape(AT,(AT.shape[0],int(neuron_number)))
	#print('re-shaped AT:',AT.shape)
	
	
	#print('before concatenate AT shape:',AT.shape)
	AT=np.concatenate((AT,layer_output_from_train), axis=1)
	#print('after concatenate AT shape:',AT.shape)                              

print('AT shape', AT.shape)

##argmin AT(x)-AT(x_i) compute dist_a
t=np.array([])
for i in range(AT.shape[0]-1):
	t=np.append(t,np.linalg.norm(AT[i]-AT[-1]))
print('t shape',t.shape)

min_index=np.argmin(t)
print('min index',min_index,'value',t[min_index])
print('AT_a',AT[min_index])

dist_a=np.linalg.norm(AT[-1]-AT[min_index])
print('dist_a',dist_a)

