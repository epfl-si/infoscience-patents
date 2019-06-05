# -*- coding: utf-8 -*-

import logging, json

import epo_ops

from .models import EspacenetPatent
from .patent_models import PatentFamilies


logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')


class EspacenetSearchResult:
    patent_families = PatentFamilies()

    def __init__(self, json_fetched):
        biblio_search = json_fetched['ops:biblio-search']

        self.initial_search = biblio_search['ops:query']['$']
        self.total_count = biblio_search['@total-result-count']
        self.range_begin = biblio_search['ops:range']['@begin']
        self.range_end = biblio_search['ops:range']['@end']


class EspacenetBuilderClient(epo_ops.Client):
    """Build models from returned json, based on the epo_ops.Client
       Force Json format as return
    """
    def __init__(self, use_cache=True, *args, **kwargs):
        kwargs['accept_type'] = 'json'
        kwargs['middlewares'] = [
            epo_ops.middlewares.Throttler(),
        ]

        if use_cache:
            kwargs['middlewares'].append(epo_ops.middlewares.Dogpile())

        super().__init__(*args, **kwargs)

    def _parse_exchange_document(self, exchange_document):
        """ from an exchange_document, verify it's valid and sent it to patent builder """
        if '@status' in exchange_document and exchange_document['@status'] == 'not found':
            return None
        
        return EspacenetPatent(exchange_document = exchange_document)

    def _parse_family_member(self, family_member):
        """ when we ask for bibliographical data (on a search or in a specific patent number)
        trough the use of endpoint or constituent, Espacenet return an exchange_document 
        """
        families_patents = PatentFamilies()
         
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
        # reference_type, input, endpoint=None, constituents=None):
        
        logger_epo.info("Getting patents trough EPO API...")
        logger_epo.debug("API fetching with %s" % kwargs)

        # only published patents
        kwargs['reference_type'] = 'publication'  # publication, application, priority
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

        family_patents_list = self._parse_family_member(json_fetched['ops:patent-family']['ops:family-member'])

        logger_epo.info("Loading published data from API")

        return family_patents_list

    def _parse_published_data_search_exchange(self):
        families_patents = PatentFamilies()
         
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

    def published_data_search(self, *args, **kwargs):
        # cql, range_begin=1, range_end=25, constituents=None
        
        logger_epo.info("Searching patents trough EPO API...")
        logger_epo.debug("API search with %s" % kwargs)

        kwargs['constituents'] =  ['biblio']  # we always want biblio
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
                    patent_families.setdefault(patent_object.family_id, [patent_object]).append(patent_object)

            results.patent_families = patent_families

        return results
