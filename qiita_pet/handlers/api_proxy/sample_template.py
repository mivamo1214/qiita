# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import loads, dumps

from natsort import natsorted
from moi import r_client

from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_core.util import execute_as_transaction
from qiita_db.metadata_template.util import looks_like_qiime_mapping_file
from qiita_db.exceptions import QiitaDBColumnError
from qiita_db.user import User
from qiita_ware.dispatchable import (
    create_sample_template, update_sample_template, delete_sample_template)
from qiita_ware.context import safe_submit
from qiita_pet.handlers.api_proxy.util import check_access, check_fp

SAMPLE_TEMPLATE_KEY_FORMAT = 'sample_template_%s'


def _check_sample_template_exists(samp_id):
    """Make sure a sample template exists in the system

    Parameters
    ----------
    samp_id : int or str castable to int
        SampleTemplate id to check

    Returns
    -------
    dict
        {'status': status,
         'message': msg}
    """
    if not SampleTemplate.exists(int(samp_id)):
        return {'status': 'error',
                'message': 'Sample template %d does not exist' % int(samp_id)
                }
    return {'status': 'success',
            'message': ''}


def sample_template_get_req(samp_id, user_id):
    """Gets the json of the full sample template

    Parameters
    ----------
    samp_id : int or int castable string
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict of objects
        {'status': status,
         'message': msg,
         'template': dict of {str: {str: object, ...}, ...}

        template is dictionary where the keys access_error the metadata samples
        and the values are a dictionary of column and value.
        Format {sample: {column: value, ...}, ...}
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(int(samp_id), user_id)
    if access_error:
        return access_error

    template = SampleTemplate(int(samp_id))
    access_error = check_access(template.study_id, user_id)
    if access_error:
        return access_error
    df = template.to_dataframe()
    return {'status': 'success',
            'message': '',
            'template': df.to_dict(orient='index')}


def sample_template_samples_get_req(samp_id, user_id):
    """Returns list of samples in the sample template

    Parameters
    ----------
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns summary information in the form
        {'status': str,
         'message': str,
         'samples': list of str}
         samples is list of samples in the template
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    return {'status': 'success',
            'message': '',
            'samples': sorted(x for x in SampleTemplate(int(samp_id)))
            }


