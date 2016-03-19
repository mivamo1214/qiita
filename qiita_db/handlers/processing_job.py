# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_job(job_id):
    """Returns the job with the given id if it exists

    Parameters
    ----------
    job_id : str
        The job id to check

    Returns
    -------
    qiita_db.processing_job.ProcessingJob, bool, string
        The requested job or None
        Whether if we could get the job or not
        Error message in case we couldn't get the job
    """
    if not qdb.processing_job.ProcessingJob.exists(job_id):
        return None, False, 'Job does not exist'

    try:
        job = qdb.processing_job.ProcessingJob(job_id)
    except qdb.exceptions.QiitaDBError as e:
        return None, False, 'Error instantiating the job: %s' % str(e)

    return job, True, ''


class JobHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, job_id):
        """Get the job information

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str,
             'command': str,
             'parameters': dict of {str, obj},
             'status': str}

             - success: whether the request is successful or not
             - error: in case that success is false, it contains the error msg
             - command: the name of the command that the job executes
             - parameters: the parameters of the command, keyed by parameter
             name
             - status: the status of the job
        """
        with qdb.sql_connection.TRN:
            job, success, error_msg = _get_job(job_id)
            cmd = None
            params = None
            status = None
            if success:
                cmd = job.command.name
                params = job.parameters.values
                status = job.status

        response = {'success': success, 'error': error_msg,
                    'command': cmd, 'parameters': params,
                    'status': status}
        self.write(response)


class HeartbeatHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Update the heartbeat timestamp of the job

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str}
            - success: whether the heartbeat was successful
            - error: in case that success is false, it contains the error msg
        """
        with qdb.sql_connection.TRN:
            job, success, error_msg = _get_job(job_id)
            if success:
                try:
                    job.update_heartbeat_state()
                except qdb.exceptions.QiitaDBOperationNotPermittedError as e:
                    success = False
                    error_msg = str(e)

        response = {'success': success, 'error': error_msg}
        self.write(response)


class ActiveStepHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Changes the current exectuion step of the given job

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str}
            - success: whether the job's step was successfully updated
            - error: in case that success is false, it contains the error msg
        """
        with qdb.sql_connection.TRN:
            job, success, error_msg = _get_job(job_id)
            if success:
                job_status = job.status
                if job_status != 'running':
                    success = False
                    error_msg = 'Job in a non-running state'
                else:
                    payload = loads(self.request.body)
                    step = payload['step']
                    job.step = step

        response = {'success': success, 'error': error_msg}
        self.write(response)


class CompleteHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self, job_id):
        """Updates the job to one of the completed statuses: 'success', 'error'

        Parameters
        ----------
        job_id : str
            The job to complete

        Returns
        -------
        dict
            Format:
            {'success': bool,
             'error': str}
            - success: whether the job information was successfuly updated
            - error: in case that success is false, it contains the error msg
        """
        with qdb.sql_connection.TRN:
            job, success, error_msg = _get_job(job_id)
            if success:
                payload = loads(self.request.body)
                payload_success = payload['success']
                if payload_success:
                    artifacts = payload['artifacts']
                    error = None
                else:
                    artifacts = None
                    error = payload['error']
                try:
                    job.complete(payload_success, artifacts, error)
                except qdb.exceptions.QiitaDBOperationNotPermittedError as e:
                    success = False
                    error_msg = str(e)

        response = {'success': success, 'error': error_msg}
        self.write(response)
