-- Wie unterscheidet sich das Fahrtenangebot im Ulmer ÖPNV nach Linie, Richtung und Tageszeit?

-- Exploration der Daten als Vorbereitung der Analyse

-- Wie viele Fahrten gibt es? --> 5507 Fahrten
SELECT COUNT(DISTINCT trip_id)
FROM trips;

-- MIN- und MAX-Werte der Stunden der stop_times ermitteln --> Der beobachtete Bereich des Datensatzes reicht von 04 bis 28 Uhr (GTFS-Zeitangabe)
SELECT
    MIN(CAST(SUBSTR(departure_time, 1, 2) AS INTEGER)) AS min_stunde,
    MAX(CAST(SUBSTR(departure_time, 1, 2) AS INTEGER)) AS max_stunde
FROM stop_times;

-- Headsigns aller Routen und Fahrtrichtungen --> es gibt für einige Linien mehrere Headsigns pro Fahrtrichtung
SELECT route_id,
	direction_id,
	trip_headsign,
	COUNT(DISTINCT trip_id) AS Fahrten
FROM trips
GROUP BY route_id, 
	direction_id, 
	trip_headsign
ORDER BY route_id, 
	direction_id, 
	Fahrten 
	DESC;

/* Gibt es eine Verbindung zwischen den unterschiedlichen Headsigns zur shape_id? --> ja, aber ein trip_headsign beschreibt NICHT eindeutig den Streckenverlauf,
 auch bei gleichem trip_headsign kann die shape_id variieren 
 Linie: route_id --> Richtung: direction_id --> Fahrtziel: trip_headsign, kann innerhalb einer Linienrichtung variieren --> Streckenverlauf: shape_id, kann auch noch zusätzlich variieren */
SELECT route_id,
	direction_id,
	trip_headsign,
	shape_id,
	COUNT(DISTINCT trip_id) AS Fahrten
FROM trips
GROUP BY route_id,
	direction_id,
	trip_headsign,
	shape_id
ORDER BY route_id, direction_id, trip_headsign;

/* Für die Analyse wird eine Linienrichtung durch die Kombination aus route_id und direction_id definiert. 
Innerhalb einzelner Linienrichtungen können unterschiedliche Fahrtziele und Streckenvarianten vorkommen. 
Diese Varianten werden für die aggregierte Betrachtung des Fahrtenangebots nicht getrennt ausgewertet. */


-- Datenqualität prüfen


-- Gibt es routes die nicht in trips vorkommen? Nein
SELECT COUNT(*)
FROM routes r
LEFT JOIN trips t
ON r.route_id = t.route_id
WHERE t.route_id IS NULL;

-- Gibt es trips ohne stop_times? Nein
SELECT COUNT(*)
FROM trips t
LEFT JOIN stop_times st
ON t.trip_id = st.trip_id
WHERE st.trip_id IS NULL;

-- Gibt es stop_times ohne passenden trip? Nein
SELECT COUNT(*)
FROM stop_times st
LEFT JOIN trips t
ON t.trip_id = st.trip_id
WHERE t.trip_id IS NULL;


-- Datenanalyse

-- Gesamtzahl der Fahrten pro route_id und direction_id
SELECT route_id,
	direction_id,
	COUNT(DISTINCT trip_id) AS Fahrtenanzahl
FROM trips
GROUP BY route_id, 
	direction_id
ORDER BY route_id, 
	direction_id;

/* Tagesprofil des Fahrtenangebots: 
Eine Fahrt wird anhand ihrer ersten Abfahrtsstunde genau einem Zeitbereich zugeordnet.
Ausgewertet wird die Anzahl der Fahrten je Linie und Richtung.

Beobachtungen:
L02: Verstärktes Fahrtenangebot bei 06-10 und 14-18 --> prüfen ob diese Fahrten an Werktagen häufiger angeboten werden als an Wochenenden
L01, L02, L04 und L05 haben ein ähnliches Grundmuster: höheres Fahrtenangebot zw. 10-14 und 14-18, abends geht das Angebot deutlich zurück --> tageszeitlich stärker schwankendes Angebot
L06, L07 und L08 haben tagsüber ein relativ stabiles Angebot --> gleichmäßiges Tagesangebot
L09 hat tagsüber auch ein gleichmäßiges Angebot, allerdings mit stärkerer Einschränkung am Abend
L10 zeigt einen deutlichen Angebotsunterschied zwischen den Fahrtrichtungen, insbesondere bei 02-06 und 06-10
L11 hat insgesamt nur ein kleineres Angebot, tagsüber auch sehr gleichmäßig
L12 und L13 konstantes Angebot tagsüber, L13 auffallend symmetrisch (nur im Bereich 06-10 nicht)
L14 und L15 haben ein unregelmäßigeres und reduziertes Angebot
L19: Fahrten starten nur in den Zeitbereichen 06-10 bis 14-18, mit deutlichem Unterschied zwischen den Fahrtrichtungen
L90x: Fahrten nur in den Bereichen 22-02 und 02-06 --> ausgeprägtes Nachtangebot
*/

WITH zeit AS(
	SELECT t.route_id,
		t.direction_id,
		t.trip_id,
		CAST (SUBSTR(st.departure_time, 1, 2) AS INTEGER) AS Stunden
	FROM stop_times st
	JOIN trips t
	ON st.trip_id = t.trip_id
),

