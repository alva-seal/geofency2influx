# coding=utf-8
from cherrypy.process.plugins import Daemonizer
import urllib
import os
import os.path
from influxdb import InfluxDBClient
import cherrypy
import datetime
import json

from ConfigParser import SafeConfigParser
conf = SafeConfigParser()
conf.read('api.conf')

dbname = conf.get('db','dbname')
dbuser = conf.get('db','dbuser')
dbuser_password = conf.get('db','dbuser_password')
host = conf.get('db','host')
USERS = conf.get('auth','USERS')

client = InfluxDBClient(
	host,
	'8086',
	dbuser,
	dbuser_password,
	dbname,
	ssl=True,
	verify_ssl=True)


# d = Daemonizer(cherrypy.engine)
# d.subscribe()
root_dir = os.path.abspath(os.path.dirname(__file__))
cherrypy.config.update({'server.socket_port': 8083}),



class Api(object):

	@cherrypy.expose
	def index(self):
		return {'currentTime': datetime.datetime.now()}



class LocationApiWebService():
	exposed = True

	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		result = client.query('SELECT * FROM location ORDER BY DESC LIMIT 1')
		if (len(list(result.get_points())) !=1):
			print "noch keien Daten vorhanden"
		return str(json.dumps(list(result.get_points())[0]))

	def POST(self, id, name, entry, date, radius, device, latitude="", longitude="", address="", beaconUUID="", major="", minor=""):
		#print address.decode('utf-8')
		json_body = [
			{
				"measurement": "location",
				"tags": {
					"Id": id,
					"name" : name,
					"address" : urllib.quote_plus(address.encode('utf-8')),
					"device" : device,
					"beaconUUID" : beaconUUID,
					"major" : major,
					"minor" : minor,
				},
				"time" : date,
				"fields": {
					"entry": int(entry),
					"latitude": float(latitude),
					"longitude": float(longitude),
					"radius": float(radius),
				}
			}
		]
		print json_body
		client.write_points(json_body)
		return


def validate_password(realm, username, password):
	if username in USERS and USERS[username] == password:
		return True
	return False


if __name__ == '__main__':
	conf = {
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd()),
			'tools.auth_basic.on': True,
			'tools.auth_basic.realm': 'localhost',
			'tools.auth_basic.checkpassword': validate_password
		},
		'/location': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'text/plain')],
		}
	}


	webapp = Api()
	webapp.location = LocationApiWebService()
	cherrypy.quickstart(webapp, '/', conf)
