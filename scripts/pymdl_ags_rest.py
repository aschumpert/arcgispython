#!/usr/bin/env python
#-*- coding: UTF-8 -*-

###############################################################################
##
##  Script: pymdl_ags_rest.py
##  Author: Andrew Schumpert | aschumpert@keywcorp.com       
##  Date: 2014/06/03
##  Purpose: A set of functions to facilitate interacion with the
##      ArcGIS Server 10.2.2 REST API
##
##  Usage:
##      From primary script, import AGS_REST_API and call the included methods
##
###############################################################################


import traceback
import httplib
import urllib
import json
import random

# Custom modules
import pymdl_logging as log


#########################
## General HTTP Functions


def postHttpRequest(serverName, serverPort, URL, URL_ParamsEncoded):
    """Post the Http Request and return response.

    serverName: The name or IP of ArcGIS Server
    serverPort: The port number to ArcGIS Server
    URL: The REST endpoint to POST to
    URL_ParamsEncoded: The urllib.urlencode parameters to POST
    return: JSON response or False
    """
    try:
        #log.debug(r'Attempting to POST to {0}:{1}{2}?{3}'.format(serverName, serverPort, URL, URL_ParamsEncoded))
        httpConn = httplib.HTTPConnection(serverName, serverPort)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        httpConn.request('POST', URL, URL_ParamsEncoded, headers)
        response = httpConn.getresponse()
        # Determine if the response is successful or not
        if (response.status != 200):
            httpConn.close()
            log.error('Server response was not OK: {0}'.format(response.status))
            return False
        else:
            data = response.read()
            httpConn.close()
            # Determine if JSON response is successful or not
            if not assertJsonSuccess(data):
                return False
            jsonResponse = json.loads(data)
            return jsonResponse
    except:
        log.exception('Error with postHttpRequest()')
        return False


def assertJsonSuccess(data):
    """Checks that the input JSON object is not an error object.

    data: Response from HTTP server
    return: True or False
    """
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == 'error':
        log.error('JSON object returns an error. {0}'.format(str(obj)))
        return False
    else:
        return True


############################
## ArcGIS REST API Functions


def generateToken(username, password, serverName, serverPort, exp=360):
    """A REST API function to generate a token given username, password and the adminURL.

    username: A user with valid ArcGIS Server Publisher or Admin role
    password: The password for user
    serverName: The name or IP of ArcGIS Server
    serverPort: The port number to ArcGIS Server
    exp: The time in minutes before token expires (default = 360)
    return: token or False
    """    
    try:
        tokenURL = r'/arcgis/admin/generateToken'
        log.info('Generating token for: {0}:{1}{2}'.format(serverName, serverPort, tokenURL))
        paramsUrlencoded = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'expiration': str(exp), 'f': 'json'})
        #log.debug('URL Params: {0}'.format(paramsUrlencoded))
        r = postHttpRequest(serverName, serverPort, tokenURL, paramsUrlencoded)
        if r == False:
            log.error('Unable to Generate Token due to failed POST')
            return False
        else:
            log.info('Token Successfully Generated')
            return r['token']
    except:
        log.exception('Error with generateToken()')
        return False


def getServiceList(serverName, serverPort, token):
    """Get and return services from ArcGIS Server.

    serverName: The name or IP of ArcGIS Server
    serverPort: The port number to ArcGIS Server
    token: A valid token
    return: list of services formatted like: "Folder/ServiceName.ServiceType"

    Note: Excludes services in the Utilities or System folder
    """      
    try:
        log.info('Getting list of services')
        services = []
        baseServiceUrl = r'/arcgis/admin/services'
        url = r'{}/'.format(baseServiceUrl)
        log.info('Getting JSON definition for Service URL: {0}:{1}{2}'.format(serverName, serverPort, url))
        paramsUrlencoded = urllib.urlencode({'token': token, 'f': 'json'})
        r = postHttpRequest(serverName, serverPort, url, paramsUrlencoded)

        # Determine if services were returned
        if r == False:
            log.error('Unable to get service JSON definition due to failed POST')
            return []

        # Get the folders dictionary from the response
        folders = r['folders']
        # Remove unwanted folders
        folders.remove('System')
        folders.remove('Utilities')
        # Add an entry for the root folder
        folders.append('')

        # Loop through the folders and get services from within them
        for folder in folders:
            if folder != '':
                folder += '/'
            url = r'{}/{}'.format(baseServiceUrl, folder)
            paramsUrlencoded = urllib.urlencode({'token': token, 'f': 'json'})
            r = postHttpRequest(serverName, serverPort, url, paramsUrlencoded)

            # Determine if services were returned
            if r == False:
                log.error('Unable to get service JSON definition due to failed POST')
                return []

            # Build the service URL path
            for item in r['services']:
                if folder:
                    serviceUrl = r'{}{}.{}'.format(folder, item['serviceName'], item['type'])
                else:
                    serviceUrl = r'{}.{}'.format(item['serviceName'], item['type'])
                log.info(serviceUrl)
                services.append(serviceUrl)    
        return services
    except:
        log.exception('Unable to get list of services')
        return []


