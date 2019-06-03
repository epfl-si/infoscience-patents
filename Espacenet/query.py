# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

"""
Espacenet Module allows to query espacenet.com database very simply 

Sample of working url:

http://ops.epo.org/3.1/rest-services/published-data/search?q=ti%3Dplastic

This modules is made of a query manager (class Espacenet)

Usage:

# =========================
# Patent
 
from Curator.harvest.Espacenet.models import EspacenetPatent
patent = EspacenetPatent(number='2011121089', country = 'WO')
all_kind_patents = patent.fetch()
for p in all_kind_patents: 
    print p.details

# =========================
# PCT
from Curator.harvest.Espacenet.models import EspacenetPCT
pct = EspacenetPCT(epodoc = 'PCT/IB2007/51010')
all_kind_patents = pct.fetch()
for p in all_kind_patents:
    print p.details

# =========================
# Family Patent

from Curator.harvest.Espacenet import EspacenetPatent, EspacenetQuery, EspacenetPatentQuery, EspacenetFamilyPatentQuery
patent = EspacenetPatent(number='697953', country = 'CH')

patent_families = patent.fetch_families() 


patent_family_query = EspacenetFamilyPatentQuery()
patent_families = patent_family_query.fetch(patent)
for patent_family in patent_families.values():
    for patent in patent_family:
        print patent.details

# =========================
# General query

s = EspacenetQuery()
fs = s.fetch('liquid')
"""
import logging
import requests, json, pickle, os.path
import urllib.parse

from datetime import timedelta
from datetime import datetime

from oauthlib.oauth2 import BackendApplicationClient, OAuth2Error

from .models import EspacenetPatent
from .patent_models import PatentFamilies
from .throttle import throttle
from .epo_secrets import get_secret

from cacheout import Cache

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError


client_id = get_secret()["client_id"]
client_secret = get_secret()["client_secret"]

cache = Cache()


ESPACENET_CACHE_TIMEOUT = timedelta(days=30)

logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')


class EspacenetBase(object):
    """Base class for the espacenet api
    Implement rules from espacenet (see http://documents.epo.org/projects/babylon/eponet.nsf/0/7AF8F1D2B36F3056C1257C04002E0AD6/$File/OPS_v3.1_documentation_version_1.2.11_en.pdf
    """
    # url vars, prefix with url_, as we don't want a name clash
    url_protocol = "https"
    url_authority = "ops.epo.org"
    url_version = "3.2"
    url_prefix = "rest-services"
    url_token_generator = "auth/accesstoken"

    # url_service # we may have (p.52) : published-data service
                                        # family service
                                        # number service
                                        # register service
                                        # legal service
                                        # classification service
    # url_reference-type: "", # can be "search" or "publication"
    
    headers = {'Accept': 'application/json'} # we work with json data
    json_fetched = {} # keep a trace of the full return, fulfilled on query call
    
    patents_fetched = [] # keep the result

    @property
    def url(self):
        # sample : http://ops.epo.org/3.1/rest-services/published-data/search/abstract,biblio?q=test
        return "%(url_protocol)s://%(url_authority)s/%(url_version)s/%(url_prefix)s" % EspacenetBase.__dict__

    @property
    def token(self):
        token = cache.get('espacenet_token')
        return token

    @token.setter
    def token_saver(self, token):
        cache.set('espacenet_token', token)

    @property
    def token_url(self):
        # sample : http://ops.epo.org/3.1/rest-services/published-data/search/abstract,biblio?q=test
        return "%(url_protocol)s://%(url_authority)s/%(url_version)s/%(url_token_generator)s" % EspacenetBase.__dict__

    def request(self, url, **kwargs):
        #return requests.get(url, **kwargs)
        # client = BackendApplicationClient(client_id=client_id,
        #                                   token=self.token)
        # oauth = OAuth2Session(client=client)
        #
        # client_session = OAuth2Session(client_id=client_id,
        #                                ,
        #                                token=self.token,
        #                                auto_refresh_url=self.token_url,
        #                                token_updater=self.token_saver)
        try:
            client_type = BackendApplicationClient(client_id=client_id)
            token = cache.get('espacenet_token')

            if not token:
                logger_epo.debug("Need a token, fetching one from %s" % self.token_url)
                logger_epo.debug("client_id %s" % client_id)
                logger_epo.debug("client_secret %s" % client_secret)
                oauth = OAuth2Session(client_id, client=client_type)
                token = oauth.fetch_token(token_url=self.token_url,
                                          client_id=client_id,
                                          client_secret=client_secret, auth=False)
                # rewrite token_type, as Espacenet write 'BearerToken',
                # and it's 'Bearer'
                token['token_type'] = 'Bearer'
                logger_epo.debug("We got our token :  %s" % token)
                cache.set('espacenet_token', token)

            client = OAuth2Session(client_id, token=token)
            return client.get(url, **kwargs)
        except TokenExpiredError as e:
            token = client.refresh_token(self.token_url)
            self.token = token

        client = OAuth2Session(client_id, token=token)
        return client.get(url, **kwargs)

    def fetch(self, file_path = ""):
        """ fetch from Espacenet if no file is provided or we don't have the right to r/w """
        request_return = None

        try:
            if file_path and os.path.exists(file_path):
                outdated = datetime.fromtimestamp(os.path.getctime(file_path)) < (datetime.now() - ESPACENET_CACHE_TIMEOUT)
                if outdated:
                    os.remove(file_path)
                    self.json_fetched = {}
                else:
                    with open(file_path, "r") as my_file:
                        self.json_fetched = pickle.load(my_file)
            
            if not self.json_fetched:
                # get from epo
                try:
                    request_return = self.request(self.url, headers=self.headers)
                except ValueError as e:
                    if not request_return:
                        # nothing returned, that's a request problem
                        raise OAuth2Error(e.message)

                try:
                    self.json_fetched = json.loads(request_return.text)
                except ValueError as e:
                    raise ValueError(e.message + "Value :%s" % request_return.text)
                
                if file_path:
                    json_pickle_file = open(file_path, "w")
                    pickle.dump(self.json_fetched, json_pickle_file, pickle.HIGHEST_PROTOCOL)
                    json_pickle_file.close()

            self.patents_fetched = self._parse_returned_json()
            return self.patents_fetched
        except ValueError:
            if request_return.status_code == 404 or request_return.text.find("<message>No results found</message>") != -1:
                # cannot read json content
                # it may be an xml result not found
                self.patents_fetched = {}
                return self.patents_fetched
            elif request_return.text:
                # the request has completed, but still no data ?
                raise ValueError("""Unmanaged JSON returned for url %s\n
                                    Json : %s
                                 """ % (self.url, request_return.text))
            else:
                #it's a little thing I can not understand
                raise

    def _parse_returned_json(self):
        # get the root (p.18 of the manual)
        try:
            return self.json_fetched['ops:world-patent-data']
        except KeyError:
            PatentFamilies()
    
