# Sources des données

Les données proviennent de [l'Office Européen des Brevets ("EPO")](https://www.epo.org/index_fr.html), grâce au service Espacenet "Open Patent Services" ("OPS") ([documentation technique](http://documents.epo.org/projects/babylon/eponet.nsf/0/F3ECDCC915C9BCD8C1258060003AA712/$File/ops_v3.2_documentation_-_version_1.3.81_en.pdf)).

Afin de respecter les règles de la [charte d'utilisation équitable d'EPO](https://www.epo.org/service-support/ordering/fair-use_fr.html), les données récupéré au travers de ce programme sont mises en cache deux semaines.

L'anglais est la langue de chargement, même si le texte (titre ou abstract) en français existe.
Si l'anglais n'existe pas, le français est utilisé.
Tous les autres titres d'une langue différente se retrouve dans le champs note.

Lorsque l'on charge une famille de brevet, la date de publication (260__c) est l'année du brevet le plus ancien.


## Choix des brevets

- Recherche utilisée, par année `pa all "Ecole Polytech* Lausanne" and pd=2014`. [Exemple de résultat sur Espacenet](https://worldwide.espacenet.com/searchResults?submitted=true&locale=en_EP&DB=EPODOC&ST=advanced&TI=&AB=&PN=&AP=&PR=&PD=&PA=Ecole+Polytech*+Lausanne&IN=&CPC=&IC=&Submit=Search)
- Chaque record infoscience est une famille EPO avec un identifiant


## Mapping Marcxml
- Chaque nouvelle famille de brevet est transformé en MarcXML ainsi :

~~~
  <record>
    <datafield ind1=" " ind2=" " tag="013">
      <subfield code="a">US2019336649234</subfield>
      <subfield code="b">US</subfield>
      <subfield code="c">A1</subfield>
      <subfield code="d">20191107</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="013">
      <subfield code="a">WO2018130949563463</subfield>
      <subfield code="b">WO</subfield>
      <subfield code="c">A1</subfield>
      <subfield code="d">20180719</subfield>
    </datafield>
    <datafield ind1="7" ind2="0" tag="024">
      <subfield code="a">58463685324234234</subfield>
      <subfield code="2">EPO Family ID</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="245">
      <subfield code="a">Cryogel scaffolds</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="260">
      <subfield code="c">2018</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="269">
      <subfield code="a">2018</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="336">
      <subfield code="a">Patents</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="700">
      <subfield code="a">Author, Author</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="973">
      <subfield code="a">EPFL</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="980">
      <subfield code="a">PATENT</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="520">
      <subfield code="a">A method of producing a cryogel.</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="981">
      <subfield code="a">S2</subfield>
    </datafield>
    <datafield ind1="C" ind2="0" tag="999">
      <subfield code="0">252085</subfield>
      <subfield code="p">TTO</subfield>
      <subfield code="x">U10021</subfield>
    </datafield>
    <datafield ind1=" " ind2=" " tag="037">
      <subfield code="a">PATENT</subfield>
    </datafield>
  </record>
~~~


## Mises à jour

Lorsqu'une publication reçoit une mise à jour de sa liste de brevet, la règle suivante est appliquée :

- Les entrées manuelles qui ne sont pas dans la liste Espacenet sont placée à la fin (en dernière position)
- Les entrées manuelles qui sont reconnus dans la liste Espacenet, ainsi que les nouvelles entrées, sont triée par date et ajouter de haut en bas
- Exemple possible : [Brevet1_Espacenet, Brevet2_Manuel_Espacenet, Brevet3_Espacenet, Brevet4_Manuel_Espacenet, Brevet5_Manuel]