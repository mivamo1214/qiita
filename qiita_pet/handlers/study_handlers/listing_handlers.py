# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from json import dumps
from future.utils import viewitems
from collections import defaultdict
from os.path import basename

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task
from pyparsing import ParseException

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_db.artifact import Artifact
from qiita_db.user import User
from qiita_db.study import Study, StudyPerson
from qiita_db.search import QiitaStudySearch
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.logger import LogEntry
from qiita_db.exceptions import QiitaDBIncompatibleDatatypeError
<<<<<<< HEAD
from qiita_db.reference import Reference
from qiita_db.util import get_table_cols, get_pubmed_ids_from_dois
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import execute_as_transaction
=======
from qiita_db.util import (add_message, generate_study_list)
from qiita_pet.util import EBI_LINKIFIER
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import (
    study_person_linkifier, doi_linkifier, pubmed_linkifier, check_access)


@execute_as_transaction
def _get_shared_links_for_study(study):
    shared = []
    for person in study.shared_with:
        name = person.info['name']
        email = person.email
        # Name is optional, so default to email if non existant
        if name:
            shared.append(study_person_linkifier(
                (email, name)))
        else:
            shared.append(study_person_linkifier(
                (email, email)))
    return ", ".join(shared)


@execute_as_transaction
def _build_single_study_info(study, info, study_proc, proc_samples):
    """Clean up and add to the study info for HTML purposes

    Parameters
    ----------
    study : Study object
        The study to build information for
    info : dict
        Information from Study.get_info
    study_proc : dict of dict of lists
        Dictionary keyed on study_id that lists all processed data associated
        with that study. This list of processed data ids is keyed by data type
    proc_samples : dict of lists
        Dictionary keyed on proc_data_id that lists all samples associated with
        that processed data.

    Returns
    -------
    dict
        info-information + extra information for the study,
        slightly HTML formatted
    """
    PI = StudyPerson(info['principal_investigator_id'])
    status = study.status
    if info['publication_doi'] is not None:
        pmids = get_pubmed_ids_from_dois(info['publication_doi']).values()
        info['pmid'] = ", ".join([pubmed_linkifier([p]) for p in pmids])
        info['publication_doi'] = ", ".join([doi_linkifier([p])
                                             for p in info['publication_doi']])

    else:
        info['publication_doi'] = ""
        info['pmid'] = ""
    if info["number_samples_collected"] is None:
        info["number_samples_collected"] = 0
    info["shared"] = _get_shared_links_for_study(study)
    # raw data is any artifact that is not Demultiplexed or BIOM

    info["num_raw_data"] = len([a for a in study.artifacts()
                                if a.artifact_type not in ['Demultiplexed',
                                                           'BIOM']])
    info["status"] = status
    info["study_id"] = study.id
    info["pi"] = study_person_linkifier((PI.email, PI.name))
    del info["principal_investigator_id"]
    del info["email"]
    # Build the proc data info list for the child row in datatable
    info["proc_data_info"] = []
    for data_type, proc_datas in viewitems(study_proc[study.id]):
        info["proc_data_info"].extend([
            _build_single_proc_data_info(pd_id, data_type, proc_samples[pd_id])
            for pd_id in proc_datas])
    return info


@execute_as_transaction
def _build_single_proc_data_info(proc_data_id, data_type, samples):
    """Build the proc data info list for the child row in datatable

    Parameters
    ----------
    proc_data_id : int
        The processed data attached to he study, in the form
        {study_id: [proc_data_id, proc_data_id, ...], ...}
    data_type : str
        Data type of the processed data
    proc_samples : dict of lists
        The samples available in the processed data, in the form
        {proc_data_id: [samp1, samp2, ...], ...}

    Returns
    -------
    dict
        The information for the processed data, in the form {info: value, ...}
    """
    proc_data = Artifact(proc_data_id)
    proc_info = {'processed_date': str(proc_data.timestamp)}
    proc_info['pid'] = proc_data_id
    proc_info['data_type'] = data_type
    proc_info['processed_date'] = str(proc_info['processed_date'])
    params = proc_data.processing_parameters.values
    del params['input_data']
    ref = Reference(params.pop('reference'))
    proc_info['reference_name'] = ref.name
    proc_info['taxonomy_filepath'] = basename(ref.taxonomy_fp)
    proc_info['sequence_filepath'] = basename(ref.sequence_fp)
    proc_info['tree_filepath'] = basename(ref.tree_fp)
    proc_info['reference_version'] = ref.version
    proc_info['algorithm'] = 'sortmerna'
    proc_info['samples'] = sorted(proc_data.prep_templates[0].keys())
    proc_info.update(params)

    return proc_info