class PublishedDataService(EspacenetBase):
    """ add some constituent when you use the published-data service """
    url_service = "published-data"
    url_reference_type = "" # can be "publication" or an application like search
    url_constituent = ''    
    
    patent_json_sample = '' # keep a sample of json data
                            # mainly for debug purpose
    
    def __init__(self, constituent=""):
        """
        Feel free to set abstract, biblio or full_cycle
        if you need it in the result
        constituent :
                can be "full-cycle,images,biblio,abstract"
                see p.54 for special rules
        """
        super(PublishedDataService, self).__init__()
        
        allowed_constituent = "full-cycle,biblio,abstract".split(',')
        
        """
        Valid option detail:
        <option value="biblio" />
        <option value="abstract" />
        <option value="full-cycle" />
        <option value="abstract,full-cycle" />
        <option value="biblio,full-cycle" />        
        """
        # assert we are on the right road
        if constituent:
            multiple_constituent = constituent.split(',')
            if not set(multiple_constituent) & set(allowed_constituent):
                raise AttributeError
            
            if self.url_constituent:
                self.url_constituent = self.url_constituent + ',' + constituent
            else:
                self.url_constituent = constituent
        
    @property
    def url(self):
        base_url = super(PublishedDataService, self).url
        # remove empty string
        url_array = filter(None, [base_url,
                                  self.url_service,
                                  self.url_reference_type,
                                  self.url_constituent])
        return "/".join(url_array)
    
    def _parse_returned_json(self):
        """ from a the json request, transform it to a list of Patent """ 
        returned_patents = super(PublishedDataService, self)._parse_returned_json()
        
        if not returned_patents:
            PatentFamilies()
        
        family_patents_list = self._parse_exchange_documents(returned_patents['exchange-documents'])
        
        return family_patents_list
    
    def _parse_exchange_document(self, exchange_document):
        """ from an exchange_document, build a Patent """
        # keep a sample
        self.patent_json_sample = exchange_document
        
        if '@status' in exchange_document and exchange_document['@status'] == 'not found':
            return None
        
        return EspacenetPatent(exchange_document = exchange_document)
    
    def _parse_exchange_documents(self, exchange_documents):
        """ when we ask for bibliographical data (on a search or in a specific patent number)
        trough the use of endpoint or constituent, Espacenet return an exchange_document 
        """
        families_patents = PatentFamilies()        
         
        # we may have multiple documents
        if not isinstance(exchange_documents, (list, tuple)):
            exchange_documents = [exchange_documents]
        
        for exchange_document in exchange_documents:
            # we may have multiple exchange_document
            patents = exchange_document['exchange-document']
            
            if not isinstance(patents, (list, tuple)):
                patents = [patents]
                
            for patent in patents:
                patent_object = self._parse_exchange_document(patent)
                
                if patent_object:
                    if patent_object.family_id in families_patents:
                        families_patents[patent_object.family_id].append(patent_object)
                    else:
                        families_patents[patent_object.family_id] = [patent_object]
            
        return families_patents
    
