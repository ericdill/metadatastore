__author__ = 'arkilic'
import time
import random
from metadataStore.dataapi.commands import *


h_id = random.randint(0, 200000)
bc_id = random.randint(0, 450000)
ev_d_id = random.randint(0, 200000)
start = time.time()
save_header(beamline_id='csx29', scan_id=h_id, tags=['arman', 123], header_versions=[0, 1, 3], header_owner='arman')
end = time.time()
print('Header insert time is ' + str((end-start)*1000) + ' ms')

start = time.time()
insert_event_descriptor(scan_id=h_id, event_type_id=1, descriptor_name='scan')
end = time.time()
print('Descriptor insert time is ' + str((end-start)*1000) + ' ms')

start = time.time()
hdr3 = save_beamline_config(scan_id=h_id, config_params={'nam1': 'val'})
end = time.time()

start = time.time()
insert_event(scan_id=h_id, descriptor_name='scan', owner='arkilic', seq_no=0, data={'motor1':12.44})
end = time.time()
print('Event insert time is ' + str((end-start)*1000) + ' ms')

print db.header.find({'tags': {'$in': ['CSX_Experiment1']}})[0]

print db.header.find({'scan_id': h_id})[0].keys()


sample_result = find(owner='arman', data=True, event_classifier={'data.motor1': 12.44})
print sample_result.keys()
print sample_result['header_0']