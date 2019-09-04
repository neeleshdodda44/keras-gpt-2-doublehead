from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import BaseLogger, History
import tensorflow as tf
import numpy as np
from collections import defaultdict
import os
from keras_gpt_2 import load_trained_model_from_checkpoint, get_bpe_from_files, generate
import requests
import gpt_2_simple as gpt_2

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

filenames = ['input_ids.json', 'lm_labels.json', 'mc_labels.json', 'mc_token_ids.json']

url = "https://persona-dataset.s3.amazonaws.com/{}"

data = []

for name in filenames:
    full_url = url.format(name)
    json_data = requests.get(full_url).json()
    data.append(np.array(json_data))
    print("Done")

input_ids, lm_labels, mc_labels, mc_token_ids = data

if not os.path.isdir(model_folder):
    gpt2.download_gpt2(model_name = '117M')

strategy = tf.distribute.MirroredStrategy()

print('Number of devices: {}'.format(strategy.num_replicas_in_sync))

with strategy.scope():
    model = load_trained_model_from_checkpoint(config_path, checkpoint_path)
    history_output = model.fit(
    {
        'LMInput': input_ids,
        'MCInput': mc_token_ids
    },
    {
        'LMOutput': lm_labels,
        'MCOutput': mc_labels
    },
    batch_size=8,
    epochs=10,
    callbacks=[BaseLogger()]
)