def sample_template_meta_cats_get_req(samp_id, user_id):
    """Returns list of metadata categories in the sample template

    Parameters
    ----------
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns information in the form
        {'status': str,
         'message': str,
         'categories': list of str}
         samples is list of metadata categories in the template
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    return {'status': 'success',
            'message': '',
            'categories': sorted(SampleTemplate(int(samp_id)).categories())
            }


def sample_template_category_get_req(category, samp_id, user_id):
    """Returns dict of values for each sample in the given category

    Parameters
    ----------
    category : str
        Metadata category to get values for
    samp_id : int or str typecastable to int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns information in the form
        {'status': str,
         'message': str,
         'values': dict of {str: object}}
    """
    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    st = SampleTemplate(int(samp_id))
    try:
        values = st.get_category(category)
    except QiitaDBColumnError:
        return {'status': 'error',
                'message': 'Category %s does not exist in sample template' %
                category}
    return {'status': 'success',
            'message': '',
            'values': values}


def sample_template_summary_get_req(samp_id, user_id):
    """Returns a summary of the sample template metadata columns

    Parameters
    ----------
    samp_id : int
        SampleTemplate id to get info for
    user_id : str
        User requesting the sample template info

    Returns
    -------
    dict
        Returns summary information in the form
        {'status': str,
         'message': str,
         'info': dict of {str: object}
        status can be success, warning, or error depending on result
        message has the warnings or errors
        info dictionary contains the keys as the metadata categories
        and the values are list of tuples. Each tuple is an observed value in
        the category and the number of times its seen.
        Format {num_samples: value,
                category: [(val1, count1), (val2, count2), ...], ...}
    """
    access_error = check_access(samp_id, user_id)
    if access_error:
        return access_error

    job_info = r_client.get(SAMPLE_TEMPLATE_KEY_FORMAT % samp_id)
    if job_info:
        job_info = loads(job_info)
        job_id = job_info['job_id']
        if job_id:
            redis_info = loads(r_client.get(job_id))
            processing = redis_info['status_msg'] == 'Running'
            if processing:
                alert_type = 'info'
                alert_msg = 'This sample template is currently being processed'
            elif redis_info['status_msg'] == 'Success':
                alert_type = redis_info['return']['status']
                alert_msg = redis_info['return']['message'].replace('\n',
                                                                    '</br>')
                payload = {'job_id': None,
                           'status': alert_type,
                           'message': alert_msg}
                r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % samp_id,
                             dumps(payload))
            else:
                alert_type = redis_info['return']['status']
                alert_msg = redis_info['return']['message'].replace('\n',
                                                                    '</br>')
        else:
            processing = False
            alert_type = job_info['status']
            alert_msg = job_info['message'].replace('\n', '</br>')
    else:
        processing = False
        alert_type = ''
        alert_msg = ''

    exists = _check_sample_template_exists(int(samp_id))
    if exists['status'] != 'success':
        return {'status': 'success',
                'message': '',
                'num_samples': 0,
                'num_columns': 0,
                'editable': not processing,
                'alert_type': alert_type,
                'alert_message': alert_msg,
                'stats': {}}

    template = SampleTemplate(int(samp_id))

    df = template.to_dataframe()

    editable = (Study(template.study_id).can_edit(User(user_id)) and not
                processing)

    out = {'status': 'success',
           'message': '',
           'num_samples': df.shape[0],
           'num_columns': df.shape[1],
           'editable': editable,
           'alert_type': alert_type,
           'alert_message': alert_msg,
           'stats': {}}

    # drop the samp_id column if it exists
    if 'study_id' in df.columns:
        df.drop('study_id', axis=1, inplace=True)
    for column in df.columns:
        counts = df[column].value_counts()
        out['stats'][str(column)] = [(str(key), counts[key])
                                     for key in natsorted(counts.index)]

    return out


def sample_template_post_req(study_id, user_id, data_type,
                             sample_template):
    """Creates the sample template from the given file

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id
    data_type : str
        Data type for the sample template
    sample_template : str
        filename to use for creation

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg,
         'file': sample_template}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    file has the file name
    """
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error
    fp_rsp = check_fp(study_id, sample_template)
    if fp_rsp['status'] != 'success':
        # Unknown filepath, so return the error message
        return fp_rsp
    fp_rsp = fp_rsp['file']

    # Define here the message and message level in case of success
    msg = ''
    status = 'success'
    is_mapping_file = looks_like_qiime_mapping_file(fp_rsp)
    if is_mapping_file and not data_type:
        return {'status': 'error',
                'message': 'Please, choose a data type if uploading a '
                           'QIIME mapping file',
                'file': sample_template}

    study = Study(int(study_id))

    # Offload the creation of the sample template to the cluster
    job_id = safe_submit(user_id, create_sample_template, fp_rsp, study,
                         is_mapping_file, data_type)
    # Store the job id attaching it to the sample template id
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study.id,
                 dumps({'job_id': job_id}))

    return {'status': status,
            'message': msg,
            'file': sample_template}


def sample_template_put_req(study_id, user_id, sample_template):
    """Updates a sample template using the given file

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id
    sample_template : str
        filename to use for updating

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg,
         'file': sample_template}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    file has the file name
    """
    exists = _check_sample_template_exists(int(study_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error

    fp_rsp = check_fp(study_id, sample_template)
    if fp_rsp['status'] != 'success':
        # Unknown filepath, so return the error message
        return fp_rsp
    fp_rsp = fp_rsp['file']

    msg = ''
    status = 'success'

    # Offload the update of the sample template to the cluster
    job_id = safe_submit(user_id, update_sample_template, int(study_id),
                         fp_rsp)
    # Store the job id attaching it to the sample template id
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                 dumps({'job_id': job_id}))

    return {'status': status,
            'message': msg,
            'file': sample_template}


@execute_as_transaction
def sample_template_delete_req(study_id, user_id):
    """Deletes the sample template attached to the study

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id

    Returns
    -------
    dict
        results dictonary in the format
        {'status': status,
         'message': msg}

    status can be success, warning, or error depending on result
    message has the warnings or errors
    """
    exists = _check_sample_template_exists(int(study_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(int(study_id), user_id)
    if access_error:
        return access_error

    # Offload the deletion of the sample template to the cluster
    job_id = safe_submit(user_id, delete_sample_template, int(study_id))
    # Store the job id attaching it to the sample template id
    r_client.set(SAMPLE_TEMPLATE_KEY_FORMAT % study_id,
                 dumps({'job_id': job_id}))

    return {'status': 'success', 'message': ''}


@execute_as_transaction
def sample_template_filepaths_get_req(study_id, user_id):
    """Returns all the filepaths attached to the sample template

    Parameters
    ----------
    study_id : int
        The current study object id
    user_id : str
        The current user object id

    Returns
    -------
    dict
        Filepaths in the form
        {'status': status,
         'message': msg,
         'filepaths': filepaths}
        status can be success, warning, or error depending on result
        message has the warnings or errors
        filepaths is a list of tuple of int and str
        All files in the sample template, as [(id, URL), ...]
    """
    exists = _check_sample_template_exists(int(study_id))
    if exists['status'] != 'success':
        return exists
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    try:
        template = SampleTemplate(int(study_id))
    except QiitaDBUnknownIDError as e:
        return {'status': 'error',
                'message': str(e)}

    return {'status': 'success',
            'message': '',
            'filepaths': template.get_filepaths()
            }
