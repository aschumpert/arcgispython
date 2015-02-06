#!/usr/bin/env python
#-*- coding: UTF-8 -*-

###############################################################################
##
##  Script: ArcServer_EditService.py
##  Created by Andrew Schumpert | aschumpert@keywcorp.com      
##  Date: 2014/11/19
##  Purpose:
##      From ArcGIS Server 10.2.2, get list of services and edit their
##      properties
##
##  Usage:
##      Provide credentials to a ArcGIS 10.2.2 Server with services to edit.
##      The service properties that will be examined and the properties
##      that they will change to are coded below.
##      Example Local Vars:
##        user: "admin"
##        password: "1234"
##        server: "hostMachine"
##        port: 6080
##      
##  Service Properties Being Evaluated in this Version:
##      maxStartupTime, recycleStartTime, schemaLockingEnabled,
##      WMSServer[enabled, onlineResource]
##
###############################################################################
### Local Variables  ###


# Credentials needed to generate a token for ArcServer
user = r''
password = r''
server = r''
port = 6080


##############################################################################


import urlparse

# Custom modules
import pymdl_logging as log
import pymdl_ags_rest as customPy


def main():
    try:
        # Establish logging
        fh = log.establish(lvl = 'DEBUG',
                           logName = 'ArcServer_EditService - LOG.txt',
                           logPath = r'..\Logs',
                           backups = 30)

        # Get a token to login to the ArcGIS Server
        token = customPy.generateToken(user, password, server, port, exp=720)

        # Get the list of services
        serviceList = customPy.getServiceList(server, port, token)
        log.info('Number of Services: {}'.format(len(serviceList)))
        
        # Update each service with new property value
        log.info('Getting service properties.  Will update properties if needed.')
        for service in serviceList:

            # Flag if posting changes are needed
            postTheUpdate = None

            # Get properties for the service
            sp = customPy.getServiceProperties(server, port, token, service)

            # Set the max startup time
            mxStTime = 900
            if sp['maxStartupTime'] != mxStTime:
                sp['maxStartupTime'] = mxStTime
                postTheUpdate = True
                log.info('Updating: maxStartupTime to "{0}"'.format(mxStTime))
                
            # Set Service Recycle Time to not be default value (00:00)
            if sp['recycleStartTime'] == '00:00':
                newRecycleStartTime = customPy.createRandom24HourTime()
                sp['recycleStartTime'] = newRecycleStartTime
                postTheUpdate = True
                log.info('Updating: recycleStartTime to "{0}"'.format(newRecycleStartTime))

            # Disable schema locking if the property exist (ex: for map services)
            if sp.get('properties', None).get('schemaLockingEnabled', None) != None:
                # Test for FEATURE SERVICE and if true skip
                isFeatureServer = None
                for d in sp['extensions']:
                    if d['typeName'] == 'FeatureServer':
                        if d['enabled'] == 'true':
                            isFeatureServer = True
                if isFeatureServer != True:
                    if sp.get('properties', None).get('schemaLockingEnabled', None) == 'true':
                        sp['properties']['schemaLockingEnabled'] = 'false'
                        postTheUpdate = True
                        log.info('Updating: schemaLockingEnabled to "false"')

           # Examine WMS properties
##
            # OnlineResource ex: "MyServer.com"
            desiredOnlineResource = ''
##
            for d in sp['extensions']:
                if d['typeName'] == 'WMSServer':

                    # Ensure the WMS service is enabled
                    if d['enabled'] != 'true':
                        d['enabled'] = 'true'
                        postTheUpdate = True
                        log.info('Updating: WMSServer, enabled to "true"')

                    # Examine WMS Online Resource for correct URL network location
                    onlineResource = urlparse.urlparse(d['properties']['onlineResource'])
                    if onlineResource.netloc.upper() != desiredOnlineResource:
                        url = urlparse.urljoin('http://{0}'.format(desiredOnlineResource), onlineResource.path)
                        d['properties']['onlineResource'] = url
                        postTheUpdate = True
                        log.info('Updating: WMSServer, onlineResource to "{0}"'.format(url))

            # If changes have been made, post the update
            if postTheUpdate:
                customPy.postUpdatedServiceProperties(server, port, token, service, sp)

    except:
        log.exception('Error in main function of script')
        print 'ERROR WITH SCRIPT: {0}'.format(traceback.format_exc())
    finally:
        log.info('Script Completed')
        log.shutdown(fh)


###############################################################################


if __name__ == '__main__':
    main()


###############################################################################
