# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime

import qiita_db as qdb
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class ProcessingJobTest(TestCase):
    def setUp(self):
        self.tester1 = qdb.processing_job.ProcessingJob(
            "063e553b-327c-4818-ab4a-adfe58e49860")
        self.tester2 = qdb.processing_job.ProcessingJob(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d")
        self.tester3 = qdb.processing_job.ProcessingJob(
            "b72369f9-a886-4193-8d3d-f7b504168e75")
        self.tester4 = qdb.processing_job.ProcessingJob(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55")

    def test_exists(self):
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "063e553b-327c-4818-ab4a-adfe58e49860"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "bcc7ebcd-39c1-43e4-af2d-822e3589f14d"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "b72369f9-a886-4193-8d3d-f7b504168e75"))
        self.assertTrue(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-a12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "d19f76ee-274e-4c1b-b3a2-b12d73507c55"))
        self.assertFalse(qdb.processing_job.ProcessingJob.exists(
            "some-other-string"))

    def test_create(self):
        exp_command = qdb.software.Command(1)
        json_str = (
            '{"input_data": 1, "max_barcode_errors": 1.5, '
            '"barcode_type": "golay_12", "max_bad_run_length": 3, '
            '"rev_comp": false, "phred_quality_threshold": 3, '
            '"rev_comp_barcode": false, "rev_comp_mapping_barcodes": false, '
            '"min_per_read_length_fraction": 0.75, "sequence_max_n": 0}')
        exp_params = qdb.software.Parameters.load(exp_command,
                                                  json_str=json_str)
        exp_user = qdb.user.User('test@foo.bar')
        obs = qdb.processing_job.ProcessingJob.create(exp_user, exp_params)
        self.assertEqual(obs.user, exp_user)
        self.assertEqual(obs.command, exp_command)
        self.assertEqual(obs.parameters, exp_params)
        self.assertEqual(obs.status, 'queued')
        self.assertEqual(obs.log, None)
        self.assertEqual(obs.heartbeat, None)
        self.assertEqual(obs.step, None)
        self.assertTrue(obs in qdb.artifact.Artifact(1).jobs())

    def test_user(self):
        exp_user = qdb.user.User('test@foo.bar')
        self.assertEqual(self.tester1.user, exp_user)
        self.assertEqual(self.tester2.user, exp_user)
        exp_user = qdb.user.User('shared@foo.bar')
        self.assertEqual(self.tester3.user, exp_user)
        self.assertEqual(self.tester4.user, exp_user)

    def test_command(self):
        cmd1 = qdb.software.Command(1)
        cmd2 = qdb.software.Command(2)
        cmd3 = qdb.software.Command(3)
        self.assertEqual(self.tester1.command, cmd1)
        self.assertEqual(self.tester2.command, cmd2)
        self.assertEqual(self.tester3.command, cmd1)
        self.assertEqual(self.tester4.command, cmd3)

    def test_parameters(self):
        json_str = (
            '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,'
            '"sequence_max_n":0,"rev_comp_barcode":false,'
            '"rev_comp_mapping_barcodes":false,"rev_comp":false,'
            '"phred_quality_threshold":3,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(1),
                                                  json_str=json_str)
        self.assertEqual(self.tester1.parameters, exp_params)

        json_str = (
            '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,'
            '"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,'
            '"max_primer_mismatch":0,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"disable_bc_correction":false,'
            '"qual_score_window":0,"disable_primers":false,'
            '"reverse_primers":"disable","reverse_primer_mismatches":0,'
            '"truncate_ambi_bases":false,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(2),
                                                  json_str=json_str)
        self.assertEqual(self.tester2.parameters, exp_params)

        json_str = (
            '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,'
            '"sequence_max_n":0,"rev_comp_barcode":false,'
            '"rev_comp_mapping_barcodes":true,"rev_comp":false,'
            '"phred_quality_threshold":3,"barcode_type":"golay_12",'
            '"max_barcode_errors":1.5,"input_data":1}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(1),
                                                  json_str=json_str)
        self.assertEqual(self.tester3.parameters, exp_params)

        json_str = (
            '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,'
            '"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,'
            '"input_data":2}')
        exp_params = qdb.software.Parameters.load(qdb.software.Command(3),
                                                  json_str=json_str)
        self.assertEqual(self.tester4.parameters, exp_params)

    def test_input_artifacts(self):
        exp = [qdb.artifact.Artifact(1)]
        self.assertEqual(self.tester1.input_artifacts, exp)
        self.assertEqual(self.tester2.input_artifacts, exp)
        self.assertEqual(self.tester3.input_artifacts, exp)
        exp = [qdb.artifact.Artifact(2)]
        self.assertEqual(self.tester4.input_artifacts, exp)

    def test_status(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.assertEqual(self.tester2.status, 'running')
        self.assertEqual(self.tester3.status, 'success')
        self.assertEqual(self.tester4.status, 'error')

    def test_status_setter(self):
        self.assertEqual(self.tester1.status, 'queued')
        self.tester1.status = 'running'
        self.assertEqual(self.tester1.status, 'running')
        self.tester1.status = 'error'
        self.assertEqual(self.tester1.status, 'error')
        self.tester1.status = 'running'
        self.assertEqual(self.tester1.status, 'running')
        self.tester1.status = 'success'
        self.assertEqual(self.tester1.status, 'success')

    def test_status_setter_error(self):
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester2.status = 'queued'

        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.tester3.status = 'running'

    def test_log(self):
        self.assertIsNone(self.tester1.log)
        self.assertIsNone(self.tester2.log)
        self.assertIsNone(self.tester3.log)
        self.assertEqual(self.tester4.log, qdb.logger.LogEntry(1))

    def test_log_setter(self):
        self.tester2.status = 'error'
        exp = qdb.logger.LogEntry(1)
        self.tester2.log = exp
        self.assertEqual(self.tester2.log, exp)

    def test_log_setter_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester2.log = qdb.logger.LogEntry(1)

    def test_heartbeat(self):
        self.assertIsNone(self.tester1.heartbeat)
        self.assertEqual(self.tester2.heartbeat,
                         datetime(2015, 11, 22, 21, 00, 00))
        self.assertEqual(self.tester3.heartbeat,
                         datetime(2015, 11, 22, 21, 15, 00))
        self.assertEqual(self.tester4.heartbeat,
                         datetime(2015, 11, 22, 21, 30, 00))

    def test_heartbeat_setter(self):
        self.assertEqual(self.tester2.heartbeat,
                         datetime(2015, 11, 22, 21, 00, 00))
        exp = datetime(2015, 11, 22, 21, 00, 10)
        self.tester2.heartbeat = exp
        self.assertEqual(self.tester2.heartbeat, exp)

    def test_step(self):
        self.assertIsNone(self.tester1.step)
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.assertIsNone(self.tester3.step)
        self.assertEqual(self.tester4.step, 'generating demux file')

    def test_step_setter(self):
        self.assertEqual(self.tester2.step, 'demultiplexing')
        self.tester2.step = 'generating demux file'
        self.assertEqual(self.tester2.step, 'generating demux file')

    def test_step_setter_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester1.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester3.step = 'demultiplexing'

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.tester4.step = 'demultiplexing'

if __name__ == '__main__':
    main()
