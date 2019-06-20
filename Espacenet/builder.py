# -*- coding: utf-8 -*-

import logging, json

import epo_ops

from .patent_models import PatentFamilies
from .marc import MarcPatentFamilies as PatentFamilies
from .marc import MarcEspacenetPatent as EspacenetPatent
from .epo_secrets import get_secret

logger_epo = logging.getLogger('EPO')


# utils to pretty print
def pp_json(json_thing, sort=True, indents=4):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


class EspacenetSearchResult:
    patent_families = PatentFamilies()

    def __init__(self, json_fetched=None):
        if json_fetched:
            biblio_search = json_fetched['ops:biblio-search']

            self.initial_search = biblio_search['ops:query']['$']
            self.total_count = int(biblio_search['@total-result-count'])
            self.range_begin = int(biblio_search['ops:range']['@begin'])
            self.range_end = int(biblio_search['ops:range']['@end'])
        else:
            # allow empty instanciation
            self.total_count = None


class EspacenetBuilderClient(epo_ops.Client):
    """Build models from returned json, based on the epo_ops.Client
       Force Json format as return
    """
    def __init__(self, use_cache=True, *args, **kwargs):
        if not "key" in kwargs and not "secret" in kwargs:
            kwargs['key'] = get_secret()["client_id"]
            kwargs['secret'] = get_secret()["client_secret"]

        kwargs['accept_type'] = 'json'
        kwargs['middlewares'] = [
            epo_ops.middlewares.Throttler(),
        ]

        if use_cache:
            logger_epo.debug("Cache middleware is enabled")
            kwargs['middlewares'].append(epo_ops.middlewares.Dogpile())
        else:
            logger_epo.debug("Cache middleware is disabled")

        super().__init__(*args, **kwargs)

    def _parse_exchange_document(self, exchange_document):
        """ from an exchange_document, verify it's valid and sent it to patent builder """
        if '@status' in exchange_document and exchange_document['@status'] == 'not found':
            return None

        return EspacenetPatent(exchange_document = exchange_document)

    def _parse_patent(self, exchange_documents_json):
        exchange_document = exchange_documents_json['exchange-documents']['exchange-document']
        # look like we can have a list of exchange-document,
        # it may mean that we have the same number but with a different kind
        # keep only the first
        if isinstance(exchange_document, (tuple, list)):
            exchange_document = exchange_document[0]
        return self._parse_exchange_document(exchange_document)

    def patent(self, *args, **kwargs):
        r"""
        Retrieve a specific patent
        :Keyword Arguments:
            * *input* (``epo_ops.models``) --
        """
        logger_epo.debug("Patent fetching API with patent %s ..." % kwargs['input'].number)

        # only published patents
        kwargs['reference_type'] = 'publication'  # publication, application, priority
        # we need biblio info
        kwargs['endpoint'] = 'biblio'
        kwargs['constituents'] = []

        request = super().published_data(*args, **kwargs)
        json_fetched = request.content

        try:
            json_fetched = json.loads(json_fetched)
        except ValueError as e:
            raise ValueError("Value error for : %s" % request.content) from e

        try:
            json_fetched = json_fetched['ops:world-patent-data']
        except KeyError:
            # this should not happens
            raise

        if not json_fetched:
            return PatentFamilies()

        logger_epo.debug("Parsing a returned json...")

        patent = self._parse_patent(json_fetched)

        logger_epo.debug("Patent found and returning")

        return patent

    def _parse_family_member(self, family_member):
        """ when we ask for bibliographical data (on a search or in a specific patent number)
        trough the use of endpoint or constituent, Espacenet return an exchange_document
        """
        families_patents = PatentFamilies()

        if not isinstance(family_member, (list, tuple)):
            # only one exchange-document, make it like a multiple
            family_member = [family_member]

        for patent_in_family in family_member:
            if 'exchange-document' not in patent_in_family:
                # sometimes we don't have an exchange-document
                continue

            patent = patent_in_family['exchange-document']
            patent_object = self._parse_exchange_document(patent)

            if patent_object:
                if patent_object.family_id in families_patents:
                    families_patents[patent_object.family_id].append(patent_object)
                else:
                    families_patents[patent_object.family_id] = [patent_object]

        return families_patents

    def family(self, *args, **kwargs):
        r"""
        Do a search inside a specific range
        :Keyword Arguments:
            * *input* (``epo_ops.models``) --
        """

        logger_epo.debug("Family fetching API with patent %s ..." % kwargs['input'].number)

        # only published patents
        kwargs['reference_type'] = 'publication'  # publication, application, priority
        # we need biblio info
        kwargs['endpoint'] = 'biblio'
        kwargs['constituents'] = []

        request = super().family(*args, **kwargs)
        json_fetched = request.content

        try:
            json_fetched = json.loads(json_fetched)
        except ValueError as e:
            raise ValueError("Value error for : %s" % request.content) from e

        try:
            json_fetched = json_fetched['ops:world-patent-data']
        except KeyError:
            # this should not happens
            raise

        if not json_fetched:
            return PatentFamilies()

        logger_epo.info("Loading published data as patent families")
        family_patents_list = self._parse_family_member(json_fetched['ops:patent-family']['ops:family-member'])

        return family_patents_list

    def _fetch_search_in_range(self, *args, **kwargs):
        kwargs['constituents'] = ['biblio']  # we always want biblio
        logger_epo.debug("Doing an API search with {}".format(kwargs))
        request = super().published_data_search(*args, **kwargs)
        json_fetched = request.content

        try:
            json_fetched = json.loads(json_fetched)
        except ValueError as e:
            raise ValueError("Value error for : %s" % request.content) from e

        try:
            json_fetched = json_fetched['ops:world-patent-data']
        except KeyError:
            # this should not happens
            raise

        results = EspacenetSearchResult(json_fetched)

        if results.total_count == 0:
            results.patent_families = PatentFamilies()
        else:
            # fullfil results with a families patents dict
            patent_families = PatentFamilies()
            search_result_json = json_fetched['ops:biblio-search']['ops:search-result']['exchange-documents']

            for exchange_document in search_result_json:
                patent_json = exchange_document['exchange-document']
                patent_object = self._parse_exchange_document(patent_json)

                if patent_object:
                    patent_families.setdefault(patent_object.family_id, []).append(patent_object)

            logger_epo.debug("Found {} patents in {} families".format(
                len(patent_families.patents),
                len(patent_families)
            ))

            results.patent_families = patent_families

        return results

    def published_data_search_with_range(self, *args, **kwargs):
        r"""
        Do a search inside a specific range
        :Keyword Arguments:
            * *cql* (``str``) --
                search value
            * *range_begin* (``int``) --
            * *range_end* (``int``) --
        """
        return self._fetch_search_in_range(*args, **kwargs)

    def published_data_search(self, *args, **kwargs):
        r"""
        Unlimited search that make multiple requests until
        all patents have been fetched. Limit is still 10'000 though

        :Keyword Arguments:
            * *cql* (``str``) --
                search value
        """
        final_results = EspacenetSearchResult()
        total_fetched = 0
        espacenet_range_limit = 10000
        range_iteration_count = 100

        range_begin = 1
        range_end = 100

        logger_epo.info("Searching patents trough EPO API...")

        while True:
            if range_begin > espacenet_range_limit:
                break

            # set kwargs for _fetch_search_in_range
            kwargs["range_begin"] = range_begin
            kwargs["range_end"] = range_end

            result_patents = self._fetch_search_in_range(*args, **kwargs)

            # build one result
            for key, value in result_patents.patent_families.items():
                if final_results.patent_families.get(key):
                    final_results.patent_families[key].extend(value)
                else:
                    final_results.patent_families[key] = value

            # need more ?
            total_fetched += result_patents.range_end - result_patents.range_begin + 1

            logger_epo.debug("Done an iteration of fetch {}/{}".format(
                total_fetched,
                result_patents.total_count,
            ))

            if result_patents.total_count > espacenet_range_limit:
                    raise ValueError("Espacenet has a limit of 10000 "
                                    "elements. Build a specific query ")

            if result_patents.total_count == 0 or \
                total_fetched >= result_patents.total_count:
                break

            # prepare next iteration
            range_begin += range_iteration_count
            range_end += range_iteration_count
            # don't allow over 10000
            range_end = min(range_end, espacenet_range_limit)
            if range_end > result_patents.total_count:
                range_end = result_patents.total_count

        # set final results good values
        final_results.range_begin = range_begin
        final_results.range_end = range_end
        final_results.total_count = total_fetched

        logger_epo.debug("Search result : Found {} patents inside {} uniq families".format(
                len(final_results.patent_families.patents),
                len(final_results.patent_families),
        ))

        return final_results

    def search(self, value, range_begin=None, range_end=None):
        """ Entry method that decide if auto_range is needed """
        if range_begin and range_end:
            return self.published_data_search_with_range(
                cql = value,
                range_begin = range_begin,
                range_end = range_end)
        else:
            return self.published_data_search(cql = value)
