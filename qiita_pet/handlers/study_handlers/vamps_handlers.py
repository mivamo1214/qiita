# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError
from qiita_files.demux import stats as demux_stats

<<<<<<< HEAD
from qiita_ware.context import submit
from qiita_ware.demux import stats as demux_stats
from qiita_ware.dispatchable import submit_to_VAMPS
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.study import Study
=======
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.artifact import Artifact
from qiita_db.software import Software, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction


class VAMPSHandler(BaseHandler):
    @execute_as_transaction
    def display_template(self, preprocessed_data_id, msg, msg_level):
        """Simple function to avoid duplication of code"""
        preprocessed_data_id = int(preprocessed_data_id)
        try:
            preprocessed_data = Artifact(preprocessed_data_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, reason="Artifact %d does not exist!" %
                            preprocessed_data_id)
        else:
            user = self.current_user
            if user.level != 'admin':
<<<<<<< HEAD
                raise HTTPError(403, "No permissions of admin, "
                                     "get/VAMPSSubmitHandler: %s!" % user.id)

        prep_template = PrepTemplate(preprocessed_data.prep_template)
        sample_template = SampleTemplate(preprocessed_data.study)
        study = Study(preprocessed_data.study)
=======
                raise HTTPError(403, reason="No permissions of admin, "
                                "get/VAMPSSubmitHandler: %s!" % user.id)
        prep_templates = preprocessed_data.prep_templates
        allow_submission = len(prep_templates) == 1
        msg_list = ["Submission to EBI disabled:"]
        if not allow_submission:
            msg_list.append(
                "Only artifacts with a single prep template can be submitted")
        # If allow_submission is already false, we technically don't need to
        # do the following work. However, there is no clean way to fix this
        # using the current structure, so we perform the work as we
        # did so it doesn't fail.
        # We currently support only one prep template for submission, so
        # grabbing the first one
        prep_template = prep_templates[0]
        study = preprocessed_data.study
        sample_template = study.sample_template
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
        stats = [('Number of samples', len(prep_template)),
                 ('Number of metadata headers',
                  len(sample_template.categories()))]

        demux = [path for _, path, ftype in preprocessed_data.get_filepaths()
                 if ftype == 'preprocessed_demux']
        demux_length = len(demux)

        if not demux_length:
            msg = ("Study does not appear to have demultiplexed "
                   "sequences associated")
            msg_level = 'danger'
        elif demux_length > 1:
            msg = ("Study appears to have multiple demultiplexed files!")
            msg_level = 'danger'
        elif demux_length == 1:
            demux_file = demux[0]
            demux_file_stats = demux_stats(demux_file)
            stats.append(('Number of sequences', demux_file_stats.n))
            msg_level = 'success'

        self.render('vamps_submission.html',
                    study_title=study.title, stats=stats, message=msg,
                    study_id=study.id, level=msg_level,
                    preprocessed_data_id=preprocessed_data_id)

    @authenticated
    def get(self, preprocessed_data_id):
        self.display_template(preprocessed_data_id, "", "")

    @authenticated
    @execute_as_transaction
    def post(self, preprocessed_data_id):
        # make sure user is admin and can therefore actually submit to VAMPS
<<<<<<< HEAD
        if self.current_user.level != 'admin':
            raise HTTPError(403, "User %s cannot submit to VAMPS!" %
                            self.current_user.id)
        msg = ''
        msg_level = 'success'
        preprocessed_data = Artifact(preprocessed_data_id)
        state = preprocessed_data.submitted_to_vamps_status()

        demux = [path for _, path, ftype in preprocessed_data.get_filepaths()
                 if ftype == 'preprocessed_demux']
        demux_length = len(demux)

        if state in ('submitting',  'success'):
            msg = "Cannot resubmit! Current state is: %s" % state
            msg_level = 'danger'
        elif demux_length != 1:
            msg = "The study doesn't have demux files or have too many" % state
            msg_level = 'danger'
        else:
            channel = self.current_user.id
            job_id = submit(channel, submit_to_VAMPS,
                            int(preprocessed_data_id))

            self.render('compute_wait.html',
                        job_id=job_id, title='VAMPS Submission',
                        completion_redirect='/compute_complete/%s' % job_id)
            return
=======
        if user.level != 'admin':
            raise HTTPError(403, reason="User %s cannot submit to VAMPS!" %
                            user.id)
        msg = ''
        msg_level = 'success'

        plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = plugin.get_command('submit_to_VAMPS')
        artifact = Artifact(preprocessed_data_id)

        # Check if the artifact is already being submitted to VAMPS
        is_being_submitted = any(
            [j.status in ('queued', 'running')
             for j in artifact.jobs(cmd=cmd)])
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed

        if is_being_submitted == 'submitting':
            msg = "Cannot resubmit! Data is already being submitted"
            msg_level = 'danger'
            self.display_template(preprocessed_data_id, msg, msg_level)
        else:
            params = Parameters.load(
                cmd, values_dict={'artifact': preprocessed_data_id})
            job = ProcessingJob.create(user, params, True)
            job.submit()
            self.redirect('/study/description/%s' % artifact.study.study_id)
