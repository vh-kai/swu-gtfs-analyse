import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

## Gesamtzahl der Fahrten pro route_id und direction_id
conn = sqlite3.connect("SWU.db")

query = """
SELECT route_id,
	direction_id,
	COUNT(DISTINCT trip_id) AS Fahrtenanzahl
FROM trips
GROUP BY route_id, 
	direction_id
ORDER BY route_id, 
	direction_id;
"""

df = pd.read_sql_query(query, conn)

conn.close()

print(type(df))
print(df.dtypes)

df["direction_id"] = df["direction_id"].astype("int64")    # dtype von str zu int
df["Fahrtenanzahl"] = df["Fahrtenanzahl"].astype("int64")  # dtype von str zu int
print(df.dtypes)

df_pivotiert = df.pivot(index='route_id', columns='direction_id', values='Fahrtenanzahl')

# Balkendiagramm
df_pivotiert.plot.bar(rot=45)

plt.title('Fahrten pro Linie und Richtung')
plt.xlabel('Linie')
plt.ylabel('Anzahl Fahrten')
plt.legend(title='Richtung')

plt.show()



##Tagesprofil des Fahrtenangebots
conn = sqlite3.connect("SWU.db")

# Eine Fahrt wird anhand ihrer ersten Abfahrtsstunde genau einem Zeitbereich zugeordnet.
# Ausgewertet wird die Anzahl der Fahrten je Linie und Richtung.
query = """
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
"""

df = pd.read_sql_query(query, conn)

conn.close()

print(type(df))
print(df.dtypes)

df_melted = pd.melt(df, id_vars = ['route_id', 'direction_id'])
print(df_melted.head())
print(df_melted.columns)

df_melted_grouped = df_melted.groupby(['route_id', 'variable'])['value'].sum().reset_index() # durch ['value'].sum wird eine Series zurückgegeben,
																							# .reset_index() macht daraus wieder einen DataFrame

# Small Multiples
df_L01 = df_melted_grouped[df_melted_grouped['route_id'] == 'L01']
df_L02 = df_melted_grouped[df_melted_grouped['route_id'] == 'L02']
df_L07 = df_melted_grouped[df_melted_grouped['route_id'] == 'L07']
df_L08 = df_melted_grouped[df_melted_grouped['route_id'] == 'L08']
df_L11 = df_melted_grouped[df_melted_grouped['route_id'] == 'L11']
df_L15 = df_melted_grouped[df_melted_grouped['route_id'] == 'L15']
df_L19 = df_melted_grouped[df_melted_grouped['route_id'] == 'L19']
df_L901 = df_melted_grouped[df_melted_grouped['route_id'] == 'L901']

fig, ax = plt.subplots(nrows=2, ncols=4, sharey=True)

ax[0, 0].bar(df_L01['variable'], df_L01['value'])
ax[0, 1].bar(df_L07['variable'], df_L07['value'])
ax[0, 2].bar(df_L11['variable'], df_L11['value'])
ax[0, 3].bar(df_L19['variable'], df_L19['value'])

ax[1, 0].bar(df_L02['variable'], df_L02['value'])
ax[1, 1].bar(df_L08['variable'], df_L08['value'])
ax[1, 2].bar(df_L15['variable'], df_L15['value'])
ax[1, 3].bar(df_L901['variable'], df_L901['value'])

ax[0, 0].set_title('L01')
ax[0, 1].set_title('L07')
ax[0, 2].set_title('L11')
ax[0, 3].set_title('L19')

ax[1, 0].set_title('L02')
ax[1, 1].set_title('L08')
ax[1, 2].set_title('L15')
ax[1, 3].set_title('L901')

ax[0, 0].set_ylabel('Anzahl der Fahrten')
ax[1, 0].set_ylabel('Anzahl der Fahrten')
ax[1, 0].set_xlabel('Zeitbereiche')
ax[1, 1].set_xlabel('Zeitbereiche')
ax[1, 2].set_xlabel('Zeitbereiche')
ax[1, 3].set_xlabel('Zeitbereiche')