abfahrt AS(
	SELECT route_id,
		direction_id,
		trip_id,
		MIN(Stunden) AS Beginn
	FROM zeit
	GROUP BY route_id, direction_id, trip_id
),

bereiche AS(
	SELECT trip_id,
		route_id,
		direction_id,
		CASE
			WHEN Beginn BETWEEN 6 AND 9 THEN '06-10'
			WHEN Beginn BETWEEN 10 AND 13 THEN '10-14'
			WHEN Beginn BETWEEN 14 AND 17 THEN '14-18'
			WHEN Beginn BETWEEN 18 AND 21 THEN '18-22'
			WHEN Beginn BETWEEN 22 AND 25 THEN '22-02'
			WHEN Beginn BETWEEN 26 AND 28 
				OR Beginn BETWEEN 4 AND 5 THEN '02-06'
		END AS zeitraum
	FROM abfahrt
)

SELECT route_id,
	direction_id,
	
	COUNT(CASE
		WHEN zeitraum = '06-10' THEN trip_id
	END) AS '06-10',
	
	COUNT(CASE
		WHEN zeitraum = '10-14' THEN trip_id
	END) AS '10-14',
	
	COUNT(CASE
		WHEN zeitraum = '14-18' THEN trip_id
	END) AS '14-18',
	
	COUNT(CASE
		WHEN zeitraum = '18-22' THEN trip_id
	END) AS '18-22',
	
	COUNT(CASE
		WHEN zeitraum = '22-02' THEN trip_id
	END) AS '22-02',
	
	COUNT(CASE
		WHEN zeitraum = '02-06' THEN trip_id
	END) AS '02-06'
	
FROM bereiche
GROUP BY route_id, direction_id
ORDER BY route_id, direction_id;

/* Hypothesenprüfung für L02: 
Treten die auffällig hohen Fahrtenzahlen in den Zeitbereichen 06-10 und 14-18 insbesondere an Werktagen auf?


--> Die Hypothese, dass das höhere Fahrtenangebot der Linie L02 insbesondere in den Zeiträumen 06–10 Uhr und 14–18 Uhr mit dem werktäglichen Betrieb zusammenhängt, 
wird durch die Daten gestützt. Dieses werktägliche Muster könnte mit einem erhöhten Bedarf zu Schul-/Arbeitszeiten zusammenhängen. Aus den vorliegenden Fahrplandaten 
lässt sich jedoch nicht bestimmen, welche Nutzergruppen für das Muster verantwortlich sind.*/
WITH zeit AS(
	SELECT t.route_id,
		t.direction_id,
		t.trip_id,
		t.service_id,
		CAST (SUBSTR(st.departure_time, 1, 2) AS INTEGER) AS Stunden
	FROM stop_times st
	JOIN trips t
	ON st.trip_id = t.trip_id
	WHERE route_id = 'L02'
),

abfahrt AS(
	SELECT direction_id,
		trip_id,
		service_id,
		MIN(Stunden) AS Beginn
	FROM zeit
	GROUP BY direction_id, trip_id, service_id
),

bereiche AS(
	SELECT trip_id,
		direction_id,
		service_id,
		CASE
			WHEN Beginn BETWEEN 6 AND 9 THEN '06-10'
			WHEN Beginn BETWEEN 10 AND 13 THEN '10-14'
			WHEN Beginn BETWEEN 14 AND 17 THEN '14-18'
			WHEN Beginn BETWEEN 18 AND 21 THEN '18-22'
			WHEN Beginn BETWEEN 22 AND 25 THEN '22-02'
			WHEN Beginn BETWEEN 26 AND 28 
				OR Beginn BETWEEN 4 AND 5 THEN '02-06'
		END AS zeitraum
	FROM abfahrt
)

SELECT service_id,
	direction_id,
	
	COUNT(CASE
		WHEN zeitraum = '06-10' THEN trip_id
	END) AS '06-10',
	
	COUNT(CASE
		WHEN zeitraum = '10-14' THEN trip_id
	END) AS '10-14',
	
	COUNT(CASE
		WHEN zeitraum = '14-18' THEN trip_id
	END) AS '14-18',
	
	COUNT(CASE
		WHEN zeitraum = '18-22' THEN trip_id
	END) AS '18-22',
	
	COUNT(CASE
		WHEN zeitraum = '22-02' THEN trip_id
	END) AS '22-02',
	
	COUNT(CASE
		WHEN zeitraum = '02-06' THEN trip_id
	END) AS '02-06'
	
FROM bereiche
GROUP BY service_id, direction_id
ORDER BY service_id, direction_id;

/* Gibt es innerhalb einer Linie und Richtung Fahrten mit unterschiedlich vielen bedienten Haltestellen? 
--> innerhalb einer Linie und Fahrtrichtung kann die Haltestellenanzahl variieren */
WITH fahrten AS (
    SELECT t.route_id,
           t.direction_id,
           t.trip_id,
           COUNT(st.stop_id) AS Haltestellenanzahl
    FROM trips t
    JOIN stop_times st
      ON t.trip_id = st.trip_id
    GROUP BY t.route_id,
             t.direction_id,
             t.trip_id
)

SELECT route_id,
       direction_id,
       COUNT(DISTINCT Haltestellenanzahl) AS unterschiedliche_Haltestellenanzahlen
FROM fahrten
GROUP BY route_id, direction_id
ORDER BY route_id, direction_id;
