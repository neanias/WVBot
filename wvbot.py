import logging
import re
import db
from irc import IRC
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

log_level = logging.DEBUG if config['System'].getboolean('debug') else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

volunteering_regexes = [
    r'^(I think )?(that )?We should (.*)$',
    r'^Why don\'t we (.*)$',
    r'^Tardis should (.*)$',
    r'^Someone (should|needs to) (.*)$',
    r'^(Please )?(Can|Could) someone (.*)$',
    r'^(It|What) would be good (was )?if (.*)$'
]

listing_regexes = [
    r'^ *what have i (volunteered for|agreed to|let myself in for|got myself in ?to)',
    r'^ *(oh,? )?for (fucks|pete\'?s|christ\'?s) sake',
    r'^ *omgwtflol'
]

irc = IRC(  host=config['IRC']['host'],
            port=config['IRC']['port'],
            nick=config['IRC']['nick'],
            channel=config['IRC']['channel'])

def main():
    irc.channel_message_received_callback = channel_message
    irc.start_connection()

def channel_message(sender, channel, message):
    if config['System']['debug']:
        logger.debug("[{0}] {1}: {2}".format(channel, sender, message))
    
    for regex in volunteering_regexes:
        if re.match(regex, message, re.IGNORECASE):
            db.insert_message(nick=sender, message=message, channel=channel)
            num_recorded_messages = db.count_user_messages(nick=sender, channel=channel)
            pluralstring = 's'
            if num_recorded_messages == 1:
                pluralstring = ''
            irc.send_channel_message(channel, "{0}: Well Volunteered! You have now volunteered to do {1} thing{2}!".format(sender, num_recorded_messages, pluralstring))
            logger.info("Well Volunteered message sent to {0} in {1}".format(sender, channel))

    if message.startswith(config['IRC']['nick'] + ":"):
        statement = message.split(":", 1)[1]

        for regex in listing_regexes:
            if re.match(regex, statement, re.IGNORECASE):
                volunteered = db.get_user_messages(nick=sender, channel=channel)
                if len(volunteered) > 0:
                    plural = 's'
                    if len(volunteered) == 1:
                        plural = ''

                    irc.send_channel_message(channel, "{0}: You have volunteered for the following {1} thing{2}:".format(sender, len(volunteered), plural))
                    for item in volunteered:
                        irc.send_channel_message(channel, "{0}: {1}".format(item.nick, item.message))
                else:
                    irc.send_channel_message(channel, "{0}: You haven't volunteered for anything!".format(sender))       

if __name__ == '__main__':
    main()
