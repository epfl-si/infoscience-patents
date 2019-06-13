""" Load from a MarcXML file the patents inside """

tree = ET.parse('all_people.xml')
collection = tree.getroot()

for record in collection.iter('{http://www.loc.gov/MARC21/slim}record'):
    sciper = _get_datafield_values(record, '935').get('a')
    tind_author_id = _get_controlfield_value(record, '001')

    # just a check
    if not sciper:
        logger.info(
            "Author (Tind id %s) without a sciper, should it happens ?\nSkipping this author" % tind_author_id)
        continue

    # do we known it in epfl ? that's not mandatory as people may have gone
    epfl_author = epfl_authors.get(sciper)
    if not epfl_author:
        logger.warning(
            "This TIND author (sciper %s, tind id: %s, labs %s) is no more in EPFL or "
            "the referring laboratory is not in Infoscience.\n"
            " Skipping this author" % (
            sciper, tind_author_id, tind_authors[sciper].labs))
        continue

    # ok we know it, mark it as parsed by removing from our dict
    # so at the end we only have the one we need to create
    del epfl_authors[sciper]

    # look if it needs update
    tind_author = tind_authors[sciper]

    if tind_author != epfl_author:
        logger.debug("Author will be updated, from %s to %s" % (
            tind_author, epfl_author))

        # update record in a new instance, as we will move it to a new file
        to_update_record = copy.deepcopy(record)

        updated_record = update_marc_record(to_update_record, epfl_author)
        create_update_collection.append(updated_record)
