import logging

from pymongo import monitoring

class CommandLogger(monitoring.CommandListener):

    def started(self, event):
        logging.info("Command {0.command} with request id "
                     "{0.request_id} started on database "
                     "{0.database_name}".format(event))

    def succeeded(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "succeeded in {0.duration_micros} "
                     "microseconds".format(event))

    def failed(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "failed in {0.duration_micros} "
                     "microseconds".format(event))