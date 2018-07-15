# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .oauth2 import OauthBaseHandler, authenticate_oauth
import qiita_db as qdb


def _get_reference(r_id):
    """Returns the reference with the given id if exists

    Parameters
    ----------
    r_id : int
        The reference id

    Returns
    -------
    qiita_db.reference.Reference, bool, string
        The requested reference or None
        Whether if we could get the reference object or not
        Error message in case we counldn't get the reference object
    """
    try:
        reference = qdb.reference.Reference(r_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
<<<<<<< HEAD
        return None, False, 'Reference does not exist'
    except qdb.exceptions.QiitaDBError as e:
        return None, False, 'Error instantiating the reference: %s' % str(e)
=======
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason='Error instantiating the reference: '
                        '%s' % str(e))
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed

    return reference, True, ''


class ReferenceHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, reference_id):
        """Retrieves the filepath information of the given reference

        Parameters
        ----------
        reference_id : str
            The id of the reference whose filepath information is being
            retrieved

        Returns
        -------
        dict
<<<<<<< HEAD
            Format:
            {'success': bool,
             'error': str,
             'filepaths': list of (str, str)}
            - success: whether the request is successful or not
            - error: in case that success is false, it contains the error msg
            - filepaths: the filepaths attached to the reference and their
            filepath types
        """
        with qdb.sql_connection.TRN:
            reference, success, error_msg = _get_reference(reference_id)
            fps = None
            if success:
                fps = [(reference.sequence_fp, "reference_seqs")]
                tax_fp = reference.taxonomy_fp
                if tax_fp:
                    fps.append((tax_fp, "reference_tax"))
                tree_fp = reference.tree_fp
                if tree_fp:
                    fps.append((tree_fp, "reference_tree"))

            response = {'success': success, 'error': error_msg,
                        'filepaths': fps}
=======
            'name': str
                the reference name
            'version': str
                the reference version
            'filepaths': dict of {str: str}
                The filepaths attached to the reference keyed by filepath type
        """
        with qdb.sql_connection.TRN:
            reference = _get_reference(reference_id)

            fps = {'reference_seqs': reference.sequence_fp}
            tax_fp = reference.taxonomy_fp
            if tax_fp:
                fps["reference_tax"] = tax_fp
            tree_fp = reference.tree_fp
            if tree_fp:
                fps["reference_tree"] = tree_fp

            response = {
                'name': reference.name,
                'version': reference.version,
                'files': fps
            }
>>>>>>> 405cbef0c9f71c620da95a0c1ba6c7d3d588b3ed

        self.write(response)