@execute_as_transaction
def _build_study_info(user, study_proc=None, proc_samples=None):
    """Builds list of dicts for studies table, with all HTML formatted

    Parameters
    ----------
    user : User object
        logged in user
    study_proc : dict of lists, optional
        Dictionary keyed on study_id that lists all processed data associated
        with that study. Required if proc_samples given.
    proc_samples : dict of lists, optional
        Dictionary keyed on proc_data_id that lists all samples associated with
        that processed data. Required if study_proc given.

    Returns
    -------
    infolist: list of dict of lists and dicts
        study and processed data info for JSON serialiation for datatables
        Each dict in the list is a single study, and contains the text

    Notes
    -----
    Both study_proc and proc_samples must be passed, or neither passed.
    """
    # Logic check to make sure both needed parts passed
    if study_proc is not None and proc_samples is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass proc_samples when study_proc given')
    elif proc_samples is not None and study_proc is None:
        raise IncompetentQiitaDeveloperError(
            'Must pass study_proc when proc_samples given')

    # get list of studies for table
<<<<<<< HEAD
    study_set = user.user_studies.union(
        Study.get_by_status('public')).union(user.shared_studies)
=======
    user_study_set = user.user_studies.union(user.shared_studies)
    if search_type == 'user':
        if user.level == 'admin':
            user_study_set = (user_study_set |
                              Study.get_by_status('sandbox') |
                              Study.get_by_status('private') |
                              Study.get_by_status('awaiting_approval') -
                              Study.get_by_status('public'))
        study_set = user_study_set
    elif search_type == 'public':
        study_set = Study.get_by_status('public') - user_study_set
    else:
        raise ValueError('Not a valid search type')
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
    if study_proc is not None:
        study_set = study_set.intersection(study_proc)
    if not study_set:
        # No studies left so no need to continue
        return []

<<<<<<< HEAD
    cols = ['study_id', 'email', 'principal_investigator_id',
            'publication_doi', 'study_title', 'metadata_complete',
            'number_samples_collected', 'study_abstract']
    study_info = Study.get_info([s.id for s in study_set], cols)

    # get info for the studies
    infolist = []
    for info in study_info:
        # Convert DictCursor to proper dict
        info = dict(info)
        study = Study(info['study_id'])
        # Build the processed data info for the study if none passed
        if build_samples:
            proc_data_list = [ar for ar in study.artifacts()
                              if ar.artifact_type == 'BIOM']
            proc_samples = {}
            study_proc = {study.id: defaultdict(list)}
            for proc_data in proc_data_list:
                study_proc[study.id][proc_data.data_type].append(proc_data.id)
                # there is only one prep template for each processed data
                proc_samples[proc_data.id] = proc_data.prep_templates[0].keys()

        study_info = _build_single_study_info(study, info, study_proc,
                                              proc_samples)
        infolist.append(study_info)

    return infolist
=======
    return generate_study_list([s.id for s in study_set],
                               public_only=(search_type == 'public'))
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed


class ListStudiesHandler(BaseHandler):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, message="", msg_level=None):
        all_emails_except_current = yield Task(self._get_all_emails)
        all_emails_except_current.remove(self.current_user.id)
        avail_meta = SampleTemplate.metadata_headers() +\
            get_table_cols("study")
        self.render('list_studies.html',
                    availmeta=avail_meta,
                    all_emails_except_current=all_emails_except_current,
                    message=message,
                    msg_level=msg_level)

    def _get_all_emails(self, callback):
        callback(list(User.iter()))