class EspacenetQuery(PublishedDataService):
    """Class to allow query the Espacenet api and return a list of patent
    Return only basic info, no bibliographic-data
    If auto_range is not set, fetch only the first 100 results
    """
    url_reference_type = "search"
    total_count = 0
    espacenet_range_limit = 2000

    def __init__(self, auto_range=False, exception_on_overhead=True,
                 *args, **kwargs):
        """ 
        auto_range :
            if we have more result than the range limit, do multiple fetch and 
            return one result
        exception_on_overhead :
            Espacenet return only 2000 elements. By default, we throw an exception
             if the limit is identified. You change the behavior to have an
             incomplete return of 2000 elements
        """
        super(EspacenetQuery, self).__init__(*args, **kwargs)

        self.auto_range = auto_range
        self.exception_on_overhead = exception_on_overhead
        self.start_range = 1
        self.end_range = 100 # default 20, max 100

    @property
    def url(self):
        base_url = super(EspacenetQuery, self).url
        #add q search
        return base_url + "?q=%s" % self.paramaters + '&Range=%s-%s' % (self.start_range, self.end_range)
    
    def fetch(self, query):
        """
        query can be by example :
        A word : "liquid"
        A specific field : "applicant=IBM&Range=1"
                           "famn=312311" (family search)
                           
        More information on page 152      
        """
        self.paramaters = urllib.parse.quote(query)

        if not self.auto_range:
            # one fetch and return
            patents_fetched = super(EspacenetQuery, self).fetch()
        else:
            # fetch until we got all
            total_fetched = 0
            patents_fetched = PatentFamilies()

            while True:
                if self.start_range > self.espacenet_range_limit:
                    break

                fetch_batch = super(EspacenetQuery, self).fetch()

                # build one result
                for key, value in fetch_batch.iteritems():
                    if patents_fetched.get(key):
                        patents_fetched[key].extend(value)
                    else:
                        patents_fetched[key] = value

                # need more ?
                total_fetched += self.end_range - self.start_range + 1

                if self.exception_on_overhead and self.total_count > self.espacenet_range_limit:
                    raise ValueError("Espacenet has a limit of 2000 "
                                     "elements. Build a specific query "
                                     "or set exception_on_overhead=False")

                if self.total_count == 0 or \
                   total_fetched >= self.total_count:
                    break

                # prepare next iteration
                self.start_range += 100
                self.end_range += 100
                # don't allow over 2000
                self.end_range = min(self.end_range, self.espacenet_range_limit)
                if self.end_range > self.total_count:
                    self.end_range = self.total_count
                self.json_fetched = {}

        return patents_fetched

    def _parse_publication_references(self, returned_patents):
        """ EPO return two types of data list :
            One for search result, where you have only the patent basic's information
            One with biographical datas, in exchange_document format.
        """
        if not isinstance(returned_patents, (list, tuple)):
            returned_patents = [returned_patents]
            
        families_patents = PatentFamilies()
            
        for patent_list in returned_patents:
            # keep a sample
            self.patent_json_sample = patent_list
            
            family_patent_id = patent_list['@family-id']
            patent_info = patent_list['document-id']
            
            number = patent_info['doc-number']['$']
            country = patent_info['country']['$']
            
            try:
                kind = patent_info['kind']['$']
            except KeyError:
                kind = None
            
            try:
                date = patent_info['date']['$']
            except KeyError:
                date = None                
            
            patent = EspacenetPatent(number = number,
                                    country = country,
                                    family_id = family_patent_id,
                                    kind = kind,
                                    date = date)
            
            if family_patent_id in families_patents:
                families_patents[family_patent_id].append(patent)
            else:
                families_patents[family_patent_id] = [patent]

        return families_patents
    
    def _parse_returned_json(self):
        """ from a json request, transform it to a list of Patent  """
        returned_patents = super(PublishedDataService, self)._parse_returned_json()
        
        if not returned_patents:
            PatentFamilies()
        
        #get root path
        returned_patents = returned_patents['ops:biblio-search']
        
        try:
            self.total_count = int(returned_patents['@total-result-count'])
        except (KeyError, ValueError):
            self.total_count = 0
        
        if self.total_count == 0:
            return PatentFamilies()

        # if we have some endpoints and/or constituent (see parent class),
        # data are inside exchange-document
        # let's get the light on this :
        
        if 'ops:publication-reference' in returned_patents['ops:search-result']:
            patents_list = self._parse_publication_references(returned_patents['ops:search-result']['ops:publication-reference'])
        elif 'exchange-documents' in returned_patents['ops:search-result']:
            # exchange-document here:
            patents_list = self._parse_exchange_documents(returned_patents['ops:search-result']['exchange-documents'])
        else:
            raise TypeError
        
        return patents_list
        
