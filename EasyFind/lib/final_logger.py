#!/usr/bin/python            
# -*- coding: utf-8 -*-   
'''
Created on 2015年9月21日

@author: taroiming
'''
import logging
import logging.handlers
import sys
import os
from EasyFind.config import LOG_PATH

class FinalLogger:  
    levels = {"n" : logging.NOTSET,  
              "d" : logging.DEBUG,  
              "i" : logging.INFO,  
              "w" : logging.WARN,  
              "e" : logging.ERROR,  
              "c" : logging.CRITICAL}  
      
    log_level = "d"  
    log_file = os.path.join(LOG_PATH,'final_logger.log')  #初始化log路径
    log_max_byte = 10 * 1024 * 1024;  
    log_backup_count = 5  
     
    @staticmethod  
    def getLogger(file_name=None):  
        if file_name is not None:
            FinalLogger.log_file = file_name
        FinalLogger.logger = logging.Logger("loggingmodule.FinalLogger")  
        log_handler = logging.handlers.RotatingFileHandler(filename = FinalLogger.log_file,\
                                                           maxBytes = FinalLogger.log_max_byte,\
                                                           backupCount = FinalLogger.log_backup_count)  
        log_fmt = logging.Formatter("[%(levelname)s][%(funcName)s][%(asctime)s]%(message)s")  
        log_handler.setFormatter(log_fmt)  
        FinalLogger.logger.addHandler(log_handler)  
        FinalLogger.logger.setLevel(FinalLogger.levels.get(FinalLogger.log_level))  
        return FinalLogger.logger  

if __name__ == "__main__":
    logger = FinalLogger.getLogger()  
    logger.debug("this is a debug msg!")  
    logger.info("this is a info msg!")  
    logger.warn("this is a warn msg!")  
    logger.error("this is a error msg!")  
    logger.critical("this is a critical msg!") 




        