def getServiceProperties(serverName, serverPort, token, service):
    """Via the ArcGIS Server REST API, request service properties.

    serverName: The name or IP of ArcGIS Server
    serverPort: The port number to ArcGIS Server
    token: A valid token
    service: The "Folder/ServiceName.ServiceType" representation of a service
    return: HTTP response containing service properties
    """
    try:
        log.info('Getting properties for service: {}'.format(service))
        serviceURL = r'/arcgis/admin/services/{}'.format(service)
        #log.debug('Getting JSON definition for Service URL: {0}:{1}{2}'.format(serverName, serverPort, serviceURL))
        paramsUrlencoded = urllib.urlencode({'token': token, 'f': 'json'})
        r = postHttpRequest(serverName, serverPort, serviceURL, paramsUrlencoded)

        # Determine if return is valid and return
        if r == False:
            log.error('Unable to get service JSON definition due to failed POST')
            return False
        else:
            return r
    except:
        log.exception('Unable to get service properties')
        return False


def postUpdatedServiceProperties(serverName, serverPort, token, service, serviceProperties):
    """Post JSON edits to a ArcGIS Server service properties.

    serverName: The name or IP of ArcGIS Server
    serverPort: The port number to ArcGIS Server
    token: A valid token
    service: The "Folder/ServiceName.ServiceType" representation of a service
    serviceProperties: The JSON representation of the service
    """
    try:
        # Serialize back into JSON
        updatedSvcJson = json.dumps(serviceProperties)

        # POST updates back to service
        serviceURL = r'/arcgis/admin/services/{}/edit'.format(service)
        log.debug('Service Edit URL: {0}:{1}{2}'.format(serverName, serverPort, serviceURL))
        paramsUrlencoded = urllib.urlencode({'token': token, 'f': 'json', 'service': updatedSvcJson})
        r = postHttpRequest(serverName, serverPort, serviceURL, paramsUrlencoded)
        if r == False:
            log.error('Unable to edit service due to failed POST')
            return False
        else:
            log.info('Service Successfully Edited')
    except:
        log.exception('Unable to edit service')
        return False


###################
## Helper Functions


def createRandom24HourTime():
    """Create a random 24 Hour time for service recycle.

    return: A string representing HH:MM time
    """
    try:
        # max range set to 0200 AM to keep a 3 hour recycle window 
        hour = random.choice(range(0,2))
        # Pad single digits to ensure 2 significant digits
        if hour < 10:
            hour = '0{}'.format(hour)
        # exclude 0 in range to skip possibility of getting xx:00 value
        minute = random.choice(range(1,59))
        # Pad single digits to ensure 2 significant digits
        if minute < 10:
            minute = '0{}'.format(minute)              
        HHMM = '{0}:{1}'.format(hour,minute)
        log.debug('Generated Random Time "{0}"'.format(HHMM))
        return HHMM
    except:
        log.exception('Unable to create random time')
        return '00:00'


################
## Test Function


def _test():
    """Method for testing module functions"""
    try:
        print 'Testing this module'
        fh = log.establish('DEBUG', 'TEST_Log.txt')

        

    except:
        log.exception('Error in main function of script')
        print 'ERROR WITH SCRIPT: {0}'.format(traceback.format_exc())
    finally:
        log.info('Script Completed')
        log.shutdown(fh)


###############################################################################


if __name__ == '__main__':
    _test()


###############################################################################
