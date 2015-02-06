#!/usr/bin/env python
#-*- coding: UTF-8 -*-

###############################################################################
#
# Script: pymdl_sde_query.py
# Author: Andrew Schumpert  |  aschumpert@keywcorp.com
# Date: 2014/09/10
# Python Version: 2.7
# ArcPy Version: 10.2.2
# Purpose: To query Oracle Geodatabases for features
# Usage: Provide a .sde file to the getGdbFeaturesViaSql().
#   Optionally, the script will reture the feature datatype and the
#   feature count.
#   Results are returned as a list.  If options are used, then the list
#   is delimted by commas.
#
###############################################################################


import os
import sys
import traceback
import arcpy

# Custom module for logging
import pymdl_logging as log


###############################################################################


def getGdbFeaturesViaSql(gdb, returnType=False, returnCount=False):
    """Get features from a geodatase using SQL.

    gdb: path to a .sde file
    returnType: True/False flag to return the gdb item type
    returnCount: True/False flag to return the feature class count
    return: list of features in gdb
    examle return: "SomeDataset\SomeFeature,Feature Class,200"
    """
    try:
        log.info('Getting features via SQL for: {0}'.format(gdb))
        features = []
        count = ''
        dataType = ''
        if arcpy.Exists(gdb):
            owner = _getGdbOwner(gdb)
            if owner != False:
                # Dictionary to hold sde gdb_item types and values
                featureDict = {'Feature Dataset':
                               r"'{74737149-DCB5-4257-8904-B9724E32A530}'", 
                               'Table':
                               r"'{CD06BC3B-789D-4C51-AAFA-A467912B8965}'", 
                               'Feature Class':
                               r"'{70737809-852C-4A03-9E22-2CECEA5B9BFA}'", 
                               'Raster Dataset':
                               r"'{5ED667A3-9CA9-44A2-8029-D95BF23704B9}'", 
                               'Raster Catalog':
                               r"'{35B601F7-45CE-4AFF-ADB7-7702D3839B12}'",
                               'Relationship Class':
                               r"'{B606A7E1-FA5B-439C-849C-6E9C2481537B}'"}

                # Dictionary to hold SQL queries
                sqlDict = {'SELECT FEATURE DATASETS':
                           """select name from sde.gdb_items where name like '{0}' and TYPE = {1}""".format(
                               owner + '.%', featureDict['Feature Dataset']), 
                           'SELECT FEATURE CLASS':
                           """select name from sde.gdb_items where name like '{0}' and TYPE = {1} and path like concat('{2}', name)""".format(
                               owner + '.%', featureDict['Feature Class'], '\\'), 
                           'SELECT TABLE':
                           """select name from sde.gdb_items where name like '{0}' and TYPE = {1}""".format(
                               owner + '.%', featureDict['Table']), 
                           'SELECT RASTER DATASET':
                           """select name from sde.gdb_items where name like '{0}' and TYPE = {1}""".format(
                               owner + '.%', featureDict['Raster Dataset']), 
                           'SELECT RASTER CATALOG':
                           """select name from sde.gdb_items where name like '{0}' and TYPE = {1}""".format(
                               owner + '.%', featureDict['Raster Catalog'])}

                # Loop through the SQL queries for the gdb
                log.info('Creating ArcPy SQL Connection')
                sde_conn = arcpy.ArcSDESQLExecute(gdb)
                for key, value in sorted(sqlDict.iteritems()):
                    log.info('Executing SQL: {0}'.format(key))
                    sde_return = sde_conn.execute(value)
                    for items in _processSqlReturn(sde_return):
                        if returnCount:
                            count = ','
                            if key == 'SELECT FEATURE CLASS':
                                count = _processSqlReturn(sde_conn.execute("""select count(*) from {0}""".format(items)))
                                count = ',{0}'.format(count)
                        if returnType:
                            dataType = sde_conn.execute("""select type from sde.gdb_items where name = '{0}'""".format(items))
                            for key1, value1 in featureDict.iteritems():
                                if dataType == value1.replace("'", ''):
                                    dataType = ',' + key1
                        # Append feataures and then reset dataType and count
                        features.append('{0}{1}{2}'.format(items, dataType, count))
                        dataType, count = '',''
                        # Search inside of the feature datasets
                        if key == 'SELECT FEATURE DATASETS':
                            sqlDict2 = {'SELECT FEATURE DATASET FEATURE CLASS':
                                        """select name from sde.gdb_items where TYPE = {0} and PATH like concat('{1}', '{2}')""".format(
                                            featureDict['Feature Class'], ("\\" + items), """\%""")}
                            sde_return2 = sde_conn.execute(sqlDict2['SELECT FEATURE DATASET FEATURE CLASS'])
                            for things in _processSqlReturn(sde_return2):
                                if returnCount:
                                    count = _processSqlReturn(sde_conn.execute("""select count(*) from {0}""".format(things)))
                                    count = ',{0}'.format(count)
                                if returnType:
                                    dataType = sde_conn.execute("""select type from sde.gdb_items where name = '{0}'""".format(things))
                                    for key2, value2 in featureDict.iteritems():
                                        if dataType == value2.replace("'", ''):
                                            dataType = ',' + key2
                                # Append feataures and then reset dataType and count
                                features.append('{0}\{1}{2}{3}'.format(items, things, dataType, count))
                                dataType, count = '',''
                            del sde_return2
                    del sde_return
                del sde_conn
            else:
                log.error('Unable to get GDB features')
                return []
        else:
            log.error('GDB does not exist: {0}'.format(gdb))
        log.info('Completed SQL queries')
        return features
    except:
        log.exception('Unable to get GDB features')
        return features
    finally:
        arcpy.ClearWorkspaceCache_management()


