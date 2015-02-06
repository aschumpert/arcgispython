#!/usr/bin/env python
#-*- coding: UTF-8 -*-

###############################################################################
##
##  Script: pymdl_logging.py
##  Created by: Andrew Schumpert | aschumpert@keywcorp.com       
##  Date: 2014/07/03
##  Purpose: General logging module for import into other script
##  Usage:  See the _test() for example usage.
##
###############################################################################


import os
import sys
import socket
import logging, logging.handlers
import traceback


###############################################################################
## LOCAL VARIABLE


# Set to False to avoid importing arcpy,
# and for not logging to arcpy Messages.
# True is the default value.
_logToArcpyMessagingWindow = True

if _logToArcpyMessagingWindow:
    import arcpy


###############################################################################


def _test():
    """Test function and example of how to use logging"""
    try:
        print 'Test for Loging'
        # Establish Logging at the beginning of the script
        fh = establish(lvl='DEBUG', logName='TestLog.txt', logPath='', backups=0)

        # Supply log functions with message as a STRING
        info('TEST - Info lvl')
        debug('TEST - Debug lvl')
        warning('TEST - Warning lvl')
        error('TEST - Error lvl')
        exception('TEST - Exception.  See the exception below this line.')
        info('Would any of this be logged to ArcPy: {0}'.format(_logToArcpyMessagingWindow))

    except:
        exception('Error in main function of script')
        print 'ERROR WITH SCRIPT: {0}'.format(traceback.format_exc())
    finally:
        # Ensure to Shut-down the Logging
        info('Script Completed')
        shutdown(fh)
        print 'Test Complete'


###############################################################################


if _logToArcpyMessagingWindow:
    import arcpy


def establish(lvl='INFO', logName=None, logPath=None, backups=0):
    """Establish logging using the python logging module.

    input: lvl - logging level(ERROR, INFO, DEBUG).  Default is INFO.
    input: logName - name of logfile (ex: log.txt).  Default is None.
    input: logPath - path to save log file. 
    input: backups - number of rotating logs to keep. Default is 0
    """
    try:
        print 'Script Started.  Setting up Logging.'

        # Set logging level
        if lvl == 'DEBUG':
            logLevel = logging.DEBUG
        elif lvl == 'INFO':
            logLevel = logging.INFO
        elif lvl == 'WARNING':
            logLevel = logging.WARNING
        elif lvl == 'ERROR':
            logLevel = logging.ERROR
        else:
            print 'Invalid logging level. Choose: ERROR, WARNING, INFO, DEBUG'
            return

        # Setup basic logging configuration to standard output stream
        logging.basicConfig(level=logLevel, format="%(asctime)s\t%(levelname)s:\t%(message)s")
        
        if logName != None and logName.strip() != '':
            # A logName has been provided so create a log file
            if logPath == None or logPath.strip() == '':
                # If no logPath is provided, use relative path
                logPath = r'.\\'
            logPathName = os.path.join(logPath, str(logName).strip())
            # If backups are needed, set the write style (write/append)
            if backups == 0:
                logMode = 'w'
            else:
                logMode = 'a'
            # Setup logging to a file
            fh = logging.handlers.RotatingFileHandler(filename=logPathName, mode=logMode, backupCount=int(backups))
            fh.setLevel(logLevel)
            formatter = logging.Formatter('%(asctime)s\t%(levelname)s:\t%(message)s')
            fh.setFormatter(formatter)
            logging.getLogger('').addHandler(fh)
            if os.path.isfile(logPathName):
                fh.doRollover()
            info('STARTING THE SCRIPT: {0}'.format(sys.argv[0]))
            info('Script running on host: {0}'.format(socket.gethostname()))
            info('Script running under the account of: {0}'.format(os.environ.get('USERNAME')))
            info('Log file created at: {0}'.format(logPathName))
        else:
            info('STARTING THE SCRIPT: {0}'.format(sys.argv[0]))
            info('Script running on host: {0}'.format(socket.gethostname()))
            info('Script running under the account of: {0}'.format(os.environ.get('USERNAME')))
            fh = None
        return fh
    except:
        print 'Error Establishing Log: {0}'.format(traceback.format_exc())



# Use the following in script to log messages
def info(message):
    """Info level logging"""
    logging.info('{0}'.format(message))
    if _logToArcpyMessagingWindow:
        arcpy.AddMessage('{0}'.format(message))


def debug(message):
    """Debug level logging"""
    logging.debug('{0}'.format(message))
    if _logToArcpyMessagingWindow:
        arcpy.AddMessage('{0}'.format(message))


def warning(message):
    """Warning level logging"""
    logging.warning('{0}'.format(message))
    if _logToArcpyMessagingWindow:
        arcpy.AddWarning('{0}'.format(message))

        
def error(message):
    """Error level logging"""
    logging.error('{0}'.format(message))
    if _logToArcpyMessagingWindow:
        arcpy.AddWarning('{0}'.format(message))


def exception(message):
    """Exception logging with stack trace"""
    logging.exception('{0}'.format(message))
    if _logToArcpyMessagingWindow:
        arcpy.AddError('{0} \n{1}'.format(message, traceback.format_exc()))


def shutdown(fileHandler):
    """Shut-down the logging"""
    try:
        debug('Shutting down logging')
        if fileHandler != None:
            logging.getLogger('').removeHandler(fileHandler)
    except:
        pass
    finally:
        logging.shutdown() 


###############################################################################


if __name__ == '__main__':
    _test()


###############################################################################
