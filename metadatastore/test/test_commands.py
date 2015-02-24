from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
import uuid
import time as ttime
import mongoengine
import mongoengine.connection
from mongoengine.context_managers import switch_db
from ..api import Document as Document

from nose.tools import make_decorator
from nose.tools import assert_equal, assert_raises


from metadatastore.odm_templates import (BeamlineConfig, EventDescriptor,
                                         Event, RunStart, RunStop)
import metadatastore.commands as mdsc

db_name = str(uuid.uuid4())
dummy_db_name = str(uuid.uuid4())
blc = None


def setup():
    global blc

    # need to make 'default' connection to point to no-where, just to be safe
    mongoengine.connect(dummy_db_name)
    # connect to the db we are actually going to use
    mongoengine.connect(db_name, alias='test_db')
    blc = mdsc.insert_beamline_config({}, ttime.time())


def teardown():
    conn = mongoengine.connection.get_connection('test_db')
    conn.drop_database(db_name)
    conn.drop_database(dummy_db_name)


def context_decorator(func):
    def inner(*args, **kwargs):
        with switch_db(BeamlineConfig, 'test_db'), \
          switch_db(EventDescriptor, 'test_db'), \
          switch_db(Event, 'test_db'), \
          switch_db(RunStop, 'test_db'), \
          switch_db(RunStart, 'test_db'):
            func(*args, **kwargs)

    return make_decorator(func)(inner)


@context_decorator
def _blc_tester(config_dict):
    """Test BeamlineConfig Insert
    """
    blc = mdsc.insert_beamline_config(config_dict, ttime.time())
    doc = Document(blc) # test document creation
    repr(doc) # exercise Document.__repr__
    BeamlineConfig.objects.get(id=blc.id)
    if config_dict is None:
        config_dict = dict()
    assert_equal(config_dict, blc.config_params)
    return blc


def test_blc_insert():
    for cfd in [None, {}, {'foo': 'bar', 'baz': 5, 'biz': .05}]:
        yield _blc_tester, cfd


@context_decorator
def _ev_desc_tester(run_start, data_keys, time):
    ev_desc = mdsc.insert_event_descriptor(run_start,
                                           data_keys, time)
    Document(ev_desc) # test document creation
    ret = EventDescriptor.objects.get(id=ev_desc.id)

    for k, v in zip(['run_start',
                     'time'],
                    [run_start.to_dbref(),
                     time, ]):

        assert_equal(getattr(ret, k), v)

    for k in data_keys:
        for ik in data_keys[k]:
            assert_equal(getattr(ret.data_keys[k], ik),
                         data_keys[k][ik])

    return ev_desc


def test_ev_desc():
    bre = mdsc.insert_run_start(time=ttime.time(),
                                beamline_id='sample_beamline',
                                scan_id=42,
                                beamline_config=blc)
    Document(bre) # test document creation
    data_keys = {'some_value': {'source': 'PV:pv1',
                              'shape': [1, 2],
                              'dtype': 'array'},
                 'some_other_val': {'source': 'PV:pv2',
                              'shape': [],
                              'dtype': 'number'},
                 'data_key3': {'source': 'PV:pv1',
                              'shape': [],
                              'dtype': 'number',
                              'external': 'FS:foobar'}}
    time = ttime.time()
    yield _ev_desc_tester, bre, data_keys, time


def test_dict_key_replace_rt():
    test_d = {'a.b': 1, 'b': .5, 'c.d.e': None}
    src_in, dst_in = mdsc.__src_dst('in')
    test_d_in = mdsc.__replace_dict_keys(test_d, src_in, dst_in)
    src_out, dst_out = mdsc.__src_dst('out')
    test_d_out = mdsc.__replace_dict_keys(test_d_in, src_out, dst_out)
    assert_equal(test_d_out, test_d)


def test_src_dst_fail():
    assert_raises(ValueError, mdsc.__src_dst, 'aardvark')


@context_decorator
def _run_start_tester(time, beamline_id, scan_id):

    run_start = mdsc.insert_run_start(time, beamline_id, scan_id=scan_id,
                                      beamline_config=blc)
    Document(run_start) # test document creation
    ret = RunStart.objects.get(id=run_start.id)

    for k, v in zip(['time', 'beamline_id', 'scan_id'],
                    [time, beamline_id, scan_id]):
        assert_equal(getattr(ret, k), v)


def test_run_start():
    time = ttime.time()
    beamline_id = 'sample_beamline'
    yield _run_start_tester, time, beamline_id, 42


@context_decorator
def _run_start_with_cfg_tester(beamline_cfg, time, beamline_id, scan_id):
    run_start = mdsc.insert_run_start(time, beamline_id,
                                      beamline_config=beamline_cfg,
                                      scan_id=scan_id)
    Document(run_start) # test document creation
    ret = RunStart.objects.get(id=run_start.id)

    for k, v in zip(['time', 'beamline_id', 'scan_id', 'beamline_config'],
                    [time, beamline_id, scan_id, beamline_cfg.to_dbref()]):
        assert_equal(getattr(ret, k), v)


def test_run_start2():
    bcfg = mdsc.insert_beamline_config({'cfg1': 1}, ttime.time())
    time = ttime.time()
    beamline_id = 'sample_beamline'
    scan_id = 42
    yield _run_start_with_cfg_tester, bcfg, time, beamline_id, scan_id


@context_decorator
def _event_tester(descriptor, seq_num, data, time):
    pass


@context_decorator
def _end_run_tester(run_start, time):
    print('br:', run_start)
    end_run = mdsc.insert_run_stop(run_start, time)
    Document(end_run) # test document creation
    ret = RunStop.objects.get(id=end_run.id)
    for k, v in zip(['id', 'time', 'run_start'],
                    [end_run.id, time, run_start.to_dbref()]):
        assert_equal(getattr(ret, k), v)


def test_end_run():
    bre = mdsc.insert_run_start(time=ttime.time(),
                                beamline_id='sample_beamline', scan_id=42,
                                beamline_config=blc)
    Document(bre) # test document creation
    print('bre:', bre)
    time = ttime.time()
    yield _end_run_tester, bre, time


@context_decorator
def test_bre_custom():
    cust = {'foo': 'bar', 'baz': 42,
            'aardvark': ['ants', 3.14]}
    bre = mdsc.insert_run_start(time=ttime.time(),
                                beamline_id='sample_beamline',
                                scan_id=42,
                                beamline_config=blc,
                                custom=cust)
    Document(bre) # test document creation
    ret = RunStart.objects.get(id=bre.id)

    for k in cust:
        assert_equal(getattr(ret, k), cust[k])