def _getGdbOwner(gdb):
    """Describe the geodatabase to then return the schema owner

    gdb: The full path to a .sde file
    return: The .sde geodatabase schema owner
    """
    try:
        desc = arcpy.Describe(gdb)
        user = desc.connectionProperties.user
        log.info('GDB owner: {0}'.format(user))
        del desc
        return user
    except:
        log.exception('Error describing gdb: {0}'.format(gdb))
        return False


def _processSqlReturn(sqlReturn):
    """Determine SQL response type and return as a list

    sqlReturn: The response from sde_conn.execute(value)
    return: A list of responces
    """
    try:
        results = []
        if isinstance(sqlReturn, list):
            # Multiple itmes return as list
            for row in sqlReturn:
                results.append(row[0])

        elif isinstance(sqlReturn, bool):
            # Usually empty returns
            pass

        elif isinstance(sqlReturn, unicode):
            # Single items return as unicode
            results.append(str(sqlReturn))

        elif isinstance(sqlReturn, float):
            # Typical for row or feature count
            return str(int(sqlReturn))

        else:
            log.error('Unexpected SQL return type: {0}'.format(str(type(sdeReturn))))
        log.debug('Results (total {0}): {1}'.format(len(results), ', '.join(results)))
        return results
    except:
        log.exception('Unable to process the SQL response')
        return []


###############################################################################


def _test():
    """Function to test this scipt"""
    try:
        print 'TESTING SCRIPT'
        # Establish Logging
        logName = '{0} - TESTING LOG.txt'.format(os.path.basename(sys.argv[0]).replace('.','_'))
        fh = log.establish('DEBUG', logName, logPath='.\Logs', backups=0)

        gdb = r'.\SomeGDB.sde'
        
        for f in getGdbFeaturesViaSql(gdb, returnType=True, returnCount=True):
            print f

    except:
        log.exception('Error in main function of script')
        print 'ERROR WITH SCRIPT: {0}'.format(traceback.format_exc())
    finally:
        arcpy.ClearWorkspaceCache_management()
        log.info('TESTING SCRIPT COMPLETED')
        # Ensure to Shutdown the Logging
        log.shutdown(fh)
        print 'TESTING SCRIPT COMPLETED'


###############################################################################


if __name__ == '__main__':
    _test()


###############################################################################
