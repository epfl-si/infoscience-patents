# Sources des données

Les données proviennent de [l'Office Européen des Brevets ("EPO")](https://www.epo.org/index_fr.html), grâce au service Espacenet "Open Patent Services" ("OPS") ([documentation technique](http://documents.epo.org/projects/babylon/eponet.nsf/0/F3ECDCC915C9BCD8C1258060003AA712/$File/ops_v3.2_documentation_-_version_1.3.81_en.pdf)).

Afin de respecter les règles de la [charte d'utilisation équitable d'EPO](https://www.epo.org/service-support/ordering/fair-use_fr.html), les données récupéré au travers de ce programme sont mises en cache deux semaines.

L'anglais est la langue de chargement, même si le texte (titre ou abstract) en français existe.

Lorsque l'on charge une famille de brevet, la date de publication (260__c) est l'année du brevet le plus ancien.


## Choix des brevets

- Recherche utilisée, par année `pa all "Ecole Polytech* Lausanne" and pd=2014`. [Exemple de résultat sur Espacenet](https://worldwide.espacenet.com/searchResults?submitted=true&locale=en_EP&DB=EPODOC&ST=advanced&TI=&AB=&PN=&AP=&PR=&PD=&PA=Ecole+Polytech*+Lausanne&IN=&CPC=&IC=&Submit=Search)
- Chaque record infoscience est une famille EPO avec un identifiant


## Mapping Marcxml
- Chaque nouvelle famille de brevet est transformé en MarcXML ainsi :

~~~
  <datafield tag="013" ind1=" " ind2=" ">
    <subfield code="a">patent number</subfield>
    <subfield code="c">patent kind</subfield>
    <subfield code="b">patent country</subfield>
    <subfield code="d">patent publication date</subfield>
  </datafield>
  <datafield tag="024" ind1="7" ind2="0">
    <subfield code="a">l'id</subfield>
    <subfield code="2">EPO Family ID</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">The title</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">année de publication</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="a">année de publication</subfield>
  </datafield>
  <datafield tag="336" ind1=" " ind2=" ">
    <subfield code="a">Patents</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">English abstract</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Inventor name</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="p">TTO</subfield>
    <subfield code="0">252085</subfield>
    <subfield code="x">U10021</subfield>
  </datafield>
  <datafield tag="973" ind1=" " ind2=" ">
    <subfield code="a">EPFL</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">PATENT</subfield>
  </datafield>
~~~


## Mises à jour

Lorsqu'une publication reçoit une mise à jour de sa liste de brevet, la règle suivante est appliquée :

- Les entrées manuelles qui ne sont pas dans la liste Espacenet sont placée à la fin (en dernière position)
- Les entrées manuelles qui sont reconnus dans la liste Espacenet, ainsi que les nouvelles entrées, sont triée par date et ajouter de haut en bas
- Exemple possible : [Brevet1_Espacenet, Brevet2_Manuel_Espacenet, Brevet3_Espacenet, Brevet4_Manuel_Espacenet, Brevet5_Manuel]