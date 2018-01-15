#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone
import os
import dateutil.parser as dateparser
from decimal import Decimal

from zeep import Client, xsd, helpers

import singer
from singer import utils

LOGGER = singer.get_logger()
REQUIRED_CONFIG_KEYS = [
    "publisher_id",
    "api_password",
    "user_type",
    "start_date",
    "validation_window",
]

CONFIG = {}
STATE = {}
AWIN_PUBLISHER_API = "http://api.affiliatewindow.com/v4/AffiliateService?wsdl"
BATCH_SIZE = 100 # For methods supporting batching request this number of rows in a single request
MAX_DAYS = 30 # Some of the methods only let you fetch 31 days of data in a single request

def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

def load_schema(entity):
    return utils.load_json(get_abs_path("schemas/{}.json".format(entity)))

def get_start(key, useStartDate=True):
    if key not in STATE:
        if useStartDate:
            d = utils.strptime_with_tz(CONFIG['start_date'])
            STATE[key] = utils.strftime(d)
            return d
        else:
            return None
    else:
        return dateparser.parse(STATE[key])

def map_type(x):
    if isinstance(x, Decimal):
        return float(x)
    elif isinstance(x, datetime):
        return x.isoformat()
    elif isinstance(x, dict):
        res = {}
        for k, v in x.items():
            # strip leading character indicating type
            sk = k[1:len(k)]
            res[sk] = map_type(v)
        return res
    elif isinstance(x, list):
        res = []
        for v in x:
            res.append(map_type(v))
        return res
    else:
        return x

def sync_transactions(client):
    schema = load_schema("transactions")
    singer.write_schema("transactions", schema, ["Id"])

    dateFrom=get_start("transactions") - timedelta(days=CONFIG['validation_window'])
    dateTo=datetime.now(timezone.utc)

    start = dateFrom
    offset = 0
    finalRow = None

    # handle batches by number of days and number of rows
    while start < dateTo:
        end = start + timedelta(days=MAX_DAYS)
        if (end > dateTo): end = dateTo
        resp = client.service.getTransactionList(dStartDate=start, dEndDate=end, iOffset=offset, iLimit=BATCH_SIZE, sDateType="transaction")
        if (resp.body.getTransactionListCountReturn.iRowsReturned > 0):
            for t in resp.body.getTransactionListReturn:
                t = helpers.serialize_object(t)
                if t['aTransactionParts'] != None:
                    t['aTransactionParts'] = t['aTransactionParts']
                singer.write_record("transactions", map_type(t))
                finalRow = t
        if (offset + resp.body.getTransactionListCountReturn.iRowsReturned) < resp.body.getTransactionListCountReturn.iRowsAvailable:
            offset += resp.body.getTransactionListCountReturn.iRowsReturned
        else:
            start = end
            offset = 0

    if finalRow != None:
        utils.update_state(STATE, "transactions", finalRow['dTransactionDate'])

def sync_advertisers(client):
    schema = load_schema("merchants")
    singer.write_schema("merchants", schema, ["Id"])

    lastModified=get_start("merchants", False)

    finalRow = None

    resp = client.service.getMerchantList(sRelationship="joined")
    for x in resp.body.getMerchantListReturn:
        x = helpers.serialize_object(x)
        if x['aCommissionRanges'] != None:
            x['aCommissionRanges'] = x['aCommissionRanges']
        if x['aSectors'] != None:
            x['aSectors'] = t['aSectors']
        if lastModified == None or x['dDetailsModified'] > lastModified:
            singer.write_record("merchants", map_type(x))
            finalRow = x

    if finalRow != None:
        utils.update_state(STATE, "merchants", finalRow['dDetailsModified'])

def do_sync():
    LOGGER.info("Starting sync")

    client = Client(AWIN_PUBLISHER_API)
    UserAuthentication = client.get_element("{http://api.affiliatewindow.com/}UserAuthentication")(iId=CONFIG['publisher_id'], sPassword=CONFIG['api_password'], sType=CONFIG['user_type'])
    client.set_default_soapheaders([UserAuthentication])

    sync_transactions(client)
    sync_advertisers(client)

    singer.write_state(STATE)

    LOGGER.info("Sync complete")

def main():
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    CONFIG.update(args.config)
    STATE.update(args.state)
    do_sync()


if __name__ == "__main__":
    main()
