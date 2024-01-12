# Importē bibliotēkas
import requests
import json
import datetime
import time
import yaml

# Importē datetime moduli no datetime pakotnes
from datetime import datetime
from configparser import ConfigParser
print('Asteroid processing service')

# Initiating and reading config values
print('Loading configuration from file')

try:
	config = ConfigParser()
	config.read('config.ini')

	nasa_api_key = config.get('nasa', 'api_key')
	nasa_api_url = config.get('nasa', 'api_url')

except:
	logger.exception('')
print('DONE')     

# NASA API atslēgas kods un api URL

# Getting todays date
dt = datetime.now()
request_date = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2)  
print("Generated today's date: " + str(request_date))

#Izveido pieprasījumu no NASA api url
print("Request url: " + str(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key))

#Get pieprasījums no NASA
r = requests.get(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key)

#izvada atbildes par stausa kodu, atbildes galvenēm un saturu
print("Response status code: " + str(r.status_code))
print("Response headers: " + str(r.headers))
print("Response content: " + str(r.text))


#Pārbauda, vai API atbilde ir veiksmīga
if r.status_code == 200:
	#Pārveido r.text atbildi uz json
	json_data = json.loads(r.text)
	
	#Saraksti drošajiem un bīstamajiem asteroīdiem
	ast_safe = []
	ast_hazardous = []

	#Veic pārbaudi vai elementu skaits ir iekš JSON
	if 'element_count' in json_data:
		ast_count = int(json_data['element_count'])
		print("Asteroid count today: " + str(ast_count))
		
		#Pārbauda asteroīdu skaitu un skatās vai asteroīdi ir manīti šodien
		if ast_count > 0:
			for val in json_data['near_earth_objects'][request_date]:
				#Pārbauda  pieejamos datus par asteroīdiem/tuviem zemes objektiem
				if 'name' and 'nasa_jpl_url' and 'estimated_diameter' and 'is_potentially_hazardous_asteroid' and 'close_approach_data' in val:
					
					#iegūst informāciju par objektu
					tmp_ast_name = val['name']
					tmp_ast_nasa_jpl_url = val['nasa_jpl_url']
					#Iegūst informāciju par diametru asteroīdam
					if 'kilometers' in val['estimated_diameter']:
						if 'estimated_diameter_min' and 'estimated_diameter_max' in val['estimated_diameter']['kilometers']:
							tmp_ast_diam_min = round(val['estimated_diameter']['kilometers']['estimated_diameter_min'], 3)
							tmp_ast_diam_max = round(val['estimated_diameter']['kilometers']['estimated_diameter_max'], 3)
						else:
							tmp_ast_diam_min = -2
							tmp_ast_diam_max = -2
					else:
						tmp_ast_diam_min = -1
						tmp_ast_diam_max = -1
					#Ja asterioīds ir noteikta diametra, tad tas tiek uzskatīts par potenciāli bīstamu
					tmp_ast_hazardous = val['is_potentially_hazardous_asteroid']

					#
					if len(val['close_approach_data']) > 0:
						#Tiek iegūti tuvošanās datums, ātrums, cik tālu no trāpīšanas un cik tuvu asteroīds pielidos
						if 'epoch_date_close_approach' and 'relative_velocity' and 'miss_distance' in val['close_approach_data'][0]:
							tmp_ast_close_appr_ts = int(val['close_approach_data'][0]['epoch_date_close_approach']/1000)
							tmp_ast_close_appr_dt_utc = datetime.utcfromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S')
							tmp_ast_close_appr_dt = datetime.fromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S')
							#APstrādā ātrumu km/h, tuvumu zemei un pielidošanas ātrumu
							if 'kilometers_per_hour' in val['close_approach_data'][0]['relative_velocity']:
								tmp_ast_speed = int(float(val['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']))
							else:
								tmp_ast_speed = -1

							if 'kilometers' in val['close_approach_data'][0]['miss_distance']:
								tmp_ast_miss_dist = round(float(val['close_approach_data'][0]['miss_distance']['kilometers']), 3)
							else:
								tmp_ast_miss_dist = -1
						else:
							tmp_ast_close_appr_ts = -1
							tmp_ast_close_appr_dt_utc = "1969-12-31 23:59:59"
							tmp_ast_close_appr_dt = "1969-12-31 23:59:59"
					else:
						print("No close approach data in message")
						tmp_ast_close_appr_ts = 0
						tmp_ast_close_appr_dt_utc = "1970-01-01 00:00:00"
						tmp_ast_close_appr_dt = "1970-01-01 00:00:00"
						tmp_ast_speed = -1
						tmp_ast_miss_dist = -1
					#Izvada informāciju par asteroīdiem
					print("------------------------------------------------------- >>")
					print("Asteroid name: " + str(tmp_ast_name) + " | INFO: " + str(tmp_ast_nasa_jpl_url) + " | Diameter: " + str(tmp_ast_diam_min) + " - " + str(tmp_ast_diam_max) + " km | Hazardous: " + str(tmp_ast_hazardous))
					print("Close approach TS: " + str(tmp_ast_close_appr_ts) + " | Date/time UTC TZ: " + str(tmp_ast_close_appr_dt_utc) + " | Local TZ: " + str(tmp_ast_close_appr_dt))
					print("Speed: " + str(tmp_ast_speed) + " km/h" + " | MISS distance: " + str(tmp_ast_miss_dist) + " km")
					
					# Adding asteroid data to the corresponding array
					if tmp_ast_hazardous == True:
						ast_hazardous.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist])
					else:
						ast_safe.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist])
		
			#izvada ziņojumu, par to ka asteroīdi ir pietiekami tālu no zemes.
		else:
			print("No asteroids are going to hit earth today")
	#izvada informāciju par bīstamajiem un drošajiem asteroīdiem
	print("Hazardous asteorids: " + str(len(ast_hazardous)) + " | Safe asteroids: " + str(len(ast_safe)))

	if len(ast_hazardous) > 0:
		#Kārto  bīstamo asteroīdu sarakstu cik tuvu/kad tie pienāks zemei (Pēc ast_hazardous.append saraksta)
		ast_hazardous.sort(key = lambda x: x[4], reverse=False)
		#Izcada iespējamo šodienas asteroīdu trāpījumu laikus
		print("Today's possible apocalypse (asteroid impact on earth) times:")
		for asteroid in ast_hazardous:
			print(str(asteroid[6]) + " " + str(asteroid[0]) + " " + " | more info: " + str(asteroid[1]))

		#Sakārto bīstamp asteroīdu sarakstu pēc netrāpīšanas  attāluma
		ast_hazardous.sort(key = lambda x: x[8], reverse=False)
		print("Closest passing distance is for: " + str(ast_hazardous[0][0]) + " at: " + str(int(ast_hazardous[0][8])) + " km | more info: " + str(ast_hazardous[0][1]))
	else:
		print("No asteroids close passing earth today")

else:
	print("Unable to get response from API. Response code: " + str(r.status_code) + " | content: " + str(r.text))