class EspacenetPatentQuery(PublishedDataService):
    """ Add functionality to query from a Patent
        and return a FamilyPatent list
        You can get one or more of this information :
        fulltext,claims,description,images,equivalents,biblio,abstract
    """
    url_reference_type = "publication"
    url_input_format = "epodoc" # original, docdb
    url_endpoints = ""
    returned_json = {} # keep a trace
    
    def fetch(self, patent, endpoints="", file_path = ""):
        """
        Feel free to set abstract, biblio or full_cycle
            if you need it in the result
        endpoints :
                Espacenet empty default is biblio (see p.52)
                can be : "fulltext,claims,description,images,equivalents,
                biblio,abstract" or any combination
        """        
                
        self.patent = patent
        
        allowed_endpoints = "fulltext,claims,description,images,equivalents,biblio,abstract".split(',')
        
        # assert we are on the right road
        if endpoints:
            multiple_endpoints = endpoints.split(',')
            if not set(multiple_endpoints) & set(allowed_endpoints):
                raise AttributeError
        
        self.url_endpoints = endpoints        
        
        return super(EspacenetPatentQuery, self).fetch(file_path = file_path)
        
    @property
    def url(self):
        # take the super of PubishedDataService, as we add endpoints to it
        base_url = super(PublishedDataService, self).url
        
        # remove empty string
        url_array = filter(None, [base_url,
                                  self.url_service,
                                  self.url_reference_type,
                                  self.url_input_format,
                                  self.patent.querystring(),
                                  self.url_endpoints,
                                  self.url_constituent])

        return "/".join(url_array)

class EspacenetPCTPatentQuery(EspacenetPatentQuery):
    """ Fetch PCTs by epodoc in published-data
        e.g. http://ops.epo.org/3.1/rest-services/published-data/application/epodoc/WO2007IB51010/biblio
        NB: the returned data is a _publication_ having the requested epodoc as
        its application reference.
    """
    url_reference_type = "application"

class EspacenetFamilyPatentQueryBase(EspacenetPatentQuery):
    """ Base class for family queries """
    url_service = "family"

class EspacenetFamilyPatentNumberQuery(EspacenetFamilyPatentQueryBase):    
    """ class to get only patent numbers from a family """
    
    def _parse_returned_json(self):
        """ from a the json request, transform it to a list of Patent """ 
        returned_patents = super(PublishedDataService, self)._parse_returned_json()
        
        if not returned_patents:
            return PatentFamilies()
        
        returned_patents = returned_patents['ops:patent-family']['ops:family-member']

        if not isinstance(returned_patents, (list, tuple)):
            returned_patents = [returned_patents]
            
        family_patents_list = PatentFamilies()
                    
        for patent in returned_patents:
            family_id = patent['@family-id']
            publication_reference = patent['publication-reference']

            if family_id in family_patents_list:
                family_patents_list[family_id].append(EspacenetPatent(family_id = family_id, publication_reference = publication_reference))
            else:
                family_patents_list[family_id] = [EspacenetPatent(family_id = family_id, publication_reference = publication_reference)]
            
        return family_patents_list    
    
class EspacenetFamilyPatentQuery(EspacenetFamilyPatentQueryBase):
    """ Class to query full families biblio information """
    
    # add the biblio data
    url_constituent = 'biblio' 
    
    def _parse_returned_json(self):
        """ from a the json request, transform it to a list of Patent """ 
        returned_patents = super(PublishedDataService, self)._parse_returned_json()
        
        if not returned_patents:
            return PatentFamilies()
        
        returned_patents = returned_patents['ops:patent-family']['ops:family-member']

        if not isinstance(returned_patents, (list, tuple)):
            returned_patents = [returned_patents]
            
        family_patents_list = PatentFamilies()
                    
        for patent in returned_patents:
            family_id = patent['@family-id']
            try:
                exchange_document = patent['exchange-document']
            except (KeyError) as e:
                # if we can not find exchange-document, that mean we may
                # be in a 'publication-reference' node
                # Publication references are number only, as we have data in
                # biblio, ignore it
                if patent.get('publication-reference'):
                    continue
                else:
                    raise e
            
            p = EspacenetPatent(exchange_document = exchange_document)
            if family_id in family_patents_list:
                family_patents_list[family_id].append(p)
            else:
                family_patents_list[family_id] = [p]
            
        return family_patents_list    