class StudyApprovalList(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        user = self.current_user
        if user.level != 'admin':
            raise HTTPError(403,
                            reason='User %s is not admin' % self.current_user)

        studies = defaultdict(list)
        for artifact in Artifact.iter_by_visibility('awaiting_approval'):
            studies[artifact.study].append(artifact.id)
        parsed_studies = [(s.id, s.title, s.owner.email, pds)
                          for s, pds in viewitems(studies)]

        self.render('admin_approval.html',
                    study_info=parsed_studies)


class ShareStudyAJAX(BaseHandler):
    @execute_as_transaction
    def _get_shared_for_study(self, study, callback):
        shared_links = _get_shared_links_for_study(study)
        users = [u.email for u in study.shared_with]
        callback((users, shared_links))

    @execute_as_transaction
    def _share(self, study, user, callback):
        user = User(user)
        callback(study.share(user))

    @execute_as_transaction
    def _unshare(self, study, user, callback):
        user = User(user)
        callback(study.unshare(user))

    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self):
        study_id = int(self.get_argument('study_id'))
        study = Study(study_id)
        check_access(self.current_user, study, no_public=True,
                     raise_error=True)

        selected = self.get_argument('selected', None)
        deselected = self.get_argument('deselected', None)

        if selected is not None:
            yield Task(self._share, study, selected)
        if deselected is not None:
            yield Task(self._unshare, study, deselected)

        users, links = yield Task(self._get_shared_for_study, study)

        self.write(dumps({'users': users, 'links': links}))


class SearchStudiesAJAX(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, ignore):
        user = self.get_argument('user')
        query = self.get_argument('query')
        echo = int(self.get_argument('sEcho'))

        if user != self.current_user.id:
<<<<<<< HEAD
            raise HTTPError(403, 'Unauthorized search!')
=======
            raise HTTPError(403, reason='Unauthorized search!')
        if search_type not in ['user', 'public']:
            raise HTTPError(400, reason='Not a valid search type')
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
        if query:
            # Search for samples matching the query
            search = QiitaStudySearch()
            try:
                search(query, self.current_user)
                study_proc, proc_samples, _ = search.filter_by_processed_data()
            except ParseException:
                self.clear()
                self.set_status(400)
                self.write('Malformed search query. Please read "search help" '
                           'and try again.')
                return
            except QiitaDBIncompatibleDatatypeError as e:
                self.clear()
                self.set_status(400)
                searchmsg = ''.join(e)
                self.write(searchmsg)
                return
            except Exception as e:
                # catch any other error as generic server error
                self.clear()
                self.set_status(500)
                self.write("Server error during search. Please try again "
                           "later")
                LogEntry.create('Runtime', str(e),
                                info={'User': self.current_user.id,
                                      'query': query})
                return
        else:
            study_proc = proc_samples = None
<<<<<<< HEAD
        info = _build_study_info(self.current_user, study_proc=study_proc,
                                 proc_samples=proc_samples)
=======
        info = _build_study_info(self.current_user, search_type, study_proc,
                                 proc_samples)
        # linkifying data
        len_info = len(info)
        for i in range(len_info):
            info[i]['shared'] = ", ".join([study_person_linkifier(element)
                                           for element in info[i]['shared']])

            ppid = [pubmed_linkifier([p]) for p in info[i]['publication_pid']]
            pdoi = [doi_linkifier([p]) for p in info[i]['publication_doi']]
            del info[i]['publication_pid']
            del info[i]['publication_doi']
            info[i]['pubs'] = ', '.join(ppid + pdoi)

            info[i]['pi'] = study_person_linkifier(info[i]['pi'])

            info[i]['ebi_info'] = info[i]['ebi_submission_status']
            ebi_study_accession = info[i]['ebi_study_accession']
            if ebi_study_accession:
                info[i]['ebi_info'] = '%s (%s)' % (
                    ''.join([EBI_LINKIFIER.format(a)
                             for a in ebi_study_accession.split(',')]),
                    info[i]['ebi_submission_status'])

>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed
        # build the table json
        results = {
            "sEcho": echo,
            "iTotalRecords": len(info),
            "iTotalDisplayRecords": len(info),
            "aaData": info
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))