ax[0, 0].tick_params(axis='x', rotation=90)
ax[0, 1].tick_params(axis='x', rotation=90)
ax[0, 2].tick_params(axis='x', rotation=90)
ax[0, 3].tick_params(axis='x', rotation=90)

ax[1, 0].tick_params(axis='x', rotation=90)
ax[1, 1].tick_params(axis='x', rotation=90)
ax[1, 2].tick_params(axis='x', rotation=90)
ax[1, 3].tick_params(axis='x', rotation=90)

fig.suptitle('Tagesprofile ausgewählter Linien')

fig.set_layout_engine('tight')
plt.show()

## Vergleich der Richtungen von Linie L19
df_L19 = df_melted[df_melted['route_id'] == 'L19'] # nicht gruppiert!
df_L19_d0 = df_L19[df_L19['direction_id'] == 0]
df_L19_d1 = df_L19[df_L19['direction_id'] == 1]

fig, ax = plt.subplots(nrows=2, ncols=1, sharey=True, figsize=(4,4))

ax[0].bar(df_L19_d0['variable'], df_L19_d0['value'])
ax[1].bar(df_L19_d1['variable'], df_L19_d1['value'])

ax[0].set_title('L19 - Richtung 0')
ax[1].set_title('L19 - Richtung 1')

ax[0].set_ylabel('Anzahl der Fahrten')
ax[1].set_ylabel('Anzahl der Fahrten')
ax[1].set_xlabel('Zeitbereiche')

fig.suptitle('Vergleich Fahrtenangebot nach Richtung - L19')

fig.set_layout_engine('tight')
plt.show()



## Hypothesenprüfung für L02
conn = sqlite3.connect("SWU.db")

# Eine Fahrt wird anhand ihrer ersten Abfahrtsstunde genau einem Zeitbereich zugeordnet.
# Ausgewertet wird die Anzahl der Fahrten je Linie und Richtung.
query = """
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
"""

df = pd.read_sql_query(query, conn)

conn.close()

print(type(df))
print(df.dtypes)

df_melted = pd.melt(df, id_vars = ['service_id', 'direction_id'])
print(df_melted.head())
print(df_melted.columns)

df_melted_grouped = df_melted.groupby(['service_id', 'variable'])['value'].sum().reset_index()
print(df_melted_grouped)

# Small Multiples
df_MoTh = df_melted_grouped[df_melted_grouped['service_id'] == 'Service_period_1-Mo-Th']
df_Fr = df_melted_grouped[df_melted_grouped['service_id'] == 'Service_period_1-Fr']
df_Sa = df_melted_grouped[df_melted_grouped['service_id'] == 'Service_period_1-Sa']
df_Su = df_melted_grouped[df_melted_grouped['service_id'] == 'Service_period_1-Su']

fig, ax = plt.subplots(nrows=2, ncols=2, sharey=True)

ax[0, 0].bar(df_MoTh['variable'], df_MoTh['value'])
ax[0, 1].bar(df_Sa['variable'], df_Sa['value'])

ax[1, 0].bar(df_Fr['variable'], df_Fr['value'])
ax[1, 1].bar(df_Su['variable'], df_Su['value'])

ax[0, 0].set_title('Montag-Donnerstag')
ax[0, 1].set_title('Samstag')
ax[1, 0].set_title('Freitag')
ax[1, 1].set_title('Sonntag')

ax[0, 0].set_ylabel('Anzahl der Fahrten')
ax[1, 0].set_ylabel('Anzahl der Fahrten')
ax[1, 0].set_xlabel('Zeitbereiche')
ax[1, 1].set_xlabel('Zeitbereiche')

fig.suptitle('Fahrtangebot von L02 nach Serviceperiode')

fig.set_layout_engine('tight')
plt.show()