import os
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import BaseLogger, History
import tensorflow as tf
import numpy as np
from collections import defaultdict
from keras_gpt_2 import load_trained_model_from_checkpoint, get_bpe_from_files, generate
import requests
import gpt_2_simple as gpt2
from keras_gpt_2 import Metrics

from tensorflow.python.client import device_lib
def get_available_devices():
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos]
print(get_available_devices()) 

model_folder = 'models/117M'
config_path = os.path.join(model_folder, 'hparams.json')
checkpoint_path = os.path.join(model_folder, 'model.ckpt')
encoder_path = os.path.join(model_folder, 'encoder.json')
vocab_path = os.path.join(model_folder, 'vocab.bpe')
checkpoint_dir = './training_checkpoints'
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")
filenames = ['input_ids.json', 'lm_labels.json', 'mc_labels.json', 'mc_token_ids.json']

url = "https://persona-dataset.s3.amazonaws.com/{}"

data = []

for name in filenames:
    full_url = url.format(name)
    json_data = requests.get(full_url).json()
    data.append(np.array(json_data))
    print("Done")

input_ids, lm_labels, mc_labels, mc_token_ids = data
input_ids = input_ids[:6]
lm_labels = lm_labels[:6]
mc_labels = mc_labels[:6]
mc_token_ids = mc_token_ids[:6]

print(lm_labels.shape)
print(input_ids.shape)

print(mc_token_ids.shape)
print(mc_labels.shape)

if not os.path.isdir(model_folder):
    gpt2.download_gpt2(model_name = '117M')

batch_size=2
model = load_trained_model_from_checkpoint(config_path, checkpoint_path, batch_size=batch_size)
print("starting fit")
history_output = model.fit(
    {
        'LMInput': input_ids,
        'MCInput': mc_token_ids
    },
    {
        'LMOutput': lm_labels,
        'MCOutput': mc_labels
    },
    batch_size=batch_size,
    epochs=3,
    callbacks=[Metrics(input_ids, lm_labels, mc_token_ids, mc_labels),
        tf.keras.callbacks.TensorBoard(log_dir='./logs'),
        tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_prefix,
                                    save_weights_only=True)]
)
import json

with open('training_history.json', 'w') as f:
    json.dump(history_output.history, f)
    
# def gather(params, indices):
#     indices_dims = [1, 278, 1, 768]
#     params_dims = [1, 278, 768]
#     indices = K.squeeze(indices, -2)

#     aa = tf.Variable(tf.zeros((params_dims)))
#     for i in range(params_dims[0]):
#         for j in range(params_dims[1]):
#             for k in range(params_dims[2]):
#                 aa = aa[i, j, k].assign(params[i, indices[i, j, k], k])
#     return aa


# import tensorflow as tf
# from tensorflow.keras import backend as K

# a = tf.ones((1, 278, 768))
# b = tf.zeros((1, 278, 1, 768))

# c = gather(a, b)

# print(c.shape)