import json
import re

patent_regex = r"^(?P<country>\D{2})(?P<number>\d{1,})[\s|-]?(?P<kind>\w\d)?"

# utils to pretty print
def p_json(json_thing, sort=True, indents=4):
    if type(json_thing) is str:
        return json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents)
    else:
        return json.dumps(json_thing, sort_keys=sort, indent=indents)
    return None


def _get_best_patent_for_data(patents):
    """ from multiple patents, find the best one that as data we need
        Like, not using the chinese name of inventors, ...
    """
    # not used anymore, unless we fetch multiple patent in a family
    # for patent in patents:
    #    has_extended_unicode_char = False
    #    if patent.inventors:
    #        for inventor in patent.inventors:
    #            for charact in inventor:
    #                if unicodedata.category(charact) == 'Lo':
    #                    has_extended_unicode_char = True
    #
    #        if not has_extended_unicode_char:
    #            return patent

    # Find a patent that is first EP, then US, then WO
    patent_priority = ['EP', 'US', 'WO']

    for country in patent_priority:
        for patent in patents:
            # respect priority
            if patent.epodoc.startswith(country) or patent.country == country:
                if patent.kind and patent.kind[0].upper() == "T":
                    # nope, don't want this one
                    continue

                # we may have a 'WO2016075599 A1', so try
                epodoc_with_space = patent.epodoc.split(' ')
                if len(epodoc_with_space) > 1:
                    epodoc_for_query = epodoc_with_space[0]
                else:
                    epodoc_for_query = patent.epodoc

                matched = re.match(patent_regex, epodoc_for_query)
                if matched:
                    # can be a good one, check for special chars
                    if "'" in epodoc_for_query:
                        #nope, don't want this one
                        continue
                # all good, use this
                return patent

    # no valid patent found ? then try all, reverse order to test older first, until we get one

    # doing this here because cycling import
    from requests.exceptions import HTTPError
    from Espacenet.builder import EspacenetBuilderClient
    import epo_ops

    client = EspacenetBuilderClient(use_cache=True)
    for patent in reversed(patents):
        try:
            a_loaded_patent = client.patent(  # Retrieve bibliography data
                    input = epo_ops.models.Epodoc(patent.epodoc),  # original, docdb, epodoc
                    )
            if a_loaded_patent:
                return a_loaded_patent
        except HTTPError as e:
